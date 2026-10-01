"""Regras de negócio do módulo de roteirização: gerar, iniciar e acompanhar rotas."""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from math import ceil
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Courier, Establishment, OptimizationRun, Order, OrderStatusEvent, Route, RouteStop, User, utc_now
from app.optimizer import gpu
from app.optimizer.routing import ALGORITHM, OptimizationResult, Stop, haversine_km, optimize_routes
from app.schemas import (
    AssignedCourierOut,
    DepotOut,
    MyRouteOut,
    OptimizationRunOut,
    RouteGenerationOut,
    RouteOut,
    RoutesOverviewOut,
    RouteStopOut,
    SkippedCourierOut,
)

LOCAL_TIMEZONE = timezone(timedelta(hours=settings.local_utc_offset_hours))
OPEN_ROUTE_STATUSES = ("PLANNED", "IN_PROGRESS")
FINISHED_STOP_STATUSES = ("COMPLETED", "FAILED")


def local_today() -> date:
    return datetime.now(LOCAL_TIMEZONE).date()


def money(value: float, places: int = 3) -> Decimal:
    return Decimal(f"{value:.{places}f}")


# Ponto de saída

def depot_out(establishment: Establishment) -> DepotOut:
    return DepotOut(
        address=establishment.depot_address,
        latitude=float(establishment.depot_latitude) if establishment.depot_latitude is not None else None,
        longitude=float(establishment.depot_longitude) if establishment.depot_longitude is not None else None,
    )


def require_depot(establishment: Establishment) -> Stop:
    if establishment.depot_latitude is None or establishment.depot_longitude is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Marque no mapa o ponto de saída das entregas antes de gerar as rotas.",
        )
    return Stop("depot", float(establishment.depot_latitude), float(establishment.depot_longitude))


# Conversão para a resposta da API

def courier_ref(courier: Courier) -> AssignedCourierOut:
    return AssignedCourierOut(id=courier.id, full_name=courier.user.full_name)


def route_out(route: Route) -> RouteOut:
    return RouteOut(
        id=route.id,
        courier=courier_ref(route.courier),
        route_date=route.route_date,
        status=route.status,
        algorithm=route.algorithm,
        execution_mode=route.execution_mode,
        total_distance_km=float(route.total_distance_km) if route.total_distance_km is not None else None,
        estimated_duration_min=route.estimated_duration_min,
        created_at=route.created_at,
        stops=[
            RouteStopOut(
                sequence=stop.stop_sequence,
                status=stop.status,
                order_id=stop.order.id,
                order_status=stop.order.status,
                customer_name=stop.order.customer.full_name,
                customer_phone=stop.order.customer.phone,
                delivery_address=stop.order.delivery_address,
                latitude=float(stop.order.latitude),
                longitude=float(stop.order.longitude),
                priority=stop.order.priority,
                weight_kg=float(stop.order.weight_kg),
                distance_from_previous_km=(
                    float(stop.distance_from_previous_km) if stop.distance_from_previous_km is not None else None
                ),
                estimated_arrival=stop.estimated_arrival,
            )
            for stop in route.stops
        ],
    )


def run_out(run: OptimizationRun) -> OptimizationRunOut:
    return OptimizationRunOut(
        id=run.id,
        executed_at=run.executed_at,
        purpose=run.purpose,
        input_source=run.input_source,
        run_group=run.run_group,
        algorithm=run.algorithm,
        execution_mode=run.execution_mode,
        worker_count=run.worker_count,
        order_count=run.order_count,
        courier_count=run.courier_count,
        execution_time_ms=float(run.execution_time_ms),
        total_distance_km=float(run.total_distance_km),
        speedup=float(run.speedup) if run.speedup is not None else None,
        efficiency=float(run.efficiency) if run.efficiency is not None else None,
        same_routes=run.same_routes,
    )


