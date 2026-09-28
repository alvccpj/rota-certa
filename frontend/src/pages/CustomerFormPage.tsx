import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { api, ApiError, type Customer } from "../api";
import Breadcrumbs from "../components/Breadcrumbs";
import Field, { FormAlert } from "../components/Field";
import { useToast } from "../components/Toast";
import { check, collectErrors, type FieldErrors, focusFirstError, formatPhone, summarize } from "../validation";

/** Só aceita voltar para páginas internas, nunca para outro site. */
function safeReturn(path: string | null): string | null {
  return path && path.startsWith("/") && !path.startsWith("//") ? path : null;
}

export default function CustomerFormPage() {
  const { id } = useParams();
  const editing = id !== undefined;
  const navigate = useNavigate();
  const notify = useToast();
  const [params] = useSearchParams();
  const returnTo = safeReturn(params.get("voltar"));
  const [form, setForm] = useState({ full_name: "", phone: "" });
  const [loading, setLoading] = useState(editing);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    api<Customer>(`/customers/${id}`)
      .then((customer) => setForm({ full_name: customer.full_name, phone: customer.phone ?? "" }))
      .catch((err: ApiError) => setLoadError(err.status === 404 ? "Cliente não encontrado." : err.message))
      .finally(() => setLoading(false));
  }, [editing, id]);

  function set(key: "full_name" | "phone", value: string) {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => {
      if (!(key in current)) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = collectErrors({
      full_name: check.personName(form.full_name, "Informe o nome do cliente."),
      phone: check.phone(form.phone),
    });
    setErrors(found);
    if (Object.keys(found).length) {
      setFormError(summarize(found));
      focusFirstError();
      return;
    }
    setBusy(true);
    setFormError(null);
    try {
      const body = { full_name: form.full_name, phone: form.phone || null };
      const saved = editing
        ? await api<Customer>(`/customers/${id}`, { method: "PUT", body })
        : await api<Customer>("/customers", { method: "POST", body });
      notify(editing ? `Dados de ${saved.full_name} atualizados.` : `${saved.full_name} cadastrado.`);
      if (returnTo) {
        const separator = returnTo.includes("?") ? "&" : "?";
        navigate(`${returnTo}${separator}cliente=${saved.id}`);
      } else {
        navigate("/clientes");
      }
    } catch (err) {
      const error = err as ApiError;
      const fields = { ...error.fields };
      if (error.status === 409) fields.full_name = error.message;
      setErrors(fields);
      setFormError(error.status === 409 ? "Não foi possível salvar. Corrija o campo destacado." : error.message);
      focusFirstError();
    } finally {
      setBusy(false);
    }
  }

  const back = returnTo ?? "/clientes";
  const crumbs = [
    returnTo?.startsWith("/pedidos") ? { label: "Pedidos", to: "/pedidos" } : { label: "Clientes", to: "/clientes" },
    { label: editing ? "Editar cliente" : "Novo cliente" },
  ];

  if (loading) return <p className="muted">Carregando cliente…</p>;
  if (loadError) {
    return (
      <section className="page state-page">
        <Breadcrumbs items={crumbs} />
        <h1>{loadError}</h1>
        <Link className="button primary" to="/clientes">
          Voltar para os clientes
        </Link>
      </section>
    );
  }

  return (
    <section className="page">
      <Breadcrumbs items={crumbs} />
      <div className="page-head">
        <div>
          <h1>{editing ? "Editar cliente" : "Novo cliente"}</h1>
          <p className="muted">
            {returnTo
              ? "Depois de salvar, você volta ao pedido com este cliente já escolhido."
              : "O telefone ajuda o entregador a falar com o cliente na hora da entrega."}
          </p>
        </div>
      </div>
      <form className="form-card narrow" onSubmit={submit} noValidate>
        <FormAlert message={formError} />
        <fieldset disabled={busy}>
          <legend>Dados do cliente</legend>
          <Field label="Nome" name="full_name" error={errors.full_name}>
            {(props) => <input {...props} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} autoComplete="off" />}
          </Field>
          <Field label="Telefone" name="phone" error={errors.phone} hint="Opcional. Com DDD, por exemplo (81) 98800-1001.">
            {(props) => (
              <input
                {...props}
                value={form.phone}
                inputMode="tel"
                placeholder="(81) 90000-0000"
                onChange={(e) => set("phone", e.target.value)}
                onBlur={() => set("phone", formatPhone(form.phone))}
              />
            )}
          </Field>
        </fieldset>
        <div className="form-actions">
          <Link className="button quiet" to={back}>
            Cancelar
          </Link>
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar cliente"}
          </button>
        </div>
      </form>
    </section>
  );
}
