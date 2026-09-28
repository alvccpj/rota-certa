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

export interface OrderInput {
  customer_name: string;
  customer_phone: string | null;
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
    throw new ApiError(0, `A API não respondeu em ${API_URL}. Verifique se o backend está rodando.`);
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && token) onUnauthorized();
    throw new ApiError(response.status, errorMessage(data));
  }
  return data as T;
}

const FIELD_LABELS: Record<string, string> = {
  email: "E-mail",
  password: "Senha",
  full_name: "Nome",
  establishment_name: "Nome do negócio",
  depot_address: "Endereço de saída",
  customer_name: "Cliente",
  customer_phone: "Telefone",
  delivery_address: "Endereço de entrega",
  latitude: "Latitude",
  longitude: "Longitude",
  weight_kg: "Peso",
  load_capacity_kg: "Capacidade de carga",
};

interface ValidationIssue {
  type: string;
  loc: (string | number)[];
  msg: string;
  ctx?: Record<string, unknown>;
}

function errorMessage(data: unknown): string {
  const detail = (data as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return (detail as ValidationIssue[]).map(describeIssue).join(" ");
  return "Não foi possível concluir a operação.";
}

function describeIssue(issue: ValidationIssue): string {
  const field = String(issue.loc[issue.loc.length - 1]);
  const label = FIELD_LABELS[field];
  if (issue.type === "value_error" && !label) return issue.msg.replace(/^Value error, /, "");
  const name = label ?? "Campo";
  switch (issue.type) {
    case "missing":
      return `${name}: preenchimento obrigatório.`;
    case "string_too_short":
      return `${name}: use pelo menos ${issue.ctx?.min_length} caracteres.`;
    case "string_too_long":
      return `${name}: use no máximo ${issue.ctx?.max_length} caracteres.`;
    case "greater_than":
      return `${name}: informe um valor maior que ${issue.ctx?.gt}.`;
    case "value_error":
      return `${name}: valor inválido.`;
    default:
      return `${name}: verifique o valor informado.`;
  }
}
