import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api, ApiError, type Availability, type Role, type User } from "../api";
import Breadcrumbs from "../components/Breadcrumbs";
import Field, { FormAlert } from "../components/Field";
import { useToast } from "../components/Toast";
import { AVAILABILITY_LABELS, ROLE_LABELS, ROLE_PERMISSIONS } from "../labels";
import { useUser } from "../session";
import { check, collectErrors, type FieldErrors, focusFirstError, parseDecimal, summarize } from "../validation";

const ROLES: Role[] = ["ADMIN", "ATTENDANT", "COURIER"];

export default function UserFormPage() {
  const { id } = useParams();
  const editing = id !== undefined;
  const currentUser = useUser();
  const navigate = useNavigate();
  const notify = useToast();
  const isSelf = editing && Number(id) === currentUser.id;
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(editing);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    role: "ATTENDANT" as Role,
    password: "",
    load_capacity_kg: "",
    availability: "AVAILABLE" as Availability,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    api<User>(`/users/${id}`)
      .then((loaded) => {
        setUser(loaded);
        setForm({
          full_name: loaded.full_name,
          email: loaded.email,
          role: loaded.role,
          password: "",
          load_capacity_kg: loaded.courier ? String(loaded.courier.load_capacity_kg).replace(".", ",") : "",
          availability: loaded.courier?.availability ?? "AVAILABLE",
        });
      })
      .catch((err: ApiError) => setLoadError(err.status === 404 ? "Usuário não encontrado." : err.message))
      .finally(() => setLoading(false));
  }, [editing, id]);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
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
    const courier = form.role === "COURIER";
    const found = collectErrors({
      full_name: check.personName(form.full_name, "Informe o nome completo."),
      email: check.email(form.email),
      password: check.password(form.password, !editing),
      load_capacity_kg: courier
        ? check.number(form.load_capacity_kg, { label: "a capacidade de carga", min: 0, max: 1000 })
        : null,
    });
    setErrors(found);
    if (Object.keys(found).length) {
      setFormError(summarize(found));
      focusFirstError();
      return;
    }
    const body = {
      full_name: form.full_name,
      email: form.email,
      role: form.role,
      load_capacity_kg: courier ? parseDecimal(form.load_capacity_kg) : null,
    };
    setBusy(true);
    setFormError(null);
    try {
      if (editing && user) {
        await api(`/users/${id}`, {
          method: "PUT",
          body: {
            ...body,
            active: user.active,
            password: form.password || null,
            availability: courier ? form.availability : null,
          },
        });
        notify(`Dados de ${form.full_name} atualizados.`);
      } else {
        await api("/users", { method: "POST", body: { ...body, password: form.password } });
        notify(`${form.full_name} cadastrado como ${ROLE_LABELS[form.role].toLowerCase()}.`);
      }
      navigate("/usuarios");
    } catch (err) {
      const error = err as ApiError;
      const fields = { ...error.fields };
      if (/e-mail/i.test(error.message) && error.status === 409) fields.email = error.message;
      setErrors(fields);
      setFormError(error.status === 409 ? "Não foi possível salvar. Corrija o campo destacado." : error.message);
      focusFirstError();
    } finally {
      setBusy(false);
    }
  }

  const title = editing ? `Editar ${user?.full_name ?? "usuário"}` : "Novo usuário";
  const crumbs = [{ label: "Usuários", to: "/usuarios" }, { label: editing ? "Editar" : "Novo usuário" }];

  if (loading) return <p className="muted">Carregando usuário…</p>;
  if (loadError) {
    return (
      <section className="page state-page">
        <Breadcrumbs items={crumbs} />
        <h1>{loadError}</h1>
        <Link className="button primary" to="/usuarios">
          Voltar para os usuários
        </Link>
      </section>
    );
  }

  return (
    <section className="page">
      <Breadcrumbs items={crumbs} />
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p className="muted">O perfil define o que a pessoa pode ver e fazer no sistema.</p>
        </div>
      </div>
      <form className="form-card" onSubmit={submit} noValidate>
        <FormAlert message={formError} />
        <fieldset disabled={busy}>
          <legend>Dados de acesso</legend>
          <Field label="Nome completo" name="full_name" error={errors.full_name}>
            {(props) => <input {...props} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />}
          </Field>
          <Field label="E-mail" name="email" error={errors.email}>
            {(props) => (
              <input {...props} type="email" autoComplete="off" value={form.email} onChange={(e) => set("email", e.target.value)} />
            )}
          </Field>
          <Field
            label={editing ? "Nova senha" : "Senha"}
            name="password"
            error={errors.password}
            hint={editing ? "Deixe em branco para manter a senha atual." : "Mínimo de 8 caracteres, com letras e números."}
          >
            {(props) => (
              <input
                {...props}
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={(e) => set("password", e.target.value)}
              />
            )}
          </Field>
        </fieldset>

        <fieldset disabled={busy}>
          <legend>Perfil</legend>
          <div className="role-options" role="radiogroup" aria-label="Perfil">
            {ROLES.map((role) => (
              <button
                key={role}
                type="button"
                role="radio"
                aria-checked={form.role === role}
                className={form.role === role ? "role-option active" : "role-option"}
                onClick={() => set("role", role)}
                disabled={isSelf && role !== "ADMIN"}
              >
                <strong>{ROLE_LABELS[role]}</strong>
                <span>{ROLE_PERMISSIONS[role]}</span>
              </button>
            ))}
          </div>
          {isSelf && <small>Você não pode tirar o próprio acesso de administrador.</small>}
        </fieldset>

        {form.role === "COURIER" && (
          <fieldset disabled={busy}>
            <legend>Entregador</legend>
            <div className="grid-2">
              <Field
                label="Capacidade de carga (kg)"
                name="load_capacity_kg"
                error={errors.load_capacity_kg}
                hint="Soma máxima dos pedidos que ele leva ao mesmo tempo."
              >
                {(props) => (
                  <input
                    {...props}
                    inputMode="decimal"
                    value={form.load_capacity_kg}
                    onChange={(e) => set("load_capacity_kg", e.target.value)}
                  />
                )}
              </Field>
              {user?.courier && (
                <Field label="Disponibilidade" name="availability">
                  {(props) => (
                    <select
                      {...props}
                      value={form.availability}
                      onChange={(e) => set("availability", e.target.value as Availability)}
                    >
                      {(Object.keys(AVAILABILITY_LABELS) as Availability[]).map((value) => (
                        <option key={value} value={value}>
                          {AVAILABILITY_LABELS[value]}
                        </option>
                      ))}
                    </select>
                  )}
                </Field>
              )}
            </div>
          </fieldset>
        )}

        <div className="form-actions">
          <Link className="button quiet" to="/usuarios">
            Cancelar
          </Link>
          <button type="submit" className="button primary" disabled={busy}>
            {busy ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar usuário"}
          </button>
        </div>
      </form>
    </section>
  );
}
