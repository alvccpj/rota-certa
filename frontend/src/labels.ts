import type { Availability, OrderStatus, Role } from "./api";

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
