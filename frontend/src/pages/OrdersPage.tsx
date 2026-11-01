import { useCallback, useEffect, useRef, useState } from "react";
import AutoRefresh from "../components/AutoRefresh";
import { Link, useNavigate, useSearchParams } from "react-router";
import { api, type AutoAssignResult, type Order, type OrderStatus } from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import { useConfirm } from "../components/ConfirmDialog";
import { STAFF_ROLES, STATUS_LABELS, formatKg, formatWindow } from "../labels";
import { useUser } from "../session";

const STATUSES: OrderStatus[] = ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"];

function matches(order: Order, term: string): boolean {
  if (!term) return true;
  const text = `#${order.id} ${order.customer.full_name} ${order.customer.phone ?? ""} ${order.delivery_address} ${
    order.assigned_courier?.full_name ?? ""
  }`;
  return text.toLocaleLowerCase("pt-BR").includes(term.toLocaleLowerCase("pt-BR"));
}

export default function OrdersPage() {
  const user = useUser();
  const canAssign = STAFF_ROLES.includes(user.role);
  const [dialog, confirm] = useConfirm();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const filter = (params.get("situacao") as OrderStatus | null) ?? null;
  const search = params.get("busca") ?? "";
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [assigning, setAssigning] = useState(false);
  const [assignment, setAssignment] = useState<AutoAssignResult | null>(null);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const assignmentLock = useRef(false);
  const requestId = useRef(0);

  const load = useCallback(async () => {
    if (assignmentLock.current) return;
    const request = ++requestId.current;
    try {
      const next = await api<Order[]>("/orders");
      if (request !== requestId.current) return;
      setOrders(next);
      setUpdatedAt(new Date());
      setError(null);
    } catch (err) {
      if (request === requestId.current) setError((err as Error).message);
    } finally {
      if (request === requestId.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    return () => { requestId.current++; };
  }, [load]);

  const pendingCount = orders.filter((order) => order.status === "PENDING" && !order.assigned_courier).length;

  async function autoAssign() {
    if (!canAssign || assignmentLock.current || assigning || loading || error || pendingCount === 0) return;
    assignmentLock.current = true;
    const confirmed = await confirm({
      title: "Atribuir pedidos automaticamente?",
      message: `Serão avaliados todos os ${pendingCount} pedidos pendentes sem entregador, inclusive os ocultos pelos filtros. O sistema escolherá os entregadores elegíveis. Os pedidos que não puderem ser atribuídos continuarão pendentes, com o motivo no resumo. Depois, acesse Rotas para gerar os trajetos.`,
      confirmLabel: "Atribuir pedidos",
      tone: "primary",
    });
    if (!confirmed) {
      assignmentLock.current = false;
      return;
    }
    requestId.current++;
    setAssigning(true);
    setAssignment(null);
    setAssignmentError(null);
    try {
      const result = await api<AutoAssignResult>("/orders/auto-assign", { method: "POST" });
      setAssignment(result);
      // Mantém os pedidos atribuídos corretos mesmo se a atualização da lista falhar.
      const assigned = new Map(result.assigned.map((item) => [item.order_id, item]));
      setOrders((current) => current.map((order) => {
        const item = assigned.get(order.id);
        return item ? { ...order, status: "ASSIGNED", assigned_courier: { id: item.courier_id, full_name: item.courier_name } } : order;
      }));
    } catch (err) {
      setAssignmentError((err as Error).message);
    } finally {
      assignmentLock.current = false;
      await load();
      setAssigning(false);
    }
  }

  function updateParams(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    setParams(next, { replace: true });
  }

  const searched = orders.filter((order) => matches(order, search.trim()));
  const counts = Object.fromEntries(STATUSES.map((s) => [s, searched.filter((o) => o.status === s).length]));
  const visible = filter ? searched.filter((order) => order.status === filter) : searched;

  return (
    <section className="page">
      {dialog}
      <div className="page-head">
        <div>
          <h1>Pedidos</h1>
          <p className="muted">Cadastre os pedidos do dia, escolha quem vai entregar e acompanhe cada etapa.</p>
        </div>
        {canAssign && (
          <div className="page-actions">
            <button type="button" className="button quiet" onClick={autoAssign} disabled={assigning || loading || Boolean(error) || pendingCount === 0} aria-describedby="auto-assign-help" aria-busy={assigning}>
              {assigning ? "Atribuindo pedidos…" : "Atribuir automaticamente"}
            </button>
            <Link className="button primary" to="/pedidos/novo">Novo pedido</Link>
          </div>
        )}
      </div>

      {canAssign && (
        <p className="inline-note" id="auto-assign-help">
          {loading ? "Consultando pedidos pendentes…" : `${pendingCount} ${pendingCount === 1 ? "pedido pendente sem entregador" : "pedidos pendentes sem entregador"}.`}{" "}
          A atribuição automática considera todos os pedidos pendentes, independentemente dos filtros.{" "}
          <Link to="/rotas">Ver e gerar rotas</Link>
        </p>
      )}
      {assigning && <p className="inline-note" role="status">Atribuindo pedidos e atualizando a lista. Aguarde…</p>}
      {assignmentError && <div className="alert error" role="alert">Não foi possível confirmar a atribuição: {assignmentError} Confira a lista atualizada antes de tentar novamente.</div>}
      {assignment && (
        <section className="assignment-result" aria-labelledby="assignment-title">
          <h2 id="assignment-title">Resultado da atribuição automática</h2>
          <p role="status">
            <strong>{assignment.assigned.length}</strong> {assignment.assigned.length === 1 ? "pedido atribuído" : "pedidos atribuídos"} ·{" "}
            <strong>{assignment.skipped.length}</strong> {assignment.skipped.length === 1 ? "pedido não atribuído" : "pedidos não atribuídos"}.
          </p>
          {assignment.assigned.length === 0 && assignment.skipped.length === 0 && <p>Nenhum pedido pendente disponível no momento da operação. A lista foi atualizada.</p>}
          {assignment.assigned.length > 0 && (
            <div>
              <h3>Pedidos atribuídos</h3>
              <ul>{assignment.assigned.map((item) => <li key={item.order_id}><Link to={`/pedidos/${item.order_id}`}>Pedido #{item.order_id}</Link> · {item.courier_name}</li>)}</ul>
            </div>
          )}
          {assignment.skipped.length > 0 && (
            <div>
              <h3>Pedidos não atribuídos</h3>
              <ul>{assignment.skipped.map((item) => <li key={item.order_id}><Link to={`/pedidos/${item.order_id}`}>Pedido #{item.order_id}</Link>: {item.reason}</li>)}</ul>
              <p className="muted">Confira os motivos acima antes de tentar novamente ou atribuir manualmente nos detalhes do pedido.</p>
            </div>
          )}
          <p>Próximo passo: gere as rotas para os pedidos atribuídos.</p>
          <Link className="button primary" to="/rotas">Ir para Rotas</Link>
        </section>
      )}
      <AutoRefresh onRefresh={load} updatedAt={updatedAt} />
      <div className="toolbar">
        <label className="search">
          <span className="sr-only">Buscar pedidos</span>
          <input
            type="search"
            placeholder="Buscar por cliente, endereço, entregador ou número"
            value={search}
            onChange={(e) => updateParams({ busca: e.target.value })}
          />
        </label>
        <div className="filters" role="group" aria-label="Filtrar por situação">
          <button type="button" className={filter ? "chip" : "chip active"} aria-pressed={!filter} onClick={() => updateParams({ situacao: null })}>
            Todos <span>{searched.length}</span>
          </button>
          {STATUSES.map((status) => (
            <button
              key={status}
              type="button"
              className={filter === status ? "chip active" : "chip"}
              aria-pressed={filter === status}
              onClick={() => updateParams({ situacao: status })}
            >
              {STATUS_LABELS[status]} <span>{counts[status]}</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="alert error" role="alert">
          {error}{" "}
          <button type="button" className="link" onClick={load}>
            Tentar de novo
          </button>
        </div>
      )}

      {loading ? (
        <p className="muted" role="status">Carregando pedidos…</p>
      ) : error && orders.length === 0 ? null : visible.length === 0 ? (
        <div className="empty">
          {orders.length === 0 ? (
            <>
              <p>Nenhum pedido cadastrado ainda.</p>
              <Link className="button primary" to="/pedidos/novo">
                Cadastrar o primeiro pedido
              </Link>
            </>
          ) : (
            <>
              <p>Nenhum pedido encontrado com esses filtros.</p>
              <button type="button" className="button quiet" onClick={() => updateParams({ busca: null, situacao: null })}>
                Limpar busca e filtros
              </button>
            </>
          )}
        </div>
      ) : (
        <div className="table-wrap">
          <table className="clickable">
            <thead>
              <tr>
                <th scope="col">Pedido</th>
                <th scope="col">Cliente</th>
                <th scope="col">Endereço de entrega</th>
                <th scope="col">Janela de entrega</th>
                <th scope="col">Prioridade</th>
                <th scope="col">Entregador</th>
                <th scope="col">Situação</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((order) => (
                <tr key={order.id} onClick={() => navigate(`/pedidos/${order.id}`)}>
                  <td className="num">
                    <Link to={`/pedidos/${order.id}`} onClick={(e) => e.stopPropagation()}>
                      #{order.id}
                    </Link>
                  </td>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
