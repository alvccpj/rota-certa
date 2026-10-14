import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { api, type Order, type Role, type User } from "../api";
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
  const [activeOrders, setActiveOrders] = useState<Order[]>([]);

  const load = useCallback(async () => {
    try {
      const [nextUsers, orders] = await Promise.all([api<User[]>("/users"), api<Order[]>("/orders")]);
      setUsers(nextUsers);
      setActiveOrders(orders.filter((order) => order.status === "ASSIGNED" || order.status === "IN_ROUTE"));
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
      <p className="inline-note">
        Para desativar um entregador ou mudar seu perfil, finalize, cancele ou reatribua seus pedidos ativos.
        Entregas em rota precisam ser resolvidas antes de colocá-lo fora de serviço.
      </p>
      <button type="button" className="link" onClick={load}>Atualizar usuários e entregas</button>

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
                        <span className="sub">
                          {activeOrders.filter((order) => order.assigned_courier?.id === user.courier?.id).map((order) => (
                            <Link key={order.id} to={`/pedidos/${order.id}`} style={{ marginRight: 8 }}>Pedido #{order.id}</Link>
                          ))}
                        </span>
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
                        disabled={user.active && activeOrders.some((order) => order.assigned_courier?.id === user.courier?.id)}
                        title="Resolva os pedidos ativos antes de desativar o entregador."
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
