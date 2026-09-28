import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { api, type Order, type OrderStatus } from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import { STATUS_LABELS, formatKg, formatWindow } from "../labels";

const STATUSES: OrderStatus[] = ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"];

function matches(order: Order, term: string): boolean {
  if (!term) return true;
  const text = `#${order.id} ${order.customer.full_name} ${order.customer.phone ?? ""} ${order.delivery_address} ${
    order.assigned_courier?.full_name ?? ""
  }`;
  return text.toLocaleLowerCase("pt-BR").includes(term.toLocaleLowerCase("pt-BR"));
}

export default function OrdersPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const filter = (params.get("situacao") as OrderStatus | null) ?? null;
  const search = params.get("busca") ?? "";
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
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
  }, [load]);

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
      <div className="page-head">
        <div>
          <h1>Pedidos</h1>
          <p className="muted">Cadastre os pedidos do dia, escolha quem vai entregar e acompanhe cada etapa.</p>
        </div>
        <Link className="button primary" to="/pedidos/novo">
          Novo pedido
        </Link>
      </div>

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
          <button type="button" className={filter ? "chip" : "chip active"} onClick={() => updateParams({ situacao: null })}>
            Todos <span>{searched.length}</span>
          </button>
          {STATUSES.map((status) => (
            <button
              key={status}
              type="button"
              className={filter === status ? "chip active" : "chip"}
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
        <p className="muted">Carregando pedidos…</p>
      ) : visible.length === 0 ? (
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
                <th scope="col">Horário</th>
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
