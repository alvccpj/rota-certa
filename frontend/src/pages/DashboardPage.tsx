import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import {
  api,
  type DashboardReportRow,
  type DashboardSummary,
  type OrderStatus,
} from "../api";
import { Priority, StatusBadge } from "../components/Badges";
import Breadcrumbs from "../components/Breadcrumbs";
import { useToast } from "../components/Toast";
import {
  MODE_LABELS,
  formatDateTime,
  formatKm,
  formatMs,
  formatRatio,
} from "../labels";
import {
  DEFAULT_REPORT_END,
  DEFAULT_REPORT_START,
  downloadOperationalReport,
} from "../reporting";
import { useUser } from "../session";

export default function DashboardPage() {
  const user = useUser();
  const notify = useToast();
  const navigate = useNavigate();
  const [start, setStart] = useState(DEFAULT_REPORT_START);
  const [end, setEnd] = useState(DEFAULT_REPORT_END);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (from: string, to: string) => {
    if (!from || !to || from > to) {
      setError("Informe um período válido: a data inicial não pode ser posterior à final.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ start: from, end: to });
      setSummary(await api<DashboardSummary>(`/dashboard/summary?${params}`));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(DEFAULT_REPORT_START, DEFAULT_REPORT_END);
  }, [load]);

  const alerts = useMemo(() => {
    if (!summary) return [];
    const items: { tone: string; title: string; detail: string; to: string }[] = [];
    if (summary.orders.pending) {
      items.push({
        tone: "warning",
        title: `${summary.orders.pending} ${summary.orders.pending === 1 ? "pedido aguarda" : "pedidos aguardam"} atribuição`,
        detail: "Associe um entregador para que os pedidos possam entrar no planejamento.",
        to: "/pedidos?situacao=PENDING",
      });
    }
    if (summary.couriers.offline) {
      items.push({
        tone: "danger",
        title: `${summary.couriers.offline} ${summary.couriers.offline === 1 ? "entregador está" : "entregadores estão"} fora de serviço`,
        detail: "Confira a disponibilidade antes de gerar novas rotas.",
        to: "/usuarios",
      });
    }
    if (!summary.routes.total && summary.orders.assigned) {
      items.push({
        tone: "info",
        title: "Há pedidos atribuídos sem rotas no período",
        detail: "Abra o planejamento para calcular os trajetos dos entregadores.",
        to: "/rotas",
      });
    }
    return items;
  }, [summary]);

  async function exportCsv() {
    setExporting(true);
    try {
      const params = new URLSearchParams({ start, end });
      const rows = await api<DashboardReportRow[]>(`/dashboard/report?${params}`);
      downloadOperationalReport(rows, start, end);
      notify(`Relatório exportado com ${rows.length} ${rows.length === 1 ? "pedido" : "pedidos"}.`);
    } catch (err) {
      notify((err as Error).message, "error");
    } finally {
      setExporting(false);
    }
  }

  const statusRows: { status: OrderStatus; count: number }[] = summary
    ? [
        { status: "PENDING", count: summary.orders.pending },
        { status: "ASSIGNED", count: summary.orders.assigned },
        { status: "IN_ROUTE", count: summary.orders.in_route },
        { status: "DELIVERED", count: summary.orders.delivered },
        { status: "CANCELLED", count: summary.orders.cancelled },
      ]
    : [];

  return (
    <section className="page dashboard-page">
      <Breadcrumbs items={[{ label: "Visão geral" }]} />
      <div className="page-head dashboard-heading">
        <div>
          <p className="eyebrow">Operação integrada</p>
          <h1>Olá, {user.full_name.split(" ")[0]}</h1>
          <p className="muted">Pedidos, entregadores, rotas e desempenho reunidos em uma única visão.</p>
        </div>
        <div className="actions quick-actions">
          <Link className="button primary" to="/pedidos/novo">Novo pedido</Link>
          <Link className="button quiet" to="/rotas">Planejar rotas</Link>
          <Link className="button quiet" to="/relatorios">Consultar relatórios</Link>
          {user.role === "ADMIN" && <Link className="button quiet" to="/desempenho">Ver desempenho</Link>}
        </div>
      </div>

      <form
        className="dashboard-filters"
        onSubmit={(event) => {
          event.preventDefault();
          void load(start, end);
        }}
      >
        <label>
          Data inicial
          <input type="date" value={start} max={end} onChange={(event) => setStart(event.target.value)} />
        </label>
        <label>
          Data final
          <input type="date" value={end} min={start} onChange={(event) => setEnd(event.target.value)} />
        </label>
        <button className="button quiet" type="submit" disabled={loading}>Atualizar painel</button>
        <button className="button report-button" type="button" disabled={loading || exporting || !summary} onClick={exportCsv}>
          {exporting ? "Preparando…" : "Exportar relatório CSV"}
        </button>
        {summary && <span className="dashboard-updated">Atualizado em {formatDateTime(summary.generated_at)}</span>}
      </form>

      {error && <div className="alert error" role="alert">{error}</div>}
      {loading && <div className="dashboard-loading" role="status">Carregando indicadores integrados…</div>}

      {!loading && summary && (
        <>
          <div className="dashboard-stats" aria-label="Indicadores do período">
            <article className="dashboard-stat primary-stat">
              <span>Pedidos no período</span>
              <strong>{summary.orders.total}</strong>
              <small>{summary.orders.pending + summary.orders.assigned} aguardando saída</small>
            </article>
            <article className="dashboard-stat">
              <span>Entregues</span>
              <strong>{summary.orders.delivered}</strong>
              <small>{formatRatio(summary.orders.completion_rate, 1)}% dos pedidos do período</small>
            </article>
            <article className="dashboard-stat">
              <span>Rotas</span>
              <strong>{summary.routes.total}</strong>
              <small>{summary.routes.completed} concluídas · {summary.routes.in_progress} em andamento</small>
            </article>
            <article className="dashboard-stat">
              <span>Distância planejada</span>
              <strong>{formatKm(summary.routes.total_distance_km)}</strong>
              <small>Somente rotas não canceladas</small>
            </article>
            <article className="dashboard-stat">
              <span>Entregadores disponíveis</span>
              <strong>{summary.couriers.available}/{summary.couriers.total}</strong>
              <small>{summary.couriers.busy} ocupados · {summary.couriers.offline} fora de serviço</small>
            </article>
            <article className="dashboard-stat">
              <span>Execuções do otimizador</span>
              <strong>{summary.performance.run_count}</strong>
              <small>
                {summary.performance.average_execution_time_ms == null
                  ? "Nenhuma execução no período"
                  : `Média de ${formatMs(summary.performance.average_execution_time_ms)}`}
              </small>
            </article>
          </div>

          <div className="dashboard-grid">
            <article className="dashboard-card status-overview">
              <div className="card-heading">
                <div>
                  <h2>Fluxo dos pedidos</h2>
                  <p className="muted">Distribuição por situação no período selecionado.</p>
                </div>
                <Link to="/pedidos">Ver pedidos</Link>
              </div>
              <div className="status-bars">
                {statusRows.map(({ status, count }) => (
                  <div className="status-bar-row" key={status}>
                    <StatusBadge status={status} />
                    <div className="status-bar-track" aria-hidden="true">
                      <span className={`status-bar-fill fill-${status.toLowerCase()}`} style={{ width: `${summary.orders.total ? Math.max((count / summary.orders.total) * 100, count ? 3 : 0) : 0}%` }} />
                    </div>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="dashboard-card integration-card">
              <div className="card-heading">
                <div>
                  <h2>Integração operacional</h2>
                  <p className="muted">O mesmo dado acompanha toda a jornada da entrega.</p>
                </div>
              </div>
              <ol className="integration-flow">
                <li><span>1</span><div><strong>Pedidos</strong><small>{summary.orders.total} cadastrados no período</small></div></li>
                <li><span>2</span><div><strong>Roteirização</strong><small>{summary.routes.total} rotas · {formatKm(summary.routes.total_distance_km)}</small></div></li>
                <li><span>3</span><div><strong>Entrega</strong><small>{summary.orders.delivered} confirmações registradas</small></div></li>
                <li><span>4</span><div><strong>Desempenho</strong><small>{summary.performance.best_speedup == null ? "Sem comparação no período" : `Melhor speedup: ${formatRatio(summary.performance.best_speedup)}×`}</small></div></li>
              </ol>
              {summary.performance.latest_mode && (
                <p className="latest-run">
                  Última execução: <strong>{MODE_LABELS[summary.performance.latest_mode]}</strong>
                  {summary.performance.latest_executed_at && ` · ${formatDateTime(summary.performance.latest_executed_at)}`}
                </p>
              )}
              <div className="integration-links">
                <Link to="/relatorios">Pesquisar e exportar dados</Link>
                <Link to="/historico">Consultar histórico operacional</Link>
              </div>
            </article>
          </div>

          <section className="dashboard-section">
            <div className="card-heading">
              <div>
                <h2>Atenção operacional</h2>
                <p className="muted">Pendências detectadas automaticamente a partir dos dados atuais.</p>
              </div>
            </div>
            {alerts.length ? (
              <div className="operational-alerts">
                {alerts.map((item) => (
                  <Link className={`operational-alert ${item.tone}`} to={item.to} key={item.title}>
                    <span className="alert-dot" aria-hidden="true" />
                    <span><strong>{item.title}</strong><small>{item.detail}</small></span>
                    <span aria-hidden="true">→</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="all-clear"><strong>Operação sem alertas no período.</strong><span>Não há pendências que exijam ação imediata.</span></div>
            )}
          </section>

          <section className="dashboard-section recent-section">
            <div className="card-heading">
              <div>
                <h2>Pedidos recentes</h2>
                <p className="muted">Últimos registros dentro do período selecionado.</p>
              </div>
              <Link to="/pedidos">Abrir lista completa</Link>
            </div>
            {summary.recent_orders.length ? (
              <div className="table-wrap">
                <table className="clickable">
                  <thead><tr><th>Pedido</th><th>Cliente</th><th>Destino</th><th>Prioridade</th><th>Entregador</th><th>Situação</th></tr></thead>
                  <tbody>
                    {summary.recent_orders.map((order) => (
                      <tr key={order.id} onClick={() => navigate(`/pedidos/${order.id}`)}>
                        <td className="num"><Link to={`/pedidos/${order.id}`} onClick={(event) => event.stopPropagation()}>#{order.id}</Link></td>
                        <td><strong>{order.customer_name}</strong><span className="sub">{formatDateTime(order.created_at)}</span></td>
                        <td>{order.delivery_address}</td>
                        <td><Priority value={order.priority} /></td>
                        <td>{order.courier_name ?? <span className="muted">Sem entregador</span>}</td>
                        <td><StatusBadge status={order.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty"><p>Nenhum pedido foi cadastrado no período selecionado.</p><Link className="button primary" to="/pedidos/novo">Cadastrar pedido</Link></div>
            )}
          </section>
        </>
      )}
    </section>
  );
}
