"""Mapeamento ORM das tabelas definidas em database/schema.sql."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# BIGSERIAL no PostgreSQL; INTEGER no SQLite usado pelos testes automatizados.
BigId = BigInteger().with_variant(Integer, "sqlite")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Establishment(Base):
    __tablename__ = "establishments"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    document: Mapped[str | None] = mapped_column(String(20))
    depot_address: Mapped[str] = mapped_column(String(255))
    depot_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    depot_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    establishment_id: Mapped[int] = mapped_column(ForeignKey("establishments.id"))
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(180), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    establishment: Mapped[Establishment] = relationship()
    courier: Mapped["Courier | None"] = relationship(back_populates="user", uselist=False)


class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    establishment_id: Mapped[int] = mapped_column(ForeignKey("establishments.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    load_capacity_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    availability: Mapped[str] = mapped_column(String(20), default="AVAILABLE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    user: Mapped[User] = relationship(back_populates="courier", lazy="joined")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    establishment_id: Mapped[int] = mapped_column(ForeignKey("establishments.id"))
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(25))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    establishment_id: Mapped[int] = mapped_column(ForeignKey("establishments.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    assigned_courier_id: Mapped[int | None] = mapped_column(ForeignKey("couriers.id"))
    delivery_address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("1"))
    priority: Mapped[int] = mapped_column(SmallInteger, default=2)
    desired_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    desired_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    customer: Mapped[Customer] = relationship(lazy="joined")
    courier: Mapped[Courier | None] = relationship(lazy="joined")
    history: Mapped[list["OrderStatusEvent"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusEvent.changed_at, OrderStatusEvent.id",
    )


class OrderStatusEvent(Base):
    """Cada mudança de situação do pedido, com o autor e o horário."""

    __tablename__ = "order_status_history"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'ASSIGNED', 'IN_ROUTE', 'DELIVERED', 'CANCELLED')",
            name="order_status_history_status_check",
        ),
        Index("idx_order_status_history_order", "order_id", "changed_at"),
    )

    id: Mapped[int] = mapped_column(BigId, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(String(255))
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    order: Mapped[Order] = relationship(back_populates="history")
    author: Mapped[User | None] = relationship(lazy="joined")
