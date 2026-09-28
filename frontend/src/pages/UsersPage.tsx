import { type FormEvent, useCallback, useEffect, useState } from "react";
import { api, type Availability, type Role, type User } from "../api";
import Drawer from "../components/Drawer";
import { AVAILABILITY_LABELS, ROLE_LABELS, ROLE_PERMISSIONS, formatKg } from "../labels";

const ROLES: Role[] = ["ADMIN", "ATTENDANT", "COURIER"];

export default function UsersPage({ currentUser }: { currentUser: User }) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [editing, setEditing] = useState<User | "new" | null>(null);

  const load = useCallback(async () => {
    try {
      setUsers(await api<User[]>("/users"));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 3500);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function toggleActive(user: User) {
    try {
      if (user.active) {
        if (!window.confirm(`Desativar ${user.full_name}? A pessoa perde o acesso, mas o histórico é mantido.`)) return;
        await api(`/users/${user.id}`, { method: "DELETE" });
        setToast(`${user.full_name} foi desativado.`);
      } else {
        await api(`/users/${user.id}`, {
          method: "PUT",
          body: {
            full_name: user.full_name,
            email: user.email,
            role: user.role,
            active: true,
            availability: user.courier ? "AVAILABLE" : null,
          },
        });
        setToast(`${user.full_name} foi reativado.`);
      }
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Usuários</h1>
          <p className="muted">Quem acessa o sistema e o que cada perfil pode fazer.</p>
        </div>
        <button type="button" className="button primary" onClick={() => setEditing("new")}>
          Novo usuário
        </button>
      </div>

      <ul className="role-guide">
        {ROLES.map((role) => (
          <li key={role}>
            <span className={`role role-${role.toLowerCase()}`}>{ROLE_LABELS[role]}</span>
            <span>{ROLE_PERMISSIONS[role]}</span>
          </li>
        ))}
      </ul>

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="muted">Carregando usuários…</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Nome</th>
                <th scope="col">E-mail</th>
                <th scope="col">Perfil</th>
                <th scope="col">Entregas</th>
                <th scope="col">Acesso</th>
                <th scope="col">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className={user.active ? "" : "inactive"}>
                  <td>
                    <strong>{user.full_name}</strong>
                    {user.id === currentUser.id && <span className="sub">Você</span>}
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`role role-${user.role.toLowerCase()}`}>{ROLE_LABELS[user.role]}</span>
                  </td>
                  <td>
                    {user.role === "COURIER" && user.courier ? (
                      <>
                        {AVAILABILITY_LABELS[user.courier.availability]}
                        <span className="sub">Carga até {formatKg(user.courier.load_capacity_kg)}</span>
                      </>
                    ) : (
                      <span className="muted">Não se aplica</span>
                    )}
                  </td>
                  <td>{user.active ? "Ativo" : <span className="muted">Desativado</span>}</td>
                  <td className="row-actions">
                    <button type="button" className="button quiet small" onClick={() => setEditing(user)}>
                      Editar
                    </button>
                    {user.id !== currentUser.id && (
                      <button
                        type="button"
                        className={user.active ? "button danger small" : "button quiet small"}
                        onClick={() => toggleActive(user)}
                      >
                        {user.active ? "Desativar" : "Reativar"}
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
        <Drawer title={editing === "new" ? "Novo usuário" : `Editar ${editing.full_name}`} onClose={() => setEditing(null)}>
          <UserForm
            user={editing === "new" ? null : editing}
            isSelf={editing !== "new" && editing.id === currentUser.id}
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

interface FormProps {
  user: User | null;
  isSelf: boolean;
  onSaved: (message: string) => void;
}

function UserForm({ user, isSelf, onSaved }: FormProps) {
  const [form, setForm] = useState({
    full_name: user?.full_name ?? "",
    email: user?.email ?? "",
    role: user?.role ?? ("ATTENDANT" as Role),
    password: "",
    load_capacity_kg: user?.courier ? String(user.courier.load_capacity_kg) : "",
    availability: user?.courier?.availability ?? ("AVAILABLE" as Availability),
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(event: FormEvent) {
    event.preventDefault();
    const capacity = form.load_capacity_kg ? Number(form.load_capacity_kg.replace(",", ".")) : null;
    const common = {
      full_name: form.full_name,
      email: form.email,
      role: form.role,
      load_capacity_kg: form.role === "COURIER" ? capacity : null,
    };
    setBusy(true);
    setError(null);
    try {
      if (user) {
        await api(`/users/${user.id}`, {
          method: "PUT",
          body: {
            ...common,
            active: user.active,
            password: form.password || null,
            availability: form.role === "COURIER" ? form.availability : null,
          },
        });
        onSaved(`Dados de ${form.full_name} atualizados.`);
      } else {
        await api("/users", { method: "POST", body: { ...common, password: form.password } });
        onSaved(`${form.full_name} cadastrado como ${ROLE_LABELS[form.role].toLowerCase()}.`);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="drawer-form" onSubmit={submit} noValidate>
      <fieldset disabled={busy}>
        <legend>Dados de acesso</legend>
        <label>
          Nome completo
          <input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} autoComplete="off" required />
        </label>
        <label>
          E-mail
          <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} autoComplete="off" required />
        </label>
        <label>
          {user ? "Nova senha" : "Senha"}
          <input
            type="password"
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
            autoComplete="new-password"
            required={!user}
          />
          <small>{user ? "Deixe em branco para manter a senha atual." : "Mínimo de 8 caracteres."}</small>
        </label>
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
            <label>
              Capacidade de carga (kg)
              <input
                value={form.load_capacity_kg}
                onChange={(e) => set("load_capacity_kg", e.target.value)}
                inputMode="decimal"
                required
              />
            </label>
            {user?.courier && (
              <label>
                Disponibilidade
                <select value={form.availability} onChange={(e) => set("availability", e.target.value as Availability)}>
                  {(Object.keys(AVAILABILITY_LABELS) as Availability[]).map((value) => (
                    <option key={value} value={value}>
                      {AVAILABILITY_LABELS[value]}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
        </fieldset>
      )}

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
      <div className="drawer-actions">
        <button type="submit" className="button primary" disabled={busy}>
          {busy ? "Salvando…" : user ? "Salvar alterações" : "Cadastrar usuário"}
        </button>
      </div>
    </form>
  );
}
