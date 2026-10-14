"""Terceiro módulo: painel operacional e relatório integrado."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import reporting
from app.database import get_db
from app.models import User
from app.schemas import DashboardReportRowOut, DashboardSummaryOut, OrderStatus
from app.security import ADMIN, ATTENDANT, require_roles

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def summary(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> DashboardSummaryOut:
    """Consolida pedidos, entregadores, rotas e desempenho no período."""

    return reporting.dashboard_summary(db, user, reporting.resolve_period(start, end))


@router.get("/report", response_model=list[DashboardReportRowOut])
def report(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> list[DashboardReportRowOut]:
    """Lista os dados operacionais usados na exportação CSV da interface."""

    period = reporting.resolve_period(start, end)
    return reporting.operational_report(db, user, period, status_filter)
