export type Role = "ADMIN" | "ATTENDANT" | "COURIER";
export type Availability = "AVAILABLE" | "BUSY" | "OFFLINE";
export type OrderStatus = "PENDING" | "ASSIGNED" | "IN_ROUTE" | "DELIVERED" | "CANCELLED";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: Role;
  active: boolean;
  created_at: string;
  establishment: { id: number; name: string };
  courier: { id: number; load_capacity_kg: number; availability: Availability } | null;
}

export interface Session {
  access_token: string;
  user: User;
}

export interface CourierOption {
  id: number;
  full_name: string;
  availability: Availability;
  load_capacity_kg: number;
  active_load_kg: number;
  active_orders: number;
}

export interface Customer {
  id: number;
  full_name: string;
  phone: string | null;
  order_count: number;
  last_address: string | null;
  last_latitude: number | null;
  last_longitude: number | null;
  created_at: string;
}

export interface HistoryEvent {
  status: OrderStatus;
  note: string | null;
  changed_by: string | null;
  changed_at: string;
}

export interface GeocodeResult {
  label: string;
  latitude: number;
  longitude: number;
}

export interface Order {
  id: number;
  customer: { id: number; full_name: string; phone: string | null };
  delivery_address: string;
  latitude: number;
  longitude: number;
  weight_kg: number;
  priority: number;
  desired_start: string | null;
  desired_end: string | null;
  status: OrderStatus;
  assigned_courier: { id: number; full_name: string } | null;
  created_at: string;
}

export interface OrderDetail extends Order {
  history: HistoryEvent[];
}

export interface OrderInput {
  customer_id: number;
  delivery_address: string;
  latitude: number;
  longitude: number;
  weight_kg: number;
  priority: number;
  desired_start: string | null;
  desired_end: string | null;
  assigned_courier_id: number | null;
}

export const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    /** Mensagens de validação por campo, com os nomes usados pela API. */
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}

let token: string | null = null;
let onUnauthorized: () => void = () => {};

export function configureApi(nextToken: string | null, handleUnauthorized: () => void) {
  token = nextToken;
  onUnauthorized = handleUnauthorized;
}

export async function api<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: init.method ?? "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: init.body === undefined ? undefined : JSON.stringify(init.body),
    });
  } catch {
    throw new ApiError(
      0,
      "Não foi possível falar com o servidor. Verifique a conexão ou se a API está rodando e tente de novo.",
    );
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized();
    throw toApiError(response.status, data);
  }
  return data as T;
}

interface ValidationIssue {
  type: string;
  loc: (string | number)[];
  msg: string;
  ctx?: Record<string, unknown>;
}

function toApiError(status: number, data: unknown): ApiError {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return new ApiError(status, detail);
  if (Array.isArray(detail)) {
    const fields: Record<string, string> = {};
    const general: string[] = [];
    for (const issue of detail as ValidationIssue[]) {
      const field = issue.loc.length > 1 ? String(issue.loc[issue.loc.length - 1]) : null;
      const message = describeIssue(issue);
      if (field && field !== "body") fields[field] ??= message;
      else general.push(message);
    }
    const count = Object.keys(fields).length;
    const summary =
      general.join(" ") ||
      (count === 1 ? "Corrija o campo destacado." : `Corrija os ${count} campos destacados.`);
    return new ApiError(status, summary, fields);
  }
  if (status >= 500) return new ApiError(status, "O servidor encontrou um erro inesperado. Tente de novo em instantes.");
  return new ApiError(status, "Não foi possível concluir a operação.");
}

/** Traduz os erros de validação da API para mensagens exibidas junto ao campo. */
function describeIssue(issue: ValidationIssue): string {
  const ctx = issue.ctx ?? {};
  switch (issue.type) {
    case "missing":
      return "Preencha este campo.";
    case "string_too_short":
      return `Use pelo menos ${ctx.min_length} caracteres.`;
    case "string_too_long":
      return `Use no máximo ${ctx.max_length} caracteres.`;
    case "greater_than":
      return `Informe um valor maior que ${ctx.gt}.`;
    case "greater_than_equal":
      return `O valor mínimo é ${ctx.ge}.`;
    case "less_than_equal":
      return `O valor máximo é ${ctx.le}.`;
    case "int_parsing":
    case "int_type":
    case "float_parsing":
    case "float_type":
      return "Informe um número.";
    case "literal_error":
      return "Escolha uma das opções.";
    case "value_error":
      if (/email/i.test(issue.msg)) return "Informe um e-mail válido, como nome@empresa.com.br.";
      return issue.msg.replace(/^Value error, /, "");
    default:
      return "Confira o valor informado.";
  }
}