def record_run(
    establishment_id: int,
    result: OptimizationResult,
    *,
    purpose: str,
    input_source: str,
    order_count: int,
    run_group: str,
    elapsed_ms: float | None = None,
    speedup: float | None = None,
    efficiency: float | None = None,
    same_routes: bool | None = None,
) -> OptimizationRun:
    return OptimizationRun(
        establishment_id=establishment_id,
        executed_at=utc_now(),
        algorithm=ALGORITHM,
        execution_mode=result.mode,
        worker_count=max(result.worker_count, 1),
        order_count=order_count,
        courier_count=len(result.routes),
        execution_time_ms=money(result.elapsed_ms if elapsed_ms is None else elapsed_ms),
        total_distance_km=money(result.total_distance_km),
        purpose=purpose,
        input_source=input_source,
        run_group=run_group,
        speedup=money(speedup) if speedup is not None else None,
        efficiency=money(efficiency, 4) if efficiency is not None else None,
        same_routes=same_routes,
    )


# Consultas

def stop_of(order: Order) -> Stop:
    return Stop(str(order.id), float(order.latitude), float(order.longitude))


def in_open_route():
    return exists().where(
        RouteStop.order_id == Order.id,
        RouteStop.route_id == Route.id,
        Route.status.in_(OPEN_ROUTE_STATUSES),
    )


def count_waiting_orders(db: Session, establishment_id: int) -> int:
    """Pedidos atribuídos que ainda não estão em nenhuma rota planejada ou em andamento."""

    return db.scalar(
        select(func.count(Order.id)).where(
            Order.establishment_id == establishment_id,
            Order.status == "ASSIGNED",
            ~in_open_route(),
        )
    )


def assigned_orders_by_courier(db: Session, establishment_id: int) -> dict[Courier, list[Order]]:
    orders = db.scalars(
        select(Order)
        .where(
            Order.establishment_id == establishment_id,
            Order.status == "ASSIGNED",
            Order.assigned_courier_id.is_not(None),
        )
        .order_by(Order.id)
    ).unique()
    groups: dict[Courier, list[Order]] = defaultdict(list)
    for order in orders:
        groups[order.courier].append(order)
    return dict(sorted(groups.items(), key=lambda item: item[0].id))


def overview(db: Session, establishment: Establishment, day: date | None = None) -> RoutesOverviewOut:
    """Rotas do dia e as que ainda estão em andamento de dias anteriores."""

    day = day or local_today()
    routes = db.scalars(
        select(Route)
        .where(
            Route.establishment_id == establishment.id,
            Route.status != "CANCELLED",
            (Route.route_date == day) | (Route.status == "IN_PROGRESS"),
        )
        .order_by(Route.id)
    ).unique()
    return RoutesOverviewOut(
        depot=depot_out(establishment),
        routes=[route_out(route) for route in routes],
        waiting_orders=count_waiting_orders(db, establishment.id),
    )


# Otimização

def run_optimizer(depot: Stop, routes: list[list[Stop]], mode: str, workers: int | None) -> OptimizationResult:
    if mode == "GPU":
        gpu_status = gpu.status()
        if not gpu_status.available:
            raise HTTPException(status.HTTP_409_CONFLICT, f"O modo GPU não está disponível. {gpu_status.reason}")
    return optimize_routes(depot, routes, mode, workers)


def schedule(route: Route, depot: Stop, start: datetime) -> None:
    """Calcula a distância de cada trecho, o horário estimado de chegada e a duração da rota.

    A estimativa usa a velocidade média e o tempo de atendimento por parada da configuração.
    """

    speed = settings.average_speed_kmh
    service = settings.service_minutes_per_stop
    minutes = 0.0
    previous = depot
    for stop in route.stops:
        point = stop_of(stop.order)
        leg = haversine_km(previous, point)
        minutes += leg / speed * 60
        stop.distance_from_previous_km = money(leg)
        stop.estimated_arrival = start + timedelta(minutes=minutes)
        minutes += service
        previous = point
    minutes += haversine_km(previous, depot) / speed * 60
    route.estimated_duration_min = ceil(minutes) if route.stops else 0


