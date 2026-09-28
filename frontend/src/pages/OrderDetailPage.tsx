import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { api, ApiError, type OrderDetail, type OrderStatus } from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import Breadcrumbs from "../components/Breadcrumbs";
import { useConfirm } from "../components/ConfirmDialog";
import Field from "../components/Field";
import MapPicker from "../components/MapPicker";
import { useToast } from "../components/Toast";
import { STATUS_LABELS, formatDateTime, formatKg, formatWindow } from "../labels";
import { useUser } from "../session";

export const NEXT_STEP: Partial<Record<OrderStatus, { status: OrderStatus; label: string; done: string }>> = {
  ASSIGNED: { status: "IN_ROUTE", label: "Sair para entrega", done: "Entrega iniciada." },
  IN_ROUTE: { status: "DELIVERED", label: "Confirmar entrega", done: "Entrega confirmada." },
};

export default function OrderDetailPage() {
  const { id } = useParams();
  const user = useUser();
  const navigate = useNavigate();
  const notify = useToast();
  const [dialog, confirm] = useConfirm();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string | null>(null);

  const isCourier = user.role === "COURIER";
  const listPath = isCourier ? "/entregas" : "/pedidos";

  const load = useCallback(async () => {
    try {
      setOrder(await api<OrderDetail>(`/orders/${id}`));
      setError(null);
    } catch (err) {
      setError(err as ApiError);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function changeStatus(status: OrderStatus, note: string | null, done: string) {
    setBusy(true);
    try {
      await api(`/orders/${id}/status`, { method: "PATCH", body: { status, note } });
      notify(done);
      setCancelling(false);
      await load();
    } catch (err) {
      notify((err as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function submitCancel(event: FormEvent) {
    event.preventDefault();
    if (reason.trim().length < 5) {
      setReasonError("Explique o motivo em pelo menos 5 caracteres. Ele fica registrado no histórico.");
      return;
    }
    await changeStatus("CANCELLED", reason.trim(), `Pedido #${id} cancelado.`);
  }

  async function remove() {
    const confirmed = await confirm({
      title: `Excluir o pedido #${id}?`,
      message: "O pedido e o seu histórico serão apagados definitivamente. Para manter o registro, cancele o pedido.",
      confirmLabel: "Excluir pedido",
    });
    if (!confirmed) return;
    try {
      await api(`/orders/${id}`, { method: "DELETE" });
      notify(`Pedido #${id} excluído.`);
      navigate("/pedidos");
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }

  const crumbs = [
    { label: isCourier ? "Minhas entregas" : "Pedidos", to: listPath },
    { label: `Pedido #${id}` },
  ];

  if (error) {
    return (
      <section className="page state-page">
        <Breadcrumbs items={crumbs} />
        <h1>{error.status === 404 ? `O pedido #${id} não foi encontrado` : "Não foi possível abrir o pedido"}</h1>
        <p className="muted">
          {error.status === 404
            ? "Ele pode ter sido excluído ou não pertencer ao seu estabelecimento."
            : error.message}
        </p>
        <Link className="button primary" to={listPath}>
          Voltar para a lista
        </Link>
      </section>
    );
  }
  if (!order) return <p className="muted">Carregando pedido…</p>;

  const step = NEXT_STEP[order.status];
  const locked = order.status === "DELIVERED" || order.status === "CANCELLED";

  return (
    <section className="page">
      <Breadcrumbs items={crumbs} />
      <div className="page-head">
        <div className="title-row">
          <h1>Pedido #{order.id}</h1>
          <StatusBadge status={order.status} />
        </div>
        <div className="actions">
          {isCourier && step && (
            <button
              type="button"
              className="button primary"
              disabled={busy}
              onClick={() => changeStatus(step.status, null, step.done)}
            >
              {step.label}
            </button>
          )}
          {!isCourier && !locked && (
            <>
              <Link className="button primary" to={`/pedidos/${order.id}/editar`}>
                Editar pedido
              </Link>
              <button type="button" className="button quiet" onClick={() => setCancelling((v) => !v)} disabled={busy}>
                Cancelar pedido
              </button>
            </>
          )}
          {!isCourier && locked && (
            <button
              type="button"
              className="button quiet"
              disabled={busy}
              onClick={() => changeStatus("PENDING", "Pedido reaberto", `Pedido #${order.id} reaberto como pendente.`)}
            >
              Reabrir pedido
            </button>
          )}
          {user.role === "ADMIN" && (
            <button type="button" className="button danger" onClick={remove} disabled={busy}>
              Excluir
            </button>
          )}
        </div>
      </div>

      {cancelling && (
        <form className="form-card cancel-card" onSubmit={submitCancel} noValidate>
          <Field
            label="Motivo do cancelamento"
            name="cancel_reason"
            error={reasonError ?? undefined}
            hint="O motivo fica registrado no histórico do pedido."
          >
            {(props) => (
              <input
                {...props}
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  setReasonError(null);
                }}
                placeholder="Ex.: cliente desistiu da compra"
                autoFocus
              />
            )}
          </Field>
          <div className="form-actions">
            <button type="button" className="button quiet" onClick={() => setCancelling(false)}>
              Voltar
            </button>
            <button type="submit" className="button danger-solid" disabled={busy}>
              Confirmar cancelamento
            </button>
          </div>
        </form>
      )}

      <div className="detail-grid">
        <div className="detail-main">
          <dl className="detail-list">
            <div>
              <dt>Cliente</dt>
              <dd>
                {order.customer.full_name}
                {order.customer.phone && (
                  <a className="sub" href={`tel:${order.customer.phone.replace(/\D/g, "")}`}>
                    {order.customer.phone}
                  </a>
                )}
              </dd>
            </div>
            <div>
              <dt>Endereço de entrega</dt>
              <dd>{order.delivery_address}</dd>
            </div>
            <div>
              <dt>Horário</dt>
              <dd>{formatWindow(order.desired_start, order.desired_end)}</dd>
            </div>
            <div>
              <dt>Peso e prioridade</dt>
              <dd>
                {formatKg(order.weight_kg)} <Priority value={order.priority} />
              </dd>
            </div>
            <div>
              <dt>Entregador</dt>
              <dd>{order.assigned_courier?.full_name ?? <span className="muted">Sem entregador</span>}</dd>
            </div>
          </dl>
          <MapPicker latitude={order.latitude} longitude={order.longitude} zoom={15} />
          <a
            className="button quiet"
            href={`https://www.google.com/maps/dir/?api=1&destination=${order.latitude},${order.longitude}`}
            target="_blank"
            rel="noreferrer"
          >
            Abrir rota no Google Maps
          </a>
        </div>

        <aside className="timeline-card" aria-labelledby="historico">
          <h2 id="historico">Histórico</h2>
          {order.history.length === 0 ? (
            <p className="muted">Sem registros para este pedido.</p>
          ) : (
            <ol className="timeline">
              {[...order.history].reverse().map((event, index) => (
                <li key={`${event.changed_at}-${index}`}>
                  <div className="timeline-head">
                    <StatusBadge status={event.status} />
                    <time dateTime={event.changed_at}>{formatDateTime(event.changed_at)}</time>
                  </div>
                  <p>{event.note ?? STATUS_LABELS[event.status]}</p>
                  {event.changed_by && <p className="sub">por {event.changed_by}</p>}
                </li>
              ))}
            </ol>
          )}
        </aside>
      </div>
      {dialog}
    </section>
  );
}
