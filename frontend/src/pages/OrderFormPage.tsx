import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import {
  api,
  ApiError,
  type CourierOption,
  type Customer,
  type GeocodeResult,
  type Order,
  type OrderDetail,
  type OrderInput,
} from "../api";
import Breadcrumbs from "../components/Breadcrumbs";
import Field, { FormAlert } from "../components/Field";
import MapPicker from "../components/MapPicker";
import { useToast } from "../components/Toast";
import { PRIORITY_LABELS, STATUS_LABELS, formatKg, fromInputDateTime, toInputDateTime } from "../labels";
import { check, collectErrors, type FieldErrors, focusFirstError, parseDecimal, summarize } from "../validation";

const MAX_WEIGHT_KG = 500;
const ACTIVE = ["ASSIGNED", "IN_ROUTE"];

interface FormState {
  customer_id: string;
  delivery_address: string;
  latitude: string;
  longitude: string;
  weight_kg: string;
  priority: number;
  desired_start: string;
  desired_end: string;
  assigned_courier_id: string;
}

const EMPTY: FormState = {
  customer_id: "",
  delivery_address: "",
  latitude: "",
  longitude: "",
  weight_kg: "1",
  priority: 2,
  desired_start: "",
  desired_end: "",
  assigned_courier_id: "",
};

/** Mensagens de regra de negócio da API que dizem respeito a um campo específico. */
const RULE_FIELDS: [RegExp, string][] = [
  [/capacidade|fora de serviço|Entregador inválido/i, "assigned_courier_id"],
  [/km do ponto de saída/i, "location"],
  [/horário final/i, "desired_end"],
  [/Cliente inválido/i, "customer_id"],
];

function fromOrder(order: Order): FormState {
  return {
    customer_id: String(order.customer.id),
    delivery_address: order.delivery_address,
    latitude: String(order.latitude),
    longitude: String(order.longitude),
    weight_kg: String(order.weight_kg).replace(".", ","),
    priority: order.priority,
    desired_start: toInputDateTime(order.desired_start),
    desired_end: toInputDateTime(order.desired_end),
    assigned_courier_id: order.assigned_courier ? String(order.assigned_courier.id) : "",
  };
}

