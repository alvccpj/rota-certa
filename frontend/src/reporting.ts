import type { DashboardReportRow } from "./api";
import { PRIORITY_LABELS, ROUTE_STATUS_LABELS, STATUS_LABELS, formatDateTime } from "./labels";

export function localDate(daysAgo = 0): string {
  const value = new Date();
  value.setDate(value.getDate() - daysAgo);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export const DEFAULT_REPORT_START = localDate(6);
export const DEFAULT_REPORT_END = localDate();

function csvCell(value: string | number | null): string {
  const text = value == null ? "" : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

export function downloadOperationalReport(rows: DashboardReportRow[], start: string, end: string) {
  const headings = [
    "Pedido",
    "Cliente",
    "Entregador",
    "Endereço",
    "Situação",
    "Prioridade",
    "Peso (kg)",
    "Cadastrado em",
    "Rota",
    "Situação da rota",
    "Data da rota",
  ];
  const lines = rows.map((row) => [
    row.order_id,
    row.customer_name,
    row.courier_name,
    row.delivery_address,
    STATUS_LABELS[row.status],
    PRIORITY_LABELS[row.priority],
    row.weight_kg.toLocaleString("pt-BR", { maximumFractionDigits: 2 }),
    formatDateTime(row.created_at),
    row.route_id,
    row.route_status ? ROUTE_STATUS_LABELS[row.route_status] : null,
    row.route_date,
  ]);
  const csv = [headings, ...lines].map((line) => line.map(csvCell).join(";")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `rota-certa-relatorio-${start}-a-${end}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
