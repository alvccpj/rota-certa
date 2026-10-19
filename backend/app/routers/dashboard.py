"""Painel, relatórios pesquisáveis e histórico operacional integrado."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import reporting
from app.database import get_db
from app.models import User
from app.schemas import (
    DashboardReportRowOut,
    DashboardSummaryOut,
    OperationalEventType,
    OperationalHistoryEventOut,
    OrderStatus,
)
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
    q: str | None = Query(default=None, min_length=1, max_length=100),
    courier_id: int | None = Query(default=None, gt=0),
    priority: int | None = Query(default=None, ge=1, le=3),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> list[DashboardReportRowOut]:
    """Lista os dados operacionais usados na exportação CSV da interface."""

    period = reporting.resolve_period(start, end)
    return reporting.operational_report(db, user, period, status_filter, q, courier_id, priority)


@router.get("/history", response_model=list[OperationalHistoryEventOut])
def history(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    event_type: OperationalEventType | None = Query(default=None, alias="type"),
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> list[OperationalHistoryEventOut]:
    """Exibe o histórico operacional integrado para auditoria e acompanhamento."""

    period = reporting.resolve_period(start, end)
    return reporting.operational_history(db, user, period, event_type, status_filter, q)