export default function OrderFormPage() {
  const { id } = useParams();
  const editing = id !== undefined;
  const navigate = useNavigate();
  const notify = useToast();
  const [params] = useSearchParams();
  const [form, setForm] = useState<FormState>({ ...EMPTY, customer_id: params.get("cliente") ?? "" });
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [couriers, setCouriers] = useState<CourierOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [addressHint, setAddressHint] = useState<string | null>(null);
  const [lookup, setLookup] = useState<{ busy: boolean; results: GeocodeResult[] | null; message: string | null }>({
    busy: false,
    results: null,
    message: null,
  });

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Customer[]>("/customers"),
      api<CourierOption[]>("/couriers"),
      editing ? api<OrderDetail>(`/orders/${id}`) : Promise.resolve(null),
    ])
      .then(([customerList, courierList, current]) => {
        if (!active) return;
        setCustomers(customerList);
        setCouriers(courierList);
        if (current) {
          setOrder(current);
          setForm(fromOrder(current));
        }
      })
      .catch((err: ApiError) => active && setLoadError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [editing, id]);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
    clearError(key === "latitude" || key === "longitude" ? "location" : key);
  }

  function clearError(key: string) {
    setErrors((current) => {
      if (!(key in current)) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  }

  function chooseCustomer(value: string) {
    set("customer_id", value);
    const customer = customers.find((c) => String(c.id) === value);
    if (!editing && customer?.last_address && !form.delivery_address.trim()) {
      setForm((current) => ({
        ...current,
        customer_id: value,
        delivery_address: customer.last_address!,
        latitude: String(customer.last_latitude),
        longitude: String(customer.last_longitude),
      }));
      clearError("delivery_address");
      clearError("location");
      setAddressHint(`Preenchido com a última entrega de ${customer.full_name}. Confira antes de salvar.`);
    }
  }

  async function searchAddress() {
    const query = form.delivery_address.trim();
    if (query.length < 5) {
      setErrors((current) => ({ ...current, delivery_address: "Digite rua, número e bairro para buscar." }));
      return;
    }
    setLookup({ busy: true, results: null, message: null });
    try {
      const results = await api<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(query)}`);
      setLookup({
        busy: false,
        results,
        message: results.length ? null : "Nenhum endereço encontrado. Confira a grafia ou marque o local direto no mapa.",
      });
    } catch (err) {
      setLookup({ busy: false, results: null, message: (err as Error).message });
    }
  }

  function pickResult(result: GeocodeResult) {
    setForm((current) => ({
      ...current,
      delivery_address: result.label,
      latitude: String(result.latitude),
      longitude: String(result.longitude),
    }));
    clearError("delivery_address");
    clearError("location");
    setLookup({ busy: false, results: null, message: null });
    setAddressHint("Endereço encontrado no mapa. Acrescente o número ou complemento se faltar.");
  }

  function validate(): FieldErrors {
    const weight = parseDecimal(form.weight_kg);
    const latitude = parseDecimal(form.latitude);
    const longitude = parseDecimal(form.longitude);
    const start = form.desired_start ? new Date(form.desired_start) : null;
    const end = form.desired_end ? new Date(form.desired_end) : null;

    let courierError: string | null = null;
    const courier = couriers.find((c) => String(c.id) === form.assigned_courier_id);
    const sameCourier = order?.assigned_courier?.id === courier?.id;
    if (courier && weight !== null) {
      const alreadyCounted = sameCourier && order && ACTIVE.includes(order.status) ? order.weight_kg : 0;
      const total = courier.active_load_kg - alreadyCounted + weight;
      if (courier.availability === "OFFLINE" && !sameCourier) {
        courierError = `${courier.full_name} está fora de serviço e não pode receber pedidos.`;
      } else if (total > courier.load_capacity_kg + 1e-9) {
        courierError = `${courier.full_name} ficaria com ${formatKg(total)}, acima da capacidade de ${formatKg(
          courier.load_capacity_kg,
        )}.`;
      }
    }

    let locationError: string | null = null;
    if (latitude === null || longitude === null) {
      locationError = "Marque o local de entrega no mapa ou use Buscar endereço.";
    } else if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
      locationError = "Latitude vai de -90 a 90 e longitude de -180 a 180.";
    }

    let endError: string | null = null;
    if (start && end && end <= start) endError = "O fim precisa ser depois do início.";
    else if (!editing && end && end < new Date()) endError = "Esse horário já passou. Informe um horário futuro.";

    return collectErrors({
      customer_id: form.customer_id ? null : "Escolha o cliente do pedido.",
      delivery_address:
        form.delivery_address.trim().length >= 5 ? null : "Informe o endereço com rua, número e bairro.",
      location: locationError,
      weight_kg: check.number(form.weight_kg, { label: "o peso", min: 0, max: MAX_WEIGHT_KG }),
      desired_end: endError,
      assigned_courier_id: courierError,
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length) {
      setFormError(summarize(found));
      focusFirstError();
      return;
    }
    const payload: OrderInput = {
      customer_id: Number(form.customer_id),
      delivery_address: form.delivery_address,
      latitude: parseDecimal(form.latitude)!,
      longitude: parseDecimal(form.longitude)!,
      weight_kg: parseDecimal(form.weight_kg)!,
      priority: form.priority,
      desired_start: fromInputDateTime(form.desired_start),
      desired_end: fromInputDateTime(form.desired_end),
      assigned_courier_id: form.assigned_courier_id ? Number(form.assigned_courier_id) : null,
    };
    setBusy(true);
    setFormError(null);
    try {
      const saved = editing
        ? await api<Order>(`/orders/${id}`, { method: "PUT", body: payload })
        : await api<Order>("/orders", { method: "POST", body: payload });
      notify(editing ? `Pedido #${saved.id} atualizado.` : `Pedido #${saved.id} cadastrado.`);
      navigate(`/pedidos/${saved.id}`);
    } catch (err) {
      const error = err as ApiError;
      const fields = { ...error.fields };
      if (fields.latitude || fields.longitude) {
        fields.location = fields.latitude ?? fields.longitude;
        delete fields.latitude;
        delete fields.longitude;
      }
      const ruleField = RULE_FIELDS.find(([pattern]) => pattern.test(error.message))?.[1];
      if (ruleField) fields[ruleField] = error.message;
      setErrors(fields);
      setFormError(ruleField ? "Não foi possível salvar. Corrija o campo destacado." : error.message);
      focusFirstError();
    } finally {
      setBusy(false);
    }
  }

  const title = editing ? `Editar pedido #${id}` : "Novo pedido";
  const crumbs = [{ label: "Pedidos", to: "/pedidos" }, ...(editing ? [{ label: `Pedido #${id}`, to: `/pedidos/${id}` }] : []), { label: editing ? "Editar" : "Novo pedido" }];

  if (loading) return <p className="muted">Carregando formulário…</p>;
  if (loadError) {
    return (
      <section className="page state-page">
        <Breadcrumbs items={crumbs} />
        <h1>{title}</h1>
        <p className="alert error">{loadError}</p>
        <Link className="button quiet" to="/pedidos">
          Voltar para os pedidos
        </Link>
      </section>
    );
  }
  if (order && (order.status === "DELIVERED" || order.status === "CANCELLED")) {
    return (
      <section className="page state-page">
        <Breadcrumbs items={crumbs} />
        <h1>{title}</h1>
        <p className="alert info">
          Este pedido está {STATUS_LABELS[order.status].toLowerCase()} e não pode mais ser editado. Para reabri-lo, use a
          página do pedido.
        </p>
        <Link className="button primary" to={`/pedidos/${order.id}`}>
          Abrir o pedido #{order.id}
        </Link>
      </section>
    );
  }

  const latitude = parseDecimal(form.latitude);
  const longitude = parseDecimal(form.longitude);

  return (
    <section className="page">
      <Breadcrumbs items={crumbs} />
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p className="muted">Campos obrigatórios: cliente, endereço, local no mapa e peso.</p>
        </div>
      </div>

      <form className="form-card" onSubmit={submit} noValidate>
        <FormAlert message={formError} />
        <fieldset disabled={busy}>
          <legend>Cliente</legend>
          <Field label="Cliente" name="customer_id" error={errors.customer_id}>
            {(props) => (
              <select {...props} value={form.customer_id} onChange={(e) => chooseCustomer(e.target.value)}>
                <option value="">Escolha o cliente</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.full_name}
                    {customer.phone ? `, ${customer.phone}` : ""}
                  </option>
                ))}
              </select>
            )}
          </Field>
          <p className="inline-note">
            O cliente ainda não tem cadastro?{" "}
            <Link to={`/clientes/novo?voltar=${encodeURIComponent(editing ? `/pedidos/${id}/editar` : "/pedidos/novo")}`}>
              Cadastrar cliente
            </Link>
          </p>
        </fieldset>

        <fieldset disabled={busy}>
          <legend>Local de entrega</legend>
          <Field label="Endereço" name="delivery_address" error={errors.delivery_address} hint={addressHint ?? undefined}>
            {(props) => (
              <div className="input-with-action">
                <input
                  {...props}
                  value={form.delivery_address}
                  onChange={(e) => {
                    set("delivery_address", e.target.value);
                    setAddressHint(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      searchAddress();
                    }
                  }}
                  placeholder="Rua, número, bairro e cidade"
                />
                <button type="button" className="button quiet" onClick={searchAddress} disabled={lookup.busy}>
                  {lookup.busy ? "Buscando…" : "Buscar endereço"}
                </button>
              </div>
            )}
          </Field>
          {lookup.message && <p className="alert info">{lookup.message}</p>}
          {lookup.results && lookup.results.length > 0 && (
            <ul className="lookup-results" aria-label="Endereços encontrados">
              {lookup.results.map((result) => (
                <li key={`${result.latitude},${result.longitude}`}>
                  <button type="button" onClick={() => pickResult(result)}>
                    {result.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className={errors.location ? "field has-error" : "field"}>
            <span className="field-label">Local no mapa</span>
            <MapPicker
              latitude={latitude}
              longitude={longitude}
              invalid={Boolean(errors.location)}
              onPick={(lat, lon) => {
                setForm((current) => ({ ...current, latitude: String(lat), longitude: String(lon) }));
                clearError("location");
              }}
            />
            {errors.location ? (
              <p className="field-error" id="campo-location-erro">
                {errors.location}
              </p>
            ) : (
              <small>Clique no mapa para ajustar o ponto exato da entrega.</small>
            )}
          </div>
          <div className="grid-2">
            <Field label="Latitude" name="latitude">
              {(props) => (
                <input
                  {...props}
                  aria-invalid={Boolean(errors.location)}
                  value={form.latitude}
                  onChange={(e) => set("latitude", e.target.value)}
                  inputMode="decimal"
                />
              )}
            </Field>
            <Field label="Longitude" name="longitude">
              {(props) => (
                <input {...props} value={form.longitude} onChange={(e) => set("longitude", e.target.value)} inputMode="decimal" />
              )}
            </Field>
          </div>
        </fieldset>

        <fieldset disabled={busy}>
          <legend>Carga e horário</legend>
          <div className="grid-2">
            <Field label="Peso (kg)" name="weight_kg" error={errors.weight_kg} hint={`Até ${MAX_WEIGHT_KG} kg por pedido.`}>
              {(props) => (
                <input {...props} value={form.weight_kg} onChange={(e) => set("weight_kg", e.target.value)} inputMode="decimal" />
              )}
            </Field>
            <div className="field">
              <span className="field-label">Prioridade</span>
              <div className="segmented" role="radiogroup" aria-label="Prioridade">
                {[1, 2, 3].map((value) => (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={form.priority === value}
                    className={form.priority === value ? "active" : ""}
                    onClick={() => set("priority", value)}
                  >
                    {PRIORITY_LABELS[value]}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="grid-2">
            <Field label="Entregar a partir de" name="desired_start">
              {(props) => (
                <input
                  {...props}
                  type="datetime-local"
                  value={form.desired_start}
                  onChange={(e) => set("desired_start", e.target.value)}
                />
              )}
            </Field>
            <Field label="Entregar até" name="desired_end" error={errors.desired_end}>
              {(props) => (
                <input {...props} type="datetime-local" value={form.desired_end} onChange={(e) => set("desired_end", e.target.value)} />
              )}
            </Field>
          </div>
        </fieldset>

        <fieldset disabled={busy}>
          <legend>Entregador</legend>
          <Field
            label="Quem vai entregar"
            name="assigned_courier_id"
            error={errors.assigned_courier_id}
            hint="Pode ficar sem entregador e ser atribuído depois. A carga mostrada soma os pedidos atribuídos e em rota."
          >
            {(props) => (
              <select
                {...props}
                value={form.assigned_courier_id}
                onChange={(e) => set("assigned_courier_id", e.target.value)}
              >
                <option value="">Sem entregador por enquanto</option>
                {couriers.map((courier) => (
                  <option
                    key={courier.id}
                    value={courier.id}
                    disabled={courier.availability === "OFFLINE" && order?.assigned_courier?.id !== courier.id}
                  >
                    {courier.full_name}: {formatKg(courier.active_load_kg)} de {formatKg(courier.load_capacity_kg)}
                    {courier.availability === "OFFLINE" ? " (fora de serviço)" : ""}
                  </option>
                ))}
              </select>
            )}
          </Field>
        </fieldset>

        <div className="form-actions">
          <Link className="button quiet" to={editing ? `/pedidos/${id}` : "/pedidos"}>
            Cancelar
          </Link>
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar pedido"}
          </button>
        </div>
      </form>
    </section>
  );
}
