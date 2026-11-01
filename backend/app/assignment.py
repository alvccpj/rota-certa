"""Atribuição automática de pedidos pendentes, em uma única transação."""

from decimal import Decimal

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, contains_eager, lazyload

from app.models import Courier, Establishment, Order, OrderStatusEvent, Route, User
from app.rules import active_loads, ensure_window_not_past, ensure_within_radius
from app.security import COURIER


class AssignedOrderOut(BaseModel):
    order_id: int
    courier_id: int
    courier_name: str


class SkippedOrderOut(BaseModel):
    order_id: int
    reason: str


class AutoAssignOut(BaseModel):
    assigned: list[AssignedOrderOut] = Field(default_factory=list)
    skipped: list[SkippedOrderOut] = Field(default_factory=list)


def auto_assign_orders(db: Session, actor: User) -> AutoAssignOut:
    """Ordena por prioridade, prazo (nulos por último) e ID; escolhe menor kg/ID.

    Entregadores com rota IN_PROGRESS ou qualquer pedido IN_ROUTE estão ocupados,
    mesmo que o pedido em rota ainda não tenha um registro na tabela de rotas.

    O bloqueio do estabelecimento serializa chamadas desta operação no
    PostgreSQL até o commit, inclusive quando ainda não há pedidos pendentes.
    SQLite executa as mesmas regras, mas não oferece essa garantia de bloqueio.
    """

    postgres = db.get_bind().dialect.name == "postgresql"
    establishment_query = select(Establishment).where(Establishment.id == actor.establishment_id)
    if postgres:
        establishment_query = establishment_query.with_for_update(of=Establishment)
    establishment = db.scalar(establishment_query.execution_options(populate_existing=True))
    if establishment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Estabelecimento não encontrado.")

    # Só consultar a fila e as cargas depois de adquirir o bloqueio acima.
    pending_query = (
        select(Order)
        .options(lazyload("*"))
        .where(
            Order.establishment_id == establishment.id,
            Order.status == "PENDING",
            Order.assigned_courier_id.is_(None),
        )
        .order_by(Order.priority.asc(), Order.desired_end.asc().nulls_last(), Order.id.asc())
    )
    if postgres:
        pending_query = pending_query.with_for_update(of=Order)
    pending = list(db.scalars(pending_query.execution_options(populate_existing=True)))
    result = AutoAssignOut()
    if not pending:
        db.commit()
        return result

    if establishment.depot_latitude is None or establishment.depot_longitude is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Marque no mapa o ponto de saída das entregas antes da atribuição automática.",
        )

    in_progress = exists().where(
        Route.establishment_id == establishment.id,
        Route.courier_id == Courier.id,
        Route.status == "IN_PROGRESS",
    )
    in_route = exists().where(
        Order.establishment_id == establishment.id,
        Order.assigned_courier_id == Courier.id,
        Order.status == "IN_ROUTE",
    )
    courier_query = (
        select(Courier)
        .join(Courier.user)
        .options(contains_eager(Courier.user))
        .where(
            Courier.establishment_id == establishment.id,
            User.establishment_id == establishment.id,
            User.role == COURIER,
            User.active.is_(True),
            Courier.availability == "AVAILABLE",
            ~in_progress,
            ~in_route,
        )
        .order_by(Courier.id)
    )
    if postgres:
        courier_query = courier_query.with_for_update(of=Courier)
    couriers = list(db.scalars(courier_query.execution_options(populate_existing=True)))
    current_loads = active_loads(db, [courier.id for courier in couriers])
    loads = {courier.id: current_loads.get(courier.id, (Decimal("0"), 0))[0] for courier in couriers}

    for order in pending:
        try:
            ensure_window_not_past(order.desired_end)
            ensure_within_radius(establishment, float(order.latitude), float(order.longitude))
        except HTTPException as exc:
            result.skipped.append(SkippedOrderOut(order_id=order.id, reason=str(exc.detail)))
            continue

        if not couriers:
            result.skipped.append(SkippedOrderOut(
                order_id=order.id,
                reason="Nenhum entregador ativo e disponível sem rota em andamento ou pedido em rota.",
            ))
            continue

        candidates = [
            courier for courier in couriers
            if loads[courier.id] + order.weight_kg <= courier.load_capacity_kg
        ]
        if not candidates:
            result.skipped.append(SkippedOrderOut(
                order_id=order.id,
                reason="Nenhum entregador elegível possui capacidade de carga restante para este pedido.",
            ))
            continue

        courier = min(candidates, key=lambda candidate: (loads[candidate.id], candidate.id))
        order.courier = courier
        order.status = "ASSIGNED"
        db.add(OrderStatusEvent(
            order=order,
            status="ASSIGNED",
            note=f"Atribuído automaticamente a {courier.user.full_name}",
            changed_by=actor.id,
        ))
        # A sessão não faz autoflush: incluir a carga do lote antes do próximo pedido.
        loads[courier.id] += order.weight_kg
        result.assigned.append(AssignedOrderOut(
            order_id=order.id,
            courier_id=courier.id,
            courier_name=courier.user.full_name,
        ))

    db.commit()
    return result
