import { type FormEvent, useCallback, useEffect, useState } from "react";
import { api, type CourierOption, type Order, type OrderInput, type OrderStatus, type User } from "../api";
import Drawer from "../components/Drawer";
import MapPicker from "../components/MapPicker";
import {
  AVAILABILITY_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
  formatKg,
  formatWindow,
  fromInputDateTime,
  toInputDateTime,
} from "../labels";

const STATUSES: OrderStatus[] = ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"];
const COURIER_STATUSES: OrderStatus[] = ["ASSIGNED", "IN_ROUTE", "DELIVERED"];

const NEXT_STEP: Partial<Record<OrderStatus, { status: OrderStatus; label: string; done: string }>> = {
  ASSIGNED: { status: "IN_ROUTE", label: "Sair para entrega", done: "Entrega iniciada." },
  IN_ROUTE: { status: "DELIVERED", label: "Confirmar entrega", done: "Entrega confirmada." },
};

export default function OrdersPage({ user }: { user: User }) {
  const isCourier = user.role === "COURIER";
  const canDelete = user.role === "ADMIN";
  const [orders, setOrders] = useState<Order[]>([]);
  const [couriers, setCouriers] = useState<CourierOption[]>([]);
  const [filter, setFilter] = useState<OrderStatus | "ALL">("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [editing, setEditing] = useState<Order | "new" | null>(null);

  const load = useCallback(async () => {
    try {
      setOrders(await api<Order[]>("/orders"));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    if (!isCourier) api<CourierOption[]>("/couriers").then(setCouriers).catch(() => undefined);
  }, [load, isCourier]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 3500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function remove(order: Order) {
    if (!window.confirm(`Excluir o pedido #${order.id} de ${order.customer.full_name}? Essa ação não pode ser desfeita.`)) return;
    try {
      await api(`/orders/${order.id}`, { method: "DELETE" });
      setToast(`Pedido #${order.id} excluído.`);
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function advance(order: Order) {
    const step = NEXT_STEP[order.status];
    if (!step) return;
    try {
      await api(`/orders/${order.id}/status`, { method: "PATCH", body: { status: step.status } });
      setToast(step.done);
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const counts = STATUSES.reduce(
    (acc, status) => ({ ...acc, [status]: orders.filter((o) => o.status === status).length }),
    {} as Record<OrderStatus, number>,
  );
  const visible = filter === "ALL" ? orders : orders.filter((o) => o.status === filter);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>{isCourier ? "Minhas entregas" : "Pedidos"}</h1>
          <p className="muted">
            {isCourier
              ? "Pedidos atribuídos a você. Atualize o andamento a cada etapa."
              : "Cadastre os pedidos do dia e escolha quem vai entregar."}
          </p>
        </div>
        {!isCourier && (
          <button type="button" className="button primary" onClick={() => setEditing("new")}>
            Novo pedido
          </button>
        )}
      </div>

      <div className="filters" role="group" aria-label="Filtrar por situação">
        <button type="button" className={filter === "ALL" ? "chip active" : "chip"} onClick={() => setFilter("ALL")}>
          Todos <span>{orders.length}</span>
        </button>
        {(isCourier ? COURIER_STATUSES : STATUSES).map((status) => (
          <button
            key={status}
            type="button"
            className={filter === status ? "chip active" : "chip"}
            onClick={() => setFilter(status)}
          >
            {STATUS_LABELS[status]} <span>{counts[status]}</span>
          </button>
        ))}
      </div>

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="muted">Carregando pedidos…</p>
      ) : visible.length === 0 ? (
        <div className="empty">
          <p>{filter === "ALL" ? "Nenhum pedido cadastrado ainda." : `Nenhum pedido com a situação ${STATUS_LABELS[filter].toLowerCase()}.`}</p>
          {!isCourier && filter === "ALL" && (
            <button type="button" className="button primary" onClick={() => setEditing("new")}>
              Cadastrar o primeiro pedido
            </button>
          )}
        </div>
      ) : isCourier ? (
        <ul className="delivery-list">
          {visible.map((order) => {
            const step = NEXT_STEP[order.status];
            return (
              <li key={order.id} className="delivery">
                <div className="delivery-top">
                  <StatusBadge status={order.status} />
                  <Priority value={order.priority} />
                </div>
                <h3>{order.customer.full_name}</h3>
                <p className="address">{order.delivery_address}</p>
                <dl className="facts">
                  <div>
                    <dt>Horário</dt>
                    <dd>{formatWindow(order.desired_start, order.desired_end)}</dd>
                  </div>
                  <div>
                    <dt>Peso</dt>
                    <dd>{formatKg(order.weight_kg)}</dd>
                  </div>
                  {order.customer.phone && (
                    <div>
                      <dt>Telefone</dt>
                      <dd>
                        <a href={`tel:${order.customer.phone.replace(/\D/g, "")}`}>{order.customer.phone}</a>
                      </dd>
                    </div>
                  )}
                </dl>
                <div className="delivery-actions">
                  <a
                    className="button quiet"
                    href={`https://www.google.com/maps/dir/?api=1&destination=${order.latitude},${order.longitude}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Abrir no mapa
                  </a>
                  {step && (
                    <button type="button" className="button primary" onClick={() => advance(order)}>
                      {step.label}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Pedido</th>
                <th scope="col">Cliente</th>
                <th scope="col">Endereço de entrega</th>
                <th scope="col">Horário</th>
                <th scope="col">Prioridade</th>
                <th scope="col">Entregador</th>
                <th scope="col">Situação</th>
                <th scope="col">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((order) => (
                <tr key={order.id}>
                  <td className="num">#{order.id}</td>
                  <td>
                    <strong>{order.customer.full_name}</strong>
                    {order.customer.phone && <span className="sub">{order.customer.phone}</span>}
                  </td>
                  <td>
                    {order.delivery_address}
                    <span className="sub">{formatKg(order.weight_kg)}</span>
                  </td>
                  <td className="nowrap">{formatWindow(order.desired_start, order.desired_end)}</td>
                  <td>
                    <Priority value={order.priority} />
                  </td>
                  <td className="nowrap">
                    {order.assigned_courier?.full_name ?? <span className="muted">Sem entregador</span>}
                  </td>
                  <td>
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="row-actions">
                    <button type="button" className="button quiet small" onClick={() => setEditing(order)}>
                      Editar
                    </button>
                    {canDelete && (
                      <button type="button" className="button danger small" onClick={() => remove(order)}>
                        Excluir
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <Drawer title={editing === "new" ? "Novo pedido" : `Editar pedido #${editing.id}`} onClose={() => setEditing(null)}>
          <OrderForm
            order={editing === "new" ? null : editing}
            couriers={couriers}
            onSaved={(message) => {
              setEditing(null);
              setToast(message);
              load();
            }}
          />
        </Drawer>
      )}

      <div className="toast" role="status" aria-live="polite">
        {toast}
      </div>
    </section>
  );
}

export function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status status-${status.toLowerCase()}`}>{STATUS_LABELS[status]}</span>;
}

function Priority({ value }: { value: number }) {
  return <span className={`priority priority-${value}`}>{PRIORITY_LABELS[value]}</span>;
}

interface FormProps {
  order: Order | null;
  couriers: CourierOption[];
  onSaved: (message: string) => void;
}

function OrderForm({ order, couriers, onSaved }: FormProps) {
  const [form, setForm] = useState({
    customer_name: order?.customer.full_name ?? "",
    customer_phone: order?.customer.phone ?? "",
    delivery_address: order?.delivery_address ?? "",
    latitude: order ? String(order.latitude) : "",
    longitude: order ? String(order.longitude) : "",
    weight_kg: order ? String(order.weight_kg) : "1",
    priority: order?.priority ?? 2,
    desired_start: toInputDateTime(order?.desired_start ?? null),
    desired_end: toInputDateTime(order?.desired_end ?? null),
    assigned_courier_id: order?.assigned_courier ? String(order.assigned_courier.id) : "",
    status: order?.status ?? ("PENDING" as OrderStatus),
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) => setForm((f) => ({ ...f, [key]: value }));
  const latitude = form.latitude === "" ? null : Number(form.latitude);
  const longitude = form.longitude === "" ? null : Number(form.longitude);

  // Um entregador que foi desativado continua aparecendo no pedido que já era dele.
  const courierOptions =
    order?.assigned_courier && !couriers.some((c) => c.id === order.assigned_courier!.id)
      ? [...couriers, { ...order.assigned_courier, availability: "OFFLINE" as const, load_capacity_kg: 0 }]
      : couriers;

  const locked = order != null && (order.status === "DELIVERED" || order.status === "CANCELLED");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (latitude == null || longitude == null || Number.isNaN(latitude) || Number.isNaN(longitude)) {
      setError("Marque o local de entrega no mapa ou informe latitude e longitude.");
      return;
    }
    const payload: OrderInput = {
      customer_name: form.customer_name,
      customer_phone: form.customer_phone || null,
      delivery_address: form.delivery_address,
      latitude,
      longitude,
      weight_kg: Number(form.weight_kg.replace(",", ".")),
      priority: form.priority,
      desired_start: fromInputDateTime(form.desired_start),
      desired_end: fromInputDateTime(form.desired_end),
      assigned_courier_id: form.assigned_courier_id ? Number(form.assigned_courier_id) : null,
    };
    setBusy(true);
    setError(null);
    try {
      if (!order) {
        const created = await api<Order>("/orders", { method: "POST", body: payload });
        onSaved(`Pedido #${created.id} cadastrado.`);
        return;
      }
      if (!locked) await api<Order>(`/orders/${order.id}`, { method: "PUT", body: payload });
      if (form.status !== order.status) {
        await api<Order>(`/orders/${order.id}/status`, { method: "PATCH", body: { status: form.status } });
      }
      onSaved(`Pedido #${order.id} atualizado.`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="drawer-form" onSubmit={submit} noValidate>
      {locked && (
        <p className="alert info">
          Pedidos entregues ou cancelados ficam só para consulta. Para reabrir, mude a situação e salve.
        </p>
      )}
      <fieldset disabled={busy || locked}>
        <legend>Cliente</legend>
        <div className="grid-2">
          <label>
            Nome
            <input value={form.customer_name} onChange={(e) => set("customer_name", e.target.value)} required />
          </label>
          <label>
            Telefone
            <input
              value={form.customer_phone}
              onChange={(e) => set("customer_phone", e.target.value)}
              placeholder="(81) 90000-0000"
              inputMode="tel"
            />
          </label>
        </div>
      </fieldset>

      <fieldset disabled={busy || locked}>
        <legend>Entrega</legend>
        <label>
          Endereço
          <input
            value={form.delivery_address}
            onChange={(e) => set("delivery_address", e.target.value)}
            placeholder="Rua, número, bairro e cidade"
            required
          />
        </label>
        <div className="map-field">
          <span className="field-label">Local no mapa</span>
          <MapPicker
            latitude={latitude}
            longitude={longitude}
            onPick={(lat, lon) => setForm((f) => ({ ...f, latitude: String(lat), longitude: String(lon) }))}
          />
          <small>Clique no mapa para marcar o ponto de entrega.</small>
        </div>
        <div className="grid-2">
          <label>
            Latitude
            <input value={form.latitude} onChange={(e) => set("latitude", e.target.value)} inputMode="decimal" />
          </label>
          <label>
            Longitude
            <input value={form.longitude} onChange={(e) => set("longitude", e.target.value)} inputMode="decimal" />
          </label>
        </div>
        <div className="grid-2">
          <label>
            Peso (kg)
            <input value={form.weight_kg} onChange={(e) => set("weight_kg", e.target.value)} inputMode="decimal" />
          </label>
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
          <label>
            Entregar a partir de
            <input type="datetime-local" value={form.desired_start} onChange={(e) => set("desired_start", e.target.value)} />
          </label>
          <label>
            Entregar até
            <input type="datetime-local" value={form.desired_end} onChange={(e) => set("desired_end", e.target.value)} />
          </label>
        </div>
      </fieldset>

      <fieldset disabled={busy}>
        <legend>Andamento</legend>
        <div className="grid-2">
          <label>
            Entregador
            <select
              value={form.assigned_courier_id}
              onChange={(e) => set("assigned_courier_id", e.target.value)}
              disabled={locked}
            >
              <option value="">Sem entregador</option>
              {courierOptions.map((courier) => (
                <option key={courier.id} value={courier.id}>
                  {courier.full_name} ({AVAILABILITY_LABELS[courier.availability].toLowerCase()})
                </option>
              ))}
            </select>
          </label>
          {order && (
            <label>
              Situação
              <select value={form.status} onChange={(e) => set("status", e.target.value as OrderStatus)}>
                {STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {STATUS_LABELS[status]}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </fieldset>

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
      <div className="drawer-actions">
        <button type="submit" className="button primary" disabled={busy}>
          {busy ? "Salvando…" : order ? "Salvar alterações" : "Cadastrar pedido"}
        </button>
      </div>
    </form>
  );
}
