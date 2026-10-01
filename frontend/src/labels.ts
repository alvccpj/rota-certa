import type { Availability, ExecutionMode, OrderStatus, Role, RouteStatus } from "./api";

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Administrador",
  ATTENDANT: "Atendente",
  COURIER: "Entregador",
};

export const ROLE_PERMISSIONS: Record<Role, string> = {
  ADMIN: "Gerencia usuários e pedidos, inclusive exclusões.",
  ATTENDANT: "Cadastra, edita e acompanha pedidos.",
  COURIER: "Vê só as próprias entregas e atualiza o andamento.",
};

export const STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING: "Pendente",
  ASSIGNED: "Atribuído",
  IN_ROUTE: "Em rota",
  DELIVERED: "Entregue",
  CANCELLED: "Cancelado",
};

export const AVAILABILITY_LABELS: Record<Availability, string> = {
  AVAILABLE: "Disponível",
  BUSY: "Ocupado",
  OFFLINE: "Fora de serviço",
};

export const PRIORITY_LABELS: Record<number, string> = {
  1: "Alta",
  2: "Normal",
  3: "Baixa",
};

const dateTime = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});
const timeOnly = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

export function formatWindow(start: string | null, end: string | null): string {
  if (!start && !end) return "Sem horário";
  if (start && end) {
    const from = new Date(start);
    const to = new Date(end);
    const sameDay = from.toDateString() === to.toDateString();
    return `${dateTime.format(from)} até ${sameDay ? timeOnly.format(to) : dateTime.format(to)}`;
  }
  return start ? `A partir de ${dateTime.format(new Date(start))}` : `Até ${dateTime.format(new Date(end!))}`;
}

export function toInputDateTime(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function fromInputDateTime(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

export function formatKg(value: number): string {
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 2 })} kg`;
}

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export const STAFF_ROLES: Role[] = ["ADMIN", "ATTENDANT"];

export const ROUTE_STATUS_LABELS: Record<RouteStatus, string> = {
  PLANNED: "Planejada",
  IN_PROGRESS: "Em andamento",
  COMPLETED: "Concluída",
  CANCELLED: "Cancelada",
};

export const MODE_LABELS: Record<ExecutionMode, string> = {
  SEQUENTIAL: "Sequencial",
  PARALLEL: "Paralelo em CPU",
  GPU: "GPU (CUDA)",
};

/** Cores das rotas no mapa, atribuídas na ordem dos entregadores (paleta categórica validada). */
export const ROUTE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];

export function routeColor(index: number): string {
  return ROUTE_COLORS[index % ROUTE_COLORS.length];
}

export function formatKm(value: number | null): string {
  if (value == null) return "—";
  return `${value.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`;
}

export function formatDuration(minutes: number | null): string {
  if (minutes == null) return "—";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} h ${rest} min` : `${hours} h`;
}

export function formatTime(iso: string | null): string {
  return iso ? timeOnly.format(new Date(iso)) : "—";
}

export function formatMs(value: number): string {
  const digits = value < 10 ? 2 : value < 100 ? 1 : 0;
  return `${value.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits })} ms`;
}

export function formatRatio(value: number | null, digits = 2): string {
  if (value == null) return "—";
  return value.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}
