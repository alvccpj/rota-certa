import type { OrderStatus } from "../api";
import { PRIORITY_LABELS, STATUS_LABELS } from "../labels";

export function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status status-${status.toLowerCase()}`}>{STATUS_LABELS[status]}</span>;
}

export function Priority({ value }: { value: number }) {
  return <span className={`priority priority-${value}`}>{PRIORITY_LABELS[value]}</span>;
}
