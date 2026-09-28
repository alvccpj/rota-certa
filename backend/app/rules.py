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
