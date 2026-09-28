from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Courier, Order, User
from app.routers.auth import ensure_email_available
from app.rules import active_loads
from app.schemas import AvailabilityIn, CourierOption, CourierOut, UserCreate, UserOut, UserUpdate
from app.security import ADMIN, ATTENDANT, COURIER, hash_password, require_roles

router = APIRouter(tags=["users"])


def get_user_in_establishment(db: Session, admin: User, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.establishment_id != admin.establishment_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado.")
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(require_roles(ADMIN)), db: Session = Depends(get_db)) -> list[User]:
    query = select(User).where(User.establishment_id == admin.establishment_id).order_by(User.full_name)
    return list(db.scalars(query))


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    admin: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    ensure_email_available(db, data.email)
    user = User(
        establishment_id=admin.establishment_id,
        full_name=data.full_name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
    )
    if data.role == COURIER:
        user.courier = Courier(
            establishment_id=admin.establishment_id,
            load_capacity_kg=Decimal(str(data.load_capacity_kg)),
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    admin: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    return get_user_in_establishment(db, admin, user_id)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_in_establishment(db, admin, user_id)
    if user.id == admin.id and (data.role != ADMIN or not data.active):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Você não pode remover o próprio acesso de administrador.",
        )
    ensure_email_available(db, data.email, ignore_user_id=user.id)

    user.full_name = data.full_name
    user.email = data.email.lower()
    user.role = data.role
    user.active = data.active
    if data.password:
        user.password_hash = hash_password(data.password)

    if data.role == COURIER:
        if user.courier is None:
            if data.load_capacity_kg is None:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Informe a capacidade de carga do entregador.",
                )
            user.courier = Courier(
                establishment_id=user.establishment_id,
                load_capacity_kg=Decimal(str(data.load_capacity_kg)),
            )
        elif data.load_capacity_kg is not None:
            user.courier.load_capacity_kg = Decimal(str(data.load_capacity_kg))
        if data.availability is not None:
            user.courier.availability = data.availability
    if user.courier is not None and (data.role != COURIER or not data.active):
        # O registro de entregador é mantido por causa do histórico de pedidos.
        user.courier.availability = "OFFLINE"

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    admin: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> Response:
    """Desativa o usuário; o registro é preservado por causa do histórico."""

    user = get_user_in_establishment(db, admin, user_id)
    if user.id == admin.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Você não pode desativar o próprio usuário.")
    user.active = False
    if user.courier is not None:
        user.courier.availability = "OFFLINE"
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/couriers", response_model=list[CourierOption], tags=["couriers"])
def list_couriers(
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
    db: Session = Depends(get_db),
) -> list[CourierOption]:
    query = (
        select(Courier, User)
        .join(User, Courier.user_id == User.id)
        .where(
            Courier.establishment_id == user.establishment_id,
            User.role == COURIER,
            User.active.is_(True),
        )
        .order_by(User.full_name)
    )
    rows = list(db.execute(query))
    loads = active_loads(db, [courier.id for courier, _ in rows])
    return [
        CourierOption(
            id=courier.id,
            full_name=courier_user.full_name,
            availability=courier.availability,
            load_capacity_kg=courier.load_capacity_kg,
            active_load_kg=loads.get(courier.id, (0, 0))[0],
            active_orders=loads.get(courier.id, (0, 0))[1],
        )
        for courier, courier_user in rows
    ]


@router.patch("/couriers/me/availability", response_model=CourierOut, tags=["couriers"])
def update_my_availability(
    data: AvailabilityIn,
    user: User = Depends(require_roles(COURIER)),
    db: Session = Depends(get_db),
) -> Courier:
    """O entregador informa se está disponível para receber pedidos."""

    courier = user.courier
    if courier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cadastro de entregador não encontrado.")
    if data.availability == "OFFLINE":
        in_route = db.scalar(
            select(func.count(Order.id)).where(Order.assigned_courier_id == courier.id, Order.status == "IN_ROUTE")
        )
        if in_route:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Finalize as entregas em rota antes de ficar fora de serviço.",
            )
    courier.availability = data.availability
    db.commit()
    return courier
