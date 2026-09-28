"""Dados de demonstração criados quando o banco ainda não possui estabelecimentos."""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Courier, Customer, Establishment, Order, User
from app.security import ADMIN, ATTENDANT, COURIER, hash_password

DEMO_PASSWORD = "rotacerta123"
RECIFE = timezone(timedelta(hours=-3))

DEMO_USERS = (
    ("Ana Administradora", "admin@rotacerta.com.br", ADMIN, None),
    ("Bruno Atendente", "atendente@rotacerta.com.br", ATTENDANT, None),
    ("Carla Entregadora", "entregador@rotacerta.com.br", COURIER, "25"),
    ("Diego Entregador", "entregador2@rotacerta.com.br", COURIER, "40"),
)

# cliente, telefone, endereço, latitude, longitude, peso, prioridade, status, entregador
DEMO_ORDERS = (
    ("Maria Silva", "(81) 98800-1001", "Av. Boa Viagem, 1200 - Boa Viagem", "-8.119700", "-34.900600", "2.50", 1, "ASSIGNED", 0),
    ("João Pereira", "(81) 98800-1002", "Rua Amélia, 300 - Graças", "-8.044400", "-34.898600", "1.20", 2, "IN_ROUTE", 0),
    ("Ana Costa", "(81) 98800-1003", "Estrada do Encanamento, 800 - Casa Forte", "-8.033500", "-34.917900", "4.00", 2, "PENDING", None),
    ("Carlos Souza", "(81) 98800-1004", "Rua do Espinheiro, 450 - Espinheiro", "-8.045200", "-34.892000", "0.80", 3, "ASSIGNED", 1),
    ("Fernanda Lima", "(81) 98800-1005", "Rua Real da Torre, 900 - Madalena", "-8.055800", "-34.909200", "3.00", 1, "PENDING", None),
    ("Paulo Mendes", "(81) 98800-1006", "Rua da Hora, 150 - Espinheiro", "-8.041900", "-34.888900", "1.50", 2, "DELIVERED", 1),
)


def seed_demo_data(db: Session) -> bool:
    if db.scalar(select(func.count()).select_from(Establishment)):
        return False

    establishment = Establishment(
        name="Farmácia Boa Saúde (demonstração)",
        depot_address="Rua da Aurora, 325 - Boa Vista, Recife - PE",
        depot_latitude=Decimal("-8.059300"),
        depot_longitude=Decimal("-34.881600"),
    )
    db.add(establishment)
    db.flush()

    couriers: list[Courier] = []
    for full_name, email, role, capacity in DEMO_USERS:
        user = User(
            establishment_id=establishment.id,
            full_name=full_name,
            email=email,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
        )
        if capacity is not None:
            user.courier = Courier(establishment_id=establishment.id, load_capacity_kg=Decimal(capacity))
            couriers.append(user.courier)
        db.add(user)

    today = datetime.now(RECIFE).date()
    for index, (name, phone, address, lat, lon, weight, priority, status, courier_index) in enumerate(DEMO_ORDERS):
        start = datetime.combine(today, time(9 + index), tzinfo=RECIFE)
        db.add(
            Order(
                establishment_id=establishment.id,
                customer=Customer(establishment_id=establishment.id, full_name=name, phone=phone),
                courier=couriers[courier_index] if courier_index is not None else None,
                delivery_address=f"{address}, Recife - PE",
                latitude=Decimal(lat),
                longitude=Decimal(lon),
                weight_kg=Decimal(weight),
                priority=priority,
                desired_start=start,
                desired_end=start + timedelta(hours=2),
                status=status,
            )
        )
    db.commit()
    return True