def generate_routes(db: Session, user: User, mode: str, workers: int | None) -> RouteGenerationOut:
    """Gera uma rota otimizada para cada entregador com pedidos atribuídos.

    Regras:
    - só entram pedidos na situação Atribuído;
    - entregador fora de serviço ou com rota em andamento fica de fora, com o motivo;
    - as rotas ainda planejadas do estabelecimento são substituídas pelas novas.
    """

    establishment = user.establishment
    depot = require_depot(establishment)
    in_progress = set(
        db.scalars(
            select(Route.courier_id).where(
                Route.establishment_id == establishment.id,
                Route.status == "IN_PROGRESS",
            )
        )
    )
    groups: dict[Courier, list[Order]] = {}
    skipped: list[SkippedCourierOut] = []
    for courier, orders in assigned_orders_by_courier(db, establishment.id).items():
        if courier.availability == "OFFLINE":
            reason = "Está fora de serviço. Os pedidos dele não entraram em nenhuma rota."
        elif courier.id in in_progress:
            reason = "Já está com uma rota em andamento. Os novos pedidos entram na próxima rota."
        else:
            groups[courier] = orders
            continue
        skipped.append(SkippedCourierOut(courier=courier_ref(courier), reason=reason))

    if not groups:
        if skipped:
            reasons = " ".join(f"{item.courier.full_name}: {item.reason}" for item in skipped)
            raise HTTPException(status.HTTP_409_CONFLICT, f"Nenhuma rota foi gerada. {reasons}")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Não há pedidos atribuídos aguardando rota. Atribua os pedidos aos entregadores antes de gerar as rotas.",
        )

    couriers = list(groups)
    result = run_optimizer(depot, [[stop_of(order) for order in groups[c]] for c in couriers], mode, workers)

    for planned in db.scalars(
        select(Route).where(Route.establishment_id == establishment.id, Route.status == "PLANNED")
    ).unique():
        db.delete(planned)
    db.flush()
    # Um pedido reaberto pode ter ficado como parada não realizada de uma rota já
    # encerrada; a nova parada substitui esse registro (order_id é único).
    order_ids = [order.id for orders in groups.values() for order in orders]
    for old_stop in db.scalars(select(RouteStop).where(RouteStop.order_id.in_(order_ids))):
        db.delete(old_stop)
    db.flush()

    now = utc_now()
    today = local_today()
    for courier, solved in zip(couriers, result.routes):
        orders = {str(order.id): order for order in groups[courier]}
        route = Route(
            establishment_id=establishment.id,
            courier=courier,
            route_date=today,
            status="PLANNED",
            algorithm=ALGORITHM,
            execution_mode=mode,
            total_distance_km=money(solved.distance_km),
            created_at=now,
        )
        route.stops = [
            RouteStop(order=orders[stop_id], stop_sequence=position, status="PENDING")
            for position, stop_id in enumerate(solved.stop_ids, start=1)
        ]
        schedule(route, depot, now)
        db.add(route)

    run = record_run(
        establishment.id,
        result,
        purpose="ROUTE_GENERATION",
        input_source="REAL",
        order_count=sum(len(orders) for orders in groups.values()),
        run_group=str(uuid4()),
    )
    db.add(run)
    db.commit()
    return RouteGenerationOut(**overview(db, establishment).model_dump(), skipped=skipped, run=run_out(run))


def courier_route(db: Session, user: User) -> MyRouteOut:
    """A rota em andamento do entregador ou, se não houver, a última planejada."""

    courier = user.courier
    route = None
    if courier is not None:
        for route_status in ("IN_PROGRESS", "PLANNED"):
            route = db.scalars(
                select(Route)
                .where(Route.courier_id == courier.id, Route.status == route_status)
                .order_by(Route.id.desc())
                .limit(1)
            ).first()
            if route is not None:
                break
    return MyRouteOut(depot=depot_out(user.establishment), route=route_out(route) if route else None)


