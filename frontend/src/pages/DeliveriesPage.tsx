import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { api, type Availability, type MyRoute, type Order, type OrderStatus, type User } from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import RouteMap from "../components/RouteMap";
import { useToast } from "../components/Toast";
import {
  ROUTE_STATUS_LABELS,
  STATUS_LABELS,
  formatDuration,
  formatKg,
  formatKm,
  formatTime,
  formatWindow,
} from "../labels";
import { useSession, useUser } from "../session";
import { NEXT_STEP } from "./OrderDetailPage";

const STATUSES: OrderStatus[] = ["ASSIGNED", "IN_ROUTE", "DELIVERED"];
const AVAILABILITY_OPTIONS: { value: Availability; label: string }[] = [
  { value: "AVAILABLE", label: "Disponível" },
  { value: "OFFLINE", label: "Fora de serviço" },
];

export default function DeliveriesPage() {
  const user = useUser();
  const { updateUser } = useSession();
  const notify = useToast();
  const [orders, setOrders] = useState<Order[]>([]);
  const [myRoute, setMyRoute] = useState<MyRoute | null>(null);
  const [starting, setStarting] = useState(false);
  const [filter, setFilter] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const availability = user.courier?.availability ?? "OFFLINE";

  const load = useCallback(async () => {
    try {
      const [nextOrders, nextRoute] = await Promise.all([api<Order[]>("/orders"), api<MyRoute>("/routes/me")]);
      setOrders(nextOrders);
      setMyRoute(nextRoute);
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

  async function advance(order: Order) {
    const step = NEXT_STEP[order.status];
    if (!step) return;
    try {
      await api(`/orders/${order.id}/status`, { method: "PATCH", body: { status: step.status } });
      notify(step.done);
      load();
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }

  async function startRoute(routeId: number) {
    setStarting(true);
    try {
      await api(`/routes/${routeId}/start`, { method: "PATCH" });
      notify("Rota iniciada. Siga a ordem das paradas.");
      load();
    } catch (err) {
      notify((err as Error).message, "error");
    } finally {
      setStarting(false);
    }
  }

  async function changeAvailability(value: Availability) {
    if (value === availability) return;
    try {
      await api("/couriers/me/availability", { method: "PATCH", body: { availability: value } });
      updateUser(await api<User>("/auth/me"));
      notify(value === "OFFLINE" ? "Você está fora de serviço e não receberá novos pedidos." : "Você está disponível para novos pedidos.");
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }

  const counts = Object.fromEntries(STATUSES.map((s) => [s, orders.filter((o) => o.status === s).length]));
  const visible = (filter ? orders.filter((o) => o.status === filter) : orders).filter((o) => o.status !== "CANCELLED");

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Minhas entregas</h1>
          <p className="muted">Pedidos atribuídos a você. Atualize o andamento a cada etapa.</p>
        </div>
        <div className="field availability">
          <span className="field-label">Sua disponibilidade</span>
          <div className="segmented two" role="radiogroup" aria-label="Sua disponibilidade">
            {AVAILABILITY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={availability === option.value}
                className={availability === option.value ? "active" : ""}
                onClick={() => changeAvailability(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {myRoute?.route && <MyRouteCard data={myRoute} starting={starting} onStart={startRoute} />}

      <div className="filters" role="group" aria-label="Filtrar por situação">
        <button type="button" className={filter ? "chip" : "chip active"} onClick={() => setFilter(null)}>
          Todas <span>{orders.filter((o) => o.status !== "CANCELLED").length}</span>
        </button>
        {STATUSES.map((status) => (
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
        <div className="alert error" role="alert">
          {error}{" "}
          <button type="button" className="link" onClick={load}>
            Tentar de novo
          </button>
        </div>
      )}

      {loading ? (
        <p className="muted">Carregando entregas…</p>
      ) : visible.length === 0 ? (
        <div className="empty">
          <p>
            {orders.length === 0
              ? "Nenhuma entrega atribuída a você no momento."
              : "Nenhuma entrega com essa situação."}
          </p>
        </div>
      ) : (
        <ul className="delivery-list">
          {visible.map((order) => {
            const step = NEXT_STEP[order.status];
            return (
              <li key={order.id} className="delivery">
                <div className="delivery-top">
                  <StatusBadge status={order.status} />
                  <Priority value={order.priority} />
                </div>
                <h3>
                  <Link to={`/pedidos/${order.id}`}>{order.customer.full_name}</Link>
                </h3>
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
                  <Link className="button quiet" to={`/pedidos/${order.id}`}>
                    Ver detalhes
                  </Link>
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
      )}
    </section>
  );
}

function MyRouteCard({ data, starting, onStart }: { data: MyRoute; starting: boolean; onStart: (id: number) => void }) {
  const route = data.route!;
  const next = route.stops.find((stop) => stop.order_status !== "DELIVERED" && stop.order_status !== "CANCELLED");
  return (
    <div className="my-route">
      <div className="my-route-head">
        <div>
          <h2>Sua rota</h2>
          <p className="muted">
            {ROUTE_STATUS_LABELS[route.status]} · {route.stops.length} {route.stops.length === 1 ? "parada" : "paradas"} ·{" "}
            {formatKm(route.total_distance_km)} ·{" "}
            {formatDuration(route.estimated_duration_min)} estimados
          </p>
        </div>
        {route.status === "PLANNED" && (
          <button type="button" className="button primary" onClick={() => onStart(route.id)} disabled={starting}>
            {starting ? "Iniciando…" : "Iniciar rota"}
          </button>
        )}
      </div>
      <RouteMap routes={[route]} depot={data.depot} label="Mapa da sua rota" />
      <ol className="stop-list">
        {route.stops.map((stop) => (
          <li
            key={stop.order_id}
            className={stop.order_status === "DELIVERED" ? "done" : stop === next ? "next" : undefined}
          >
            <span className="stop-number">{stop.sequence}</span>
            <div>
              <Link to={`/pedidos/${stop.order_id}`}>{stop.customer_name}</Link>
              <span className="sub">{stop.delivery_address}</span>
            </div>
            <div className="stop-meta">
              <span>{stop === next ? "Próxima · " : ""}{formatTime(stop.estimated_arrival)}</span>
              <StatusBadge status={stop.order_status} />
            </div>
          </li>
        ))}
      </ol>
      <p className="inline-note">Saída e retorno: {data.depot.address}</p>
    </div>
  );
}
