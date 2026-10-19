"""Consultas integradas do painel, relatórios e histórico operacional."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import Courier, Customer, OptimizationRun, Order, OrderStatusEvent, Route, RouteStop, User
from app.schemas import (
    DashboardCourierCountsOut,
    DashboardOrderCountsOut,
    DashboardPerformanceOut,
    DashboardPeriodOut,
    DashboardRecentOrderOut,
    DashboardReportRowOut,
    DashboardRouteCountsOut,
    DashboardSummaryOut,
    OperationalEventType,
    OperationalHistoryEventOut,
    OrderStatus,
)

MAX_PERIOD_DAYS = 366
ORDER_STATUSES = ("PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED")
ROUTE_STATUSES = ("PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED")
COURIER_STATUSES = ("AVAILABLE", "BUSY", "OFFLINE")


@dataclass(frozen=True)
class Period:
    start: date
    end: date
    start_at: datetime
    end_at: datetime


def resolve_period(start: date | None, end: date | None) -> Period:
    """Normaliza o período inclusivo e limita consultas excessivamente amplas."""

    end_date = end or date.today()
    start_date = start or end_date - timedelta(days=6)
    if end_date < start_date:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A data final deve ser igual ou posterior à inicial.")
    if (end_date - start_date).days >= MAX_PERIOD_DAYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Consulte no máximo 366 dias por vez.")
    return Period(
        start=start_date,
        end=end_date,
        start_at=datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        end_at=datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc),
    )


def _counts(rows: list[tuple[str, int]], keys: tuple[str, ...]) -> dict[str, int]:
    values = {key: 0 for key in keys}
    for key, count in rows:
        if key in values:
            values[key] = count
    return values


def dashboard_summary(db: Session, user: User, period: Period) -> DashboardSummaryOut:
    establishment_id = user.establishment_id
    order_rows = db.execute(
        select(Order.status, func.count(Order.id))
        .where(
            Order.establishment_id == establishment_id,
            Order.created_at >= period.start_at,
            Order.created_at < period.end_at,
        )
        .group_by(Order.status)
    ).all()
    order_counts = _counts(order_rows, ORDER_STATUSES)
    order_total = sum(order_counts.values())

    courier_rows = db.execute(
        select(Courier.availability, func.count(Courier.id))
        .join(User, User.id == Courier.user_id)
        .where(Courier.establishment_id == establishment_id, User.active.is_(True))
        .group_by(Courier.availability)
    ).all()
    courier_counts = _counts(courier_rows, COURIER_STATUSES)

    route_rows = db.execute(
        select(Route.status, func.count(Route.id))
        .where(
            Route.establishment_id == establishment_id,
            Route.route_date >= period.start,
            Route.route_date <= period.end,
        )
        .group_by(Route.status)
    ).all()
    route_counts = _counts(route_rows, ROUTE_STATUSES)
    route_total = sum(route_counts.values())
    total_distance = db.scalar(
        select(func.coalesce(func.sum(Route.total_distance_km), 0)).where(
            Route.establishment_id == establishment_id,
            Route.route_date >= period.start,
            Route.route_date <= period.end,
            Route.status != "CANCELLED",
        )
    )

    run_filter = (
        OptimizationRun.establishment_id == establishment_id,
        OptimizationRun.executed_at >= period.start_at,
        OptimizationRun.executed_at < period.end_at,
    )
    run_count, average_time, best_speedup = db.execute(
        select(
            func.count(OptimizationRun.id),
            func.avg(OptimizationRun.execution_time_ms),
            func.max(OptimizationRun.speedup),
        ).where(*run_filter)
    ).one()
    latest_run = db.scalar(
        select(OptimizationRun).where(*run_filter).order_by(OptimizationRun.executed_at.desc(), OptimizationRun.id.desc())
    )

    recent = db.scalars(
        select(Order)
        .where(
            Order.establishment_id == establishment_id,
            Order.created_at >= period.start_at,
            Order.created_at < period.end_at,
        )
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(8)
    ).unique()

    return DashboardSummaryOut(
        generated_at=datetime.now(timezone.utc),
        period=DashboardPeriodOut(start=period.start, end=period.end),
        orders=DashboardOrderCountsOut(
            total=order_total,
            pending=order_counts["PENDING"],
            assigned=order_counts["ASSIGNED"],
            in_route=order_counts["IN_ROUTE"],
            delivered=order_counts["DELIVERED"],
            cancelled=order_counts["CANCELLED"],
            completion_rate=round(order_counts["DELIVERED"] * 100 / order_total, 1) if order_total else 0,
        ),
        couriers=DashboardCourierCountsOut(
            total=sum(courier_counts.values()),
            available=courier_counts["AVAILABLE"],
            busy=courier_counts["BUSY"],
            offline=courier_counts["OFFLINE"],
        ),
        routes=DashboardRouteCountsOut(
            total=route_total,
            planned=route_counts["PLANNED"],
            in_progress=route_counts["IN_PROGRESS"],
            completed=route_counts["COMPLETED"],
            cancelled=route_counts["CANCELLED"],
            total_distance_km=float(total_distance or 0),
        ),
        performance=DashboardPerformanceOut(
            run_count=run_count,
            average_execution_time_ms=round(float(average_time), 3) if average_time is not None else None,
            best_speedup=round(float(best_speedup), 3) if best_speedup is not None else None,
            latest_mode=latest_run.execution_mode if latest_run else None,
            latest_executed_at=latest_run.executed_at if latest_run else None,
        ),
        recent_orders=[
            DashboardRecentOrderOut(
                id=order.id,
                customer_name=order.customer.full_name,
                courier_name=order.courier.user.full_name if order.courier else None,
                delivery_address=order.delivery_address,
                status=order.status,
                priority=order.priority,
                created_at=order.created_at,
            )
            for order in recent
        ],
    )


def operational_report(
    db: Session,
    user: User,
    period: Period,
    status_filter: OrderStatus | None = None,
    query_text: str | None = None,
    courier_id: int | None = None,
    priority: int | None = None,
) -> list[DashboardReportRowOut]:
    query = (
        select(
            Order.id,
            Customer.full_name,
            User.full_name,
            Order.delivery_address,
            Order.status,
            Order.priority,
            Order.weight_kg,
            Order.created_at,
            Route.id,
            Route.status,
            Route.route_date,
        )
        .join(Customer, Customer.id == Order.customer_id)
        .outerjoin(Courier, Courier.id == Order.assigned_courier_id)
        .outerjoin(User, User.id == Courier.user_id)
        .outerjoin(RouteStop, RouteStop.order_id == Order.id)
        .outerjoin(Route, Route.id == RouteStop.route_id)
        .where(
            Order.establishment_id == user.establishment_id,
            Order.created_at >= period.start_at,
            Order.created_at < period.end_at,
        )
    )
    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    if courier_id is not None:
        query = query.where(Order.assigned_courier_id == courier_id)
    if priority is not None:
        query = query.where(Order.priority == priority)
    if query_text:
        pattern = f"%{query_text.strip()}%"
        text_conditions = (
            Customer.full_name.ilike(pattern),
            Customer.phone.ilike(pattern),
            Order.delivery_address.ilike(pattern),
            User.full_name.ilike(pattern),
        )
        if query_text.strip().isdigit():
            query = query.where(or_(*text_conditions, Order.id == int(query_text.strip())))
        else:
            query = query.where(or_(*text_conditions))

    query = query.order_by(Order.created_at.desc(), Order.id.desc()).limit(2000)

    return [
        DashboardReportRowOut(
            order_id=row[0],
            customer_name=row[1],
            courier_name=row[2],
            delivery_address=row[3],
            status=row[4],
            priority=row[5],
            weight_kg=float(row[6]),
            created_at=row[7],
            route_id=row[8],
            route_status=row[9],
            route_date=row[10],
        )
        for row in db.execute(query).all()
    ]


def operational_history(
    db: Session,
    user: User,
    period: Period,
    event_type: OperationalEventType | None = None,
    status_filter: OrderStatus | None = None,
    query_text: str | None = None,
) -> list[OperationalHistoryEventOut]:
    """Reúne mudanças de pedidos e execuções do otimizador em uma linha do tempo."""

    events: list[OperationalHistoryEventOut] = []
    if event_type in (None, "ORDER_STATUS"):
        order_query = (
            select(OrderStatusEvent, Order, Customer, User)
            .join(Order, Order.id == OrderStatusEvent.order_id)
            .join(Customer, Customer.id == Order.customer_id)
            .outerjoin(User, User.id == OrderStatusEvent.changed_by)
            .where(
                Order.establishment_id == user.establishment_id,
                OrderStatusEvent.changed_at >= period.start_at,
                OrderStatusEvent.changed_at < period.end_at,
            )
        )
        if status_filter is not None:
            order_query = order_query.where(OrderStatusEvent.status == status_filter)
        if query_text:
            pattern = f"%{query_text.strip()}%"
            conditions = (
                Customer.full_name.ilike(pattern),
                Customer.phone.ilike(pattern),
                Order.delivery_address.ilike(pattern),
                OrderStatusEvent.note.ilike(pattern),
                User.full_name.ilike(pattern),
                cast(Order.id, String).ilike(pattern),
            )
            order_query = order_query.where(or_(*conditions))
        order_query = order_query.order_by(OrderStatusEvent.changed_at.desc(), OrderStatusEvent.id.desc()).limit(500)
        for event, order, customer, author in db.execute(order_query).all():
            events.append(
                OperationalHistoryEventOut(
                    event_id=f"order-{event.id}",
                    event_type="ORDER_STATUS",
                    occurred_at=event.changed_at,
                    actor_name=author.full_name if author else None,
                    order_id=order.id,
                    customer_name=customer.full_name,
                    status=event.status,
                    note=event.note,
                    execution_mode=None,
                    execution_time_ms=None,
                    order_count=None,
                )
            )

    if event_type in (None, "OPTIMIZATION") and status_filter is None:
        run_query = select(OptimizationRun).where(
            OptimizationRun.establishment_id == user.establishment_id,
            OptimizationRun.executed_at >= period.start_at,
            OptimizationRun.executed_at < period.end_at,
        )
        if query_text:
            pattern = f"%{query_text.strip()}%"
            run_query = run_query.where(
                or_(
                    OptimizationRun.execution_mode.ilike(pattern),
                    OptimizationRun.algorithm.ilike(pattern),
                    OptimizationRun.purpose.ilike(pattern),
                    cast(OptimizationRun.order_count, String).ilike(pattern),
                )
            )
        run_query = run_query.order_by(OptimizationRun.executed_at.desc(), OptimizationRun.id.desc()).limit(500)
        for run in db.scalars(run_query):
            events.append(
                OperationalHistoryEventOut(
                    event_id=f"optimization-{run.id}",
                    event_type="OPTIMIZATION",
                    occurred_at=run.executed_at,
                    actor_name="Sistema",
                    order_id=None,
                    customer_name=None,
                    status=None,
                    note=run.purpose,
                    execution_mode=run.execution_mode,
                    execution_time_ms=float(run.execution_time_ms),
                    order_count=run.order_count,
                )
            )

    events.sort(key=lambda event: event.occurred_at, reverse=True)
    return events[:500]
