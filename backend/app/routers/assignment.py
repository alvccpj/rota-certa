"""Endpoint de atribuição automática, registrado antes das rotas dinâmicas de pedidos."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.assignment import AutoAssignOut, auto_assign_orders
from app.database import get_db
from app.models import User
from app.security import ADMIN, ATTENDANT, require_roles

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/auto-assign", response_model=AutoAssignOut)
def auto_assign(
    actor: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> AutoAssignOut:
    return auto_assign_orders(db, actor)
