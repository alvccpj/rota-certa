import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { api, type OperationalHistoryEvent, type OrderStatus } from "../api";
import { StatusBadge } from "../components/Badges";
import Breadcrumbs from "../components/Breadcrumbs";
import { MODE_LABELS, STATUS_LABELS, formatDateTime, formatMs } from "../labels";
import { DEFAULT_REPORT_END, DEFAULT_REPORT_START } from "../reporting";

const STATUSES: OrderStatus[] = ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"];

export default function HistoryPage() {
  const [start, setStart] = useState(DEFAULT_REPORT_START);
  const [end, setEnd] = useState(DEFAULT_REPORT_END);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [events, setEvents] = useState<OperationalHistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const requestId = useRef(0);

  const load = useCallback(async (filters?: { start: string; end: string; query: string; type: string; status: string }) => {
    const request = ++requestId.current;
    const current = filters ?? { start: DEFAULT_REPORT_START, end: DEFAULT_REPORT_END, query: "", type: "", status: "" };
    if (!current.start || !current.end || current.start > current.end) {
      setError("Informe um período válido: a data inicial não pode ser posterior à final.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ start: current.start, end: current.end });
    if (current.query.trim()) params.set("q", current.query.trim());
    if (current.type) params.set("type", current.type);
    if (current.status) params.set("status", current.status);
    try {
      const next = await api<OperationalHistoryEvent[]>(`/dashboard/history?${params}`);
      if (request === requestId.current) setEvents(next);
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

  function clearFilters() {
    setStart(DEFAULT_REPORT_START);
    setEnd(DEFAULT_REPORT_END);
    setQuery("");
    setType("");
    setStatus("");
    void load();
  }

  return (
    <section className="page history-page">
      <Breadcrumbs items={[{ label: "Histórico" }]} />
      <div className="page-head">
        <div>
          <h1>Histórico operacional</h1>
          <p className="muted">Acompanhe mudanças de situação dos pedidos e execuções do otimizador em ordem cronológica.</p>
        </div>
      </div>

      <form className="report-filters" aria-label="Filtros do histórico" aria-describedby="history-filter-help" onSubmit={(event) => { event.preventDefault(); void load({ start, end, query, type, status }); }}>
        <label className="wide-filter">Buscar operações
          <input type="search" placeholder="Pedido, cliente, endereço, observação ou responsável" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label>Data inicial<input type="date" required value={start} max={end} onChange={(event) => setStart(event.target.value)} /></label>
        <label>Data final<input type="date" required value={end} min={start} onChange={(event) => setEnd(event.target.value)} /></label>
        <label>Tipo de operação
          <select value={type} onChange={(event) => { setType(event.target.value); if (event.target.value === "OPTIMIZATION") setStatus(""); }}>
            <option value="">Todos</option>
            <option value="ORDER_STATUS">Pedidos</option>
            <option value="OPTIMIZATION">Otimização</option>
          </select>
        </label>
        <label>Situação do pedido
          <select value={status} disabled={type === "OPTIMIZATION"} aria-describedby={type === "OPTIMIZATION" ? "history-status-help" : undefined} onChange={(event) => setStatus(event.target.value as OrderStatus | "")}>
            <option value="">Todas</option>
            {STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
          </select>
        </label>
        <div className="filter-actions">
          <button className="button primary" type="submit" disabled={loading}>{loading ? "Consultando…" : "Aplicar filtros"}</button>
          <button className="button quiet" type="button" onClick={clearFilters}>Limpar filtros</button>
        </div>
      </form>
      <p className="inline-note" id="history-filter-help">Use Aplicar filtros para atualizar os resultados. Limpar filtros restaura os últimos 7 dias e remove a busca e as demais seleções.</p>
      {type === "OPTIMIZATION" && <p className="inline-note" id="history-status-help">O filtro de situação do pedido só se aplica às operações de pedidos.</p>}

      {error && <div className="alert error" role="alert">{error}{" "}<button type="button" className="link" onClick={() => void load({ start, end, query, type, status })}>Tentar de novo</button></div>}
      {!loading && !error && <p className="result-count" role="status">{events.length} {events.length === 1 ? "operação encontrada" : "operações encontradas"}</p>}

      {loading ? (
        <p className="muted" role="status">Consultando operações…</p>
      ) : error ? null : events.length === 0 ? (
        <div className="empty"><p>Nenhuma operação corresponde aos critérios informados. Ajuste o período ou limpe os filtros para tentar novamente.</p><button className="button quiet" type="button" onClick={clearFilters}>Limpar filtros</button></div>
      ) : (
        <ol className="operation-history" aria-label="Operações registradas">
          {events.map((event) => (
            <li key={event.event_id} className={`operation-event event-${event.event_type.toLowerCase()}`}>
              <time dateTime={event.occurred_at}>{formatDateTime(event.occurred_at)}</time>
              <div className="operation-marker" aria-hidden="true" />
              <div className="operation-content">
                {event.event_type === "ORDER_STATUS" ? (
                  <>
                    <div className="operation-heading">
                      <strong><Link to={`/pedidos/${event.order_id}`}>Pedido #{event.order_id}</Link> · {event.customer_name}</strong>
                      {event.status && <StatusBadge status={event.status} />}
                    </div>
                    <p>{event.note ?? "Situação atualizada"}</p>
                  </>
                ) : (
                  <>
                    <div className="operation-heading"><strong>Execução do otimizador</strong><span className="history-kind">Desempenho</span></div>
                    <p>{event.order_count} pedidos processados em {event.execution_mode ? MODE_LABELS[event.execution_mode] : "modo não informado"} · {event.execution_time_ms == null ? "tempo não informado" : formatMs(event.execution_time_ms)}</p>
                  </>
                )}
                <span className="operation-author">Responsável: {event.actor_name ?? "Não informado"}</span>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
