"""CRUD de pedidos, a entidade principal do RotaCerta."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Courier, Customer, Order, User
from app.schemas import AssignedCourierOut, CustomerRef, OrderIn, OrderOut, OrderStatus, StatusIn
from app.security import ADMIN, ATTENDANT, COURIER, get_current_user, require_roles

router = APIRouter(prefix="/orders", tags=["orders"])

STATUSES_WITH_COURIER = {"ASSIGNED", "IN_ROUTE", "DELIVERED"}
LOCKED_STATUSES = {"DELIVERED", "CANCELLED"}
COURIER_TRANSITIONS = {"ASSIGNED": "IN_ROUTE", "IN_ROUTE": "DELIVERED"}


def order_out(order: Order) -> OrderOut:
    courier = order.courier
    return OrderOut(
        id=order.id,
        customer=CustomerRef.model_validate(order.customer),
        delivery_address=order.delivery_address,
        latitude=order.latitude,
        longitude=order.longitude,
        weight_kg=order.weight_kg,
        priority=order.priority,
        desired_start=order.desired_start,
        desired_end=order.desired_end,
        status=order.status,
        assigned_courier=(
            AssignedCourierOut(id=courier.id, full_name=courier.user.full_name) if courier else None
        ),
        created_at=order.created_at,
    )


def visible_orders(user: User) -> Select[tuple[Order]]:
    """Administradores e atendentes veem o estabelecimento; entregadores, só os seus pedidos."""

    query = select(Order).where(Order.establishment_id == user.establishment_id)
    if user.role == COURIER:
        courier_id = user.courier.id if user.courier else None
        query = query.where(Order.assigned_courier_id == courier_id)
    return query


def get_visible_order(db: Session, user: User, order_id: int) -> Order:
    order = db.scalar(visible_orders(user).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado.")
    return order


def get_courier(db: Session, user: User, courier_id: int | None) -> Courier | None:
    if courier_id is None:
        return None
    courier = db.get(Courier, courier_id)
    if (
        courier is None
        or courier.establishment_id != user.establishment_id
        or courier.user.role != COURIER
        or not courier.user.active
    ):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Entregador inválido para este estabelecimento.")
    return courier


def get_customer(db: Session, user: User, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None or customer.establishment_id != user.establishment_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cliente inválido para este estabelecimento.")
    return customer


def apply_order_data(db: Session, user: User, order: Order, data: OrderIn) -> None:
    courier = get_courier(db, user, data.assigned_courier_id)
    order.customer = get_customer(db, user, data.customer_id)
    order.delivery_address = data.delivery_address
    order.latitude = Decimal(f"{data.latitude:.6f}")
    order.longitude = Decimal(f"{data.longitude:.6f}")
    order.weight_kg = Decimal(f"{data.weight_kg:.2f}")
    order.priority = data.priority
    order.desired_start = data.desired_start
    order.desired_end = data.desired_end

    if courier is None and order.status == "IN_ROUTE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Um pedido em rota precisa continuar com o entregador.")
    order.courier = courier
    if courier is not None and order.status == "PENDING":
        order.status = "ASSIGNED"
    elif courier is None and order.status == "ASSIGNED":
        order.status = "PENDING"


@router.get("", response_model=list[OrderOut])
def list_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrderOut]:
    query = visible_orders(user)
    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    orders = db.scalars(query.order_by(Order.id.desc())).unique()
    return [order_out(order) for order in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> OrderOut:
    return order_out(get_visible_order(db, user, order_id))


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderIn,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> OrderOut:
    order = Order(establishment_id=user.establishment_id, status="PENDING")
    apply_order_data(db, user, order, data)
    db.add(order)
    db.commit()
    return order_out(order)


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    data: OrderIn,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> OrderOut:
    order = get_visible_order(db, user, order_id)
    if order.status in LOCKED_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "Pedidos entregues ou cancelados não podem ser editados.")
    apply_order_data(db, user, order, data)
    db.commit()
    return order_out(order)


@router.patch("/{order_id}/status", response_model=OrderOut)
def change_order_status(
    order_id: int,
    data: StatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderOut:
    order = get_visible_order(db, user, order_id)
    if user.role == COURIER:
        if COURIER_TRANSITIONS.get(order.status) != data.status:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "O entregador só pode avançar o pedido de Atribuído para Em rota e de Em rota para Entregue.",
            )
    elif data.status in STATUSES_WITH_COURIER and order.courier is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Atribua um entregador antes de usar este status.")
    if data.status == "PENDING":
        order.courier = None
    order.status = data.status
    db.commit()
    return order_out(order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    user: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    order = get_visible_order(db, user, order_id)
    db.delete(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "O pedido já faz parte de uma rota e não pode ser excluído. Cancele-o.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
