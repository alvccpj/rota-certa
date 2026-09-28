import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { api, type Role, type User } from "../api";
import { useConfirm } from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { AVAILABILITY_LABELS, ROLE_LABELS, ROLE_PERMISSIONS, formatKg } from "../labels";
import { useUser } from "../session";

const ROLES: Role[] = ["ADMIN", "ATTENDANT", "COURIER"];

export default function UsersPage() {
  const currentUser = useUser();
  const notify = useToast();
  const [dialog, confirm] = useConfirm();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  async function toggleActive(user: User) {
    try {
      if (user.active) {
        const confirmed = await confirm({
          title: `Desativar ${user.full_name}?`,
          message: "A pessoa perde o acesso ao sistema na hora. O histórico de pedidos é mantido e você pode reativá-la depois.",
          confirmLabel: "Desativar",
        });
        if (!confirmed) return;
        await api(`/users/${user.id}`, { method: "DELETE" });
        notify(`${user.full_name} foi desativado.`);
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
        notify(`${user.full_name} foi reativado.`);
      }
      load();
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Usuários</h1>
          <p className="muted">Quem acessa o sistema e o que cada perfil pode fazer.</p>
        </div>
        <Link className="button primary" to="/usuarios/novo">
          Novo usuário
        </Link>
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
                    <Link className="button quiet small" to={`/usuarios/${user.id}/editar`}>
                      Editar
                    </Link>
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
      {dialog}
    </section>
  );
}
