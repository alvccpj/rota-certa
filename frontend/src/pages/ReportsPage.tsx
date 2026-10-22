import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import { api, type CourierOption, type DashboardReportRow, type OrderStatus } from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import Breadcrumbs from "../components/Breadcrumbs";
import { useToast } from "../components/Toast";
import { PRIORITY_LABELS, ROUTE_STATUS_LABELS, STATUS_LABELS, formatDateTime, formatKg } from "../labels";
import {
  DEFAULT_REPORT_END,
  DEFAULT_REPORT_START,
  downloadOperationalReport,
} from "../reporting";

const STATUSES: OrderStatus[] = ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"];

export default function ReportsPage() {
  const notify = useToast();
  const [start, setStart] = useState(DEFAULT_REPORT_START);
  const [end, setEnd] = useState(DEFAULT_REPORT_END);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [courierId, setCourierId] = useState("");
  const [priority, setPriority] = useState("");
  const [couriers, setCouriers] = useState<CourierOption[]>([]);
  const [rows, setRows] = useState<DashboardReportRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async (filters?: {
    start: string;
    end: string;
    query: string;
    status: string;
    courierId: string;
    priority: string;
  }) => {
    const current = filters ?? {
      start: DEFAULT_REPORT_START,
      end: DEFAULT_REPORT_END,
      query: "",
      status: "",
      courierId: "",
      priority: "",
    };
    if (!current.start || !current.end || current.start > current.end) {
      setError("Informe um período válido: a data inicial não pode ser posterior à final.");
      return;
    }
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ start: current.start, end: current.end });
    if (current.query.trim()) params.set("q", current.query.trim());
    if (current.status) params.set("status", current.status);
    if (current.courierId) params.set("courier_id", current.courierId);
    if (current.priority) params.set("priority", current.priority);
    try {
      setRows(await api<DashboardReportRow[]>(`/dashboard/report?${params}`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    api<CourierOption[]>("/couriers").then(setCouriers, () => setCouriers([]));
  }, [load]);

  const totals = useMemo(() => ({
    orders: rows.length,
    weight: rows.reduce((sum, row) => sum + row.weight_kg, 0),
    routed: rows.filter((row) => row.route_id != null).length,
    delivered: rows.filter((row) => row.status === "DELIVERED").length,
  }), [rows]);

  function currentFilters() {
    return { start, end, query, status, courierId, priority };
  }

  function clearFilters() {
    setStart(DEFAULT_REPORT_START);
    setEnd(DEFAULT_REPORT_END);
    setQuery("");
    setStatus("");
    setCourierId("");
    setPriority("");
    void load();
  }

  return (
    <section className="page reports-page">
      <Breadcrumbs items={[{ label: "Relatórios" }]} />
      <div className="page-head">
        <div>
          <h1>Relatórios</h1>
          <p className="muted">Consulte pedidos integrados a clientes, entregadores e rotas e exporte exatamente o resultado filtrado.</p>
        </div>
        <button
          type="button"
          className="button report-button"
          disabled={loading || rows.length === 0}
          onClick={() => {
            downloadOperationalReport(rows, start, end);
            notify(`Relatório exportado com ${rows.length} ${rows.length === 1 ? "pedido" : "pedidos"}.`);
          }}
        >
          Exportar CSV
        </button>
      </div>

      <form
        className="report-filters"
        onSubmit={(event) => {
          event.preventDefault();
          void load(currentFilters());
        }}
      >
        <label className="wide-filter">Pesquisa
          <input type="search" placeholder="Pedido, cliente, telefone, endereço ou entregador" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label>Data inicial<input type="date" value={start} max={end} onChange={(event) => setStart(event.target.value)} /></label>
        <label>Data final<input type="date" value={end} min={start} onChange={(event) => setEnd(event.target.value)} /></label>
        <label>Situação
          <select value={status} onChange={(event) => setStatus(event.target.value as OrderStatus | "")}>
            <option value="">Todas</option>
            {STATUSES.map((value) => <option key={value} value={value}>{STATUS_LABELS[value]}</option>)}
          </select>
        </label>
        <label>Entregador
          <select value={courierId} onChange={(event) => setCourierId(event.target.value)}>
            <option value="">Todos</option>
            {couriers.map((courier) => <option key={courier.id} value={courier.id}>{courier.full_name}</option>)}
          </select>
        </label>
        <label>Prioridade
          <select value={priority} onChange={(event) => setPriority(event.target.value)}>
            <option value="">Todas</option>
            {[1, 2, 3].map((value) => <option key={value} value={value}>{PRIORITY_LABELS[value]}</option>)}
          </select>
        </label>
        <div className="filter-actions">
          <button className="button primary" type="submit" disabled={loading}>{loading ? "Consultando…" : "Aplicar filtros"}</button>
          <button className="button quiet" type="button" onClick={clearFilters}>Limpar</button>
        </div>
      </form>

      {error && <div className="alert error" role="alert">{error}</div>}

      <div className="report-summary" aria-label="Resumo do relatório">
        <div><span>Pedidos encontrados</span><strong>{totals.orders}</strong></div>
        <div><span>Peso total</span><strong>{formatKg(totals.weight)}</strong></div>
        <div><span>Com rota</span><strong>{totals.routed}</strong></div>
        <div><span>Entregues</span><strong>{totals.delivered}</strong></div>
      </div>

      {!loading && rows.length === 0 ? (
        <div className="empty"><p>Nenhum pedido corresponde aos critérios informados.</p><button className="button quiet" type="button" onClick={clearFilters}>Limpar filtros</button></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Pedido</th><th>Cliente</th><th>Destino</th><th>Entregador</th><th>Prioridade</th><th>Situação</th><th>Rota</th><th>Cadastro</th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.order_id}>
                  <td className="num"><Link to={`/pedidos/${row.order_id}`}>#{row.order_id}</Link></td>
                  <td><strong>{row.customer_name}</strong><span className="sub">{formatKg(row.weight_kg)}</span></td>
                  <td>{row.delivery_address}</td>
                  <td>{row.courier_name ?? <span className="muted">Sem entregador</span>}</td>
                  <td><Priority value={row.priority} /></td>
                  <td><StatusBadge status={row.status} /></td>
                  <td>{row.route_id ? <span>#{row.route_id}<span className="sub">{row.route_status ? ROUTE_STATUS_LABELS[row.route_status] : ""}</span></span> : <span className="muted">Sem rota</span>}</td>
                  <td className="nowrap">{formatDateTime(row.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
