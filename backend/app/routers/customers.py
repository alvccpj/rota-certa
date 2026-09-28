"""Cadastro de clientes do estabelecimento."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Order, User
from app.schemas import CustomerIn, CustomerOut
from app.security import ADMIN, ATTENDANT, require_roles

router = APIRouter(prefix="/customers", tags=["customers"])


def customers_out(db: Session, customers: list[Customer]) -> list[CustomerOut]:
    """Inclui a quantidade de pedidos e o último endereço de entrega de cada cliente."""

    stats: dict[int, tuple[int, int]] = {}
    last_orders: dict[int, Order] = {}
    ids = [customer.id for customer in customers]
    if ids:
        rows = db.execute(
            select(Order.customer_id, func.count(Order.id), func.max(Order.id))
            .where(Order.customer_id.in_(ids))
            .group_by(Order.customer_id)
        )
        stats = {customer_id: (count, last_id) for customer_id, count, last_id in rows}
        last_ids = [last_id for _, last_id in stats.values()]
        if last_ids:
            last_orders = {order.id: order for order in db.scalars(select(Order).where(Order.id.in_(last_ids)))}

    result = []
    for customer in customers:
        count, last_id = stats.get(customer.id, (0, None))
        last = last_orders.get(last_id) if last_id else None
        result.append(
            CustomerOut(
                id=customer.id,
                full_name=customer.full_name,
                phone=customer.phone,
                order_count=count,
                last_address=last.delivery_address if last else None,
                last_latitude=last.latitude if last else None,
                last_longitude=last.longitude if last else None,
                created_at=customer.created_at,
            )
        )
    return result


def get_customer(db: Session, user: User, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None or customer.establishment_id != user.establishment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente não encontrado.")
    return customer


def ensure_unique(db: Session, user: User, data: CustomerIn, ignore_id: int | None = None) -> None:
    query = select(Customer.id).where(
        Customer.establishment_id == user.establishment_id,
        func.lower(Customer.full_name) == data.full_name.lower(),
        Customer.phone.is_(None) if data.phone is None else Customer.phone == data.phone,
    )
    if ignore_id is not None:
        query = query.where(Customer.id != ignore_id)
    if db.scalar(query) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um cliente com este nome e telefone.")


@router.get("", response_model=list[CustomerOut])
def list_customers(
    q: str | None = Query(default=None, max_length=100),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> list[CustomerOut]:
    query = select(Customer).where(Customer.establishment_id == user.establishment_id)
    if q and q.strip():
        term = q.strip().lower()
        query = query.where(or_(func.lower(Customer.full_name).contains(term), Customer.phone.contains(term)))
    return customers_out(db, list(db.scalars(query.order_by(Customer.full_name))))


@router.get("/{customer_id}", response_model=CustomerOut)
def read_customer(
    customer_id: int,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> CustomerOut:
    return customers_out(db, [get_customer(db, user, customer_id)])[0]


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerIn,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> CustomerOut:
    ensure_unique(db, user, data)
    customer = Customer(establishment_id=user.establishment_id, full_name=data.full_name, phone=data.phone)
    db.add(customer)
    db.commit()
    return customers_out(db, [customer])[0]


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    data: CustomerIn,
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> CustomerOut:
    customer = get_customer(db, user, customer_id)
    ensure_unique(db, user, data, ignore_id=customer.id)
    customer.full_name = data.full_name
    customer.phone = data.phone
    db.commit()
    return customers_out(db, [customer])[0]


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    user: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    customer = get_customer(db, user, customer_id)
    orders = db.scalar(select(func.count(Order.id)).where(Order.customer_id == customer.id))
    if orders:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{customer.full_name} tem {orders} {'pedido' if orders == 1 else 'pedidos'} e não pode ser excluído.",
        )
    db.delete(customer)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