def get_route(db: Session, user: User, route_id: int) -> Route:
    route = db.get(Route, route_id)
    if route is None or route.establishment_id != user.establishment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rota não encontrada.")
    if user.role == "COURIER" and (user.courier is None or route.courier_id != user.courier.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rota não encontrada.")
    return route


def start_route(db: Session, user: User, route_id: int) -> RouteOut:
    """Inicia a rota: todos os pedidos dela passam para Em rota, na ordem calculada."""

    route = get_route(db, user, route_id)
    if route.status == "IN_PROGRESS":
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta rota já está em andamento.")
    if route.status != "PLANNED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta rota já foi encerrada e não pode ser iniciada.")
    if route.courier.availability == "OFFLINE":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{route.courier.user.full_name} está fora de serviço. Fique disponível antes de iniciar a rota.",
        )
    route.status = "IN_PROGRESS"
    for stop in route.stops:
        order = stop.order
        if order.status == "ASSIGNED":
            order.status = "IN_ROUTE"
            order.history.append(
                OrderStatusEvent(
                    status="IN_ROUTE",
                    note=f"Saiu para entrega na rota {route.id}, parada {stop.stop_sequence}",
                    changed_by=user.id,
                )
            )
    schedule(route, require_depot(user.establishment), utc_now())
    db.commit()
    return route_out(route)


# Consistência entre pedidos e rotas

def open_stop_of(db: Session, order: Order) -> RouteStop | None:
    if order.id is None:
        return None
    return db.scalars(
        select(RouteStop)
        .join(Route, RouteStop.route_id == Route.id)
        .where(RouteStop.order_id == order.id, Route.status.in_(OPEN_ROUTE_STATUSES))
    ).first()


def finish_if_done(route: Route) -> None:
    if all(stop.status in FINISHED_STOP_STATUSES for stop in route.stops):
        delivered = any(stop.status == "COMPLETED" for stop in route.stops)
        route.status = "COMPLETED" if delivered else "CANCELLED"


def sync_order_route(db: Session, order: Order, location_changed: bool = False) -> None:
    """Mantém a rota coerente depois de uma mudança no pedido (chamada antes do commit).

    - Rota planejada: se o pedido sair dela (outro entregador, volta para pendente,
      cancelamento ou novo endereço), a rota é descartada e precisa ser gerada de novo.
    - Pedido de rota planejada que sai para entrega ou é entregue inicia a rota.
    - Rota em andamento: entrega conclui a parada; cancelamento marca a parada como
      não realizada; pedido que sai da rota é retirado dela. Quando todas as paradas
      terminam, a rota é concluída.
    """

    stop = open_stop_of(db, order)
    if stop is None:
        return
    route = stop.route
    courier_id = order.courier.id if order.courier is not None else None
    left_route = courier_id != route.courier_id or order.status == "PENDING"
    if route.status == "PLANNED":
        if left_route or location_changed or order.status == "CANCELLED":
            db.delete(route)
            return
        if order.status not in ("IN_ROUTE", "DELIVERED"):
            return
        route.status = "IN_PROGRESS"
    if left_route:
        route.stops.remove(stop)
    elif order.status == "DELIVERED":
        stop.status = "COMPLETED"
    elif order.status == "CANCELLED":
        stop.status = "FAILED"
    finish_if_done(route)


def release_order_for_deletion(db: Session, order: Order) -> None:
    """Um pedido só pode ser excluído se não fizer parte de rota iniciada ou concluída."""

    stop = db.scalars(select(RouteStop).where(RouteStop.order_id == order.id)).first()
    if stop is None:
        return
    if stop.route.status != "PLANNED":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "O pedido já faz parte de uma rota iniciada ou concluída e não pode ser excluído. Cancele-o.",
        )
    db.delete(stop.route)
    db.flush()
