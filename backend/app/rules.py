"""Regras de negócio da atribuição de pedidos."""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Courier, Establishment, Order
from app.optimizer.routing import Stop, haversine_km

ACTIVE_STATUSES = ("ASSIGNED", "IN_ROUTE")


def ensure_courier_can_leave(db: Session, courier: Courier, *, removing_access: bool = False) -> None:
    """Evita deixar entregas sem um responsável que possa acessá-las."""
    statuses = ACTIVE_STATUSES if removing_access else ("IN_ROUTE",)
    ids = list(db.scalars(select(Order.id).where(
        Order.assigned_courier_id == courier.id, Order.status.in_(statuses)
    ).order_by(Order.id)))
    if ids:
        orders = ", ".join(f"#{order_id}" for order_id in ids)
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Resolva as entregas ativas antes de retirar o acesso ou colocar fora de serviço. Pedidos: {orders}.")


STAFF_TRANSITIONS = {
    "PENDING": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"PENDING", "IN_ROUTE", "CANCELLED"},
    "IN_ROUTE": {"DELIVERED", "CANCELLED"},
    "DELIVERED": {"PENDING"},
    "CANCELLED": {"PENDING"},
}


def allowed_statuses(current: str, *, courier: bool) -> list[str]:
    allowed = {"ASSIGNED": {"IN_ROUTE"}, "IN_ROUTE": {"DELIVERED"}} if courier else STAFF_TRANSITIONS
    return sorted(allowed.get(current, set()))


def ensure_status_transition(current: str, target: str, *, courier: bool) -> None:
    if target not in allowed_statuses(current, courier=courier):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Esta mudança de situação não é permitida. Atualize o pedido e siga a próxima etapa; pedidos encerrados precisam ser reabertos.")


def kg(value: Decimal | float) -> str:
    """Formata pesos no padrão brasileiro: 25, 3,7 ou 2,55."""

    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def active_loads(db: Session, courier_ids: list[int]) -> dict[int, tuple[Decimal, int]]:
    """Peso e quantidade de pedidos atribuídos ou em rota de cada entregador."""

    if not courier_ids:
        return {}
    rows = db.execute(
        select(Order.assigned_courier_id, func.coalesce(func.sum(Order.weight_kg), 0), func.count(Order.id))
        .where(Order.assigned_courier_id.in_(courier_ids), Order.status.in_(ACTIVE_STATUSES))
        .group_by(Order.assigned_courier_id)
    )
    return {courier_id: (Decimal(str(load)), count) for courier_id, load, count in rows}


def ensure_courier_can_take(db: Session, courier: Courier, order: Order, weight: Decimal) -> None:
    name = courier.user.full_name
    if courier.availability == "OFFLINE":
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{name} está fora de serviço e não pode receber pedidos.",
        )
    query = select(func.coalesce(func.sum(Order.weight_kg), 0)).where(
        Order.assigned_courier_id == courier.id,
        Order.status.in_(ACTIVE_STATUSES),
    )
    if order.id is not None:
        query = query.where(Order.id != order.id)
    total = Decimal(str(db.scalar(query))) + weight
    if total > courier.load_capacity_kg:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Com este pedido, {name} ficaria com {kg(total)} kg em entregas, acima da capacidade "
            f"de {kg(courier.load_capacity_kg)} kg. Escolha outro entregador ou divida o pedido.",
        )


def ensure_within_radius(establishment: Establishment, latitude: float, longitude: float) -> None:
    if establishment.depot_latitude is None or establishment.depot_longitude is None:
        return
    depot = Stop("depot", float(establishment.depot_latitude), float(establishment.depot_longitude))
    distance = haversine_km(depot, Stop("entrega", latitude, longitude))
    limit = settings.max_delivery_radius_km
    if distance > limit:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"O local de entrega fica a {kg(round(distance, 1))} km do ponto de saída. "
            f"O limite de entrega é {kg(limit)} km.",
        )


def ensure_window_not_past(desired_end: datetime | None) -> None:
    if desired_end is None:
        return
    end = desired_end if desired_end.tzinfo else desired_end.replace(tzinfo=timezone.utc)
    if end < datetime.now(timezone.utc):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "O horário final da entrega já passou. Informe um horário futuro.",
        )


def ensure_window_update_not_past(order: Order, desired_start: datetime | None, desired_end: datetime | None) -> None:
    """Valida uma nova janela; permite preservar a antiga ao corrigir pedidos atrasados."""

    def utc(value: datetime | None) -> datetime | None:
        # SQLite retorna datas sem fuso; a aplicação as interpreta como UTC.
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value

    if (utc(desired_start), utc(desired_end)) != (utc(order.desired_start), utc(order.desired_end)):
        ensure_window_not_past(desired_end)
