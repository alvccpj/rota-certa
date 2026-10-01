"""Roteirização: ponto de saída, geração das rotas e acompanhamento pelo entregador."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import planning
from app.database import get_db
from app.models import User
from app.schemas import (
    DepotIn,
    DepotOut,
    MyRouteOut,
    RouteGenerateIn,
    RouteGenerationOut,
    RouteOut,
    RoutesOverviewOut,
)
from app.security import ADMIN, ATTENDANT, COURIER, get_current_user, require_roles

router = APIRouter(tags=["routes"])


@router.get("/establishment/depot", response_model=DepotOut)
def get_depot(user: User = Depends(require_roles(ADMIN, ATTENDANT))) -> DepotOut:
    return planning.depot_out(user.establishment)


@router.put("/establishment/depot", response_model=DepotOut)
def update_depot(
    data: DepotIn,
    user: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> DepotOut:
    """Define o endereço e a posição de onde saem e para onde voltam as rotas."""

    establishment = user.establishment
    establishment.depot_address = data.depot_address
    establishment.depot_latitude = Decimal(f"{data.latitude:.6f}")
    establishment.depot_longitude = Decimal(f"{data.longitude:.6f}")
    db.commit()
    return planning.depot_out(establishment)


@router.get("/routes", response_model=RoutesOverviewOut)
def list_routes(
    day: date | None = Query(default=None, alias="date"),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> RoutesOverviewOut:
    """Rotas do dia (hoje, se a data não for informada) e as que ainda estão em andamento."""

    return planning.overview(db, user.establishment, day)


@router.post("/routes/generate", response_model=RouteGenerationOut)
def generate_routes(
    data: RouteGenerateIn,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> RouteGenerationOut:
    return planning.generate_routes(db, user, data.mode, data.workers)


@router.get("/routes/me", response_model=MyRouteOut)
def my_route(user: User = Depends(require_roles(COURIER)), db: Session = Depends(get_db)) -> MyRouteOut:
    return planning.courier_route(db, user)


@router.patch("/routes/{route_id}/start", response_model=RouteOut)
def start_route(route_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RouteOut:
    return planning.start_route(db, user, route_id)
