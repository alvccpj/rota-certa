from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Role = Literal["ADMIN", "ATTENDANT", "COURIER"]
Availability = Literal["AVAILABLE", "BUSY", "OFFLINE"]
OrderStatus = Literal["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"]

Password = Field(min_length=8, max_length=72)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Autenticação

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RegisterIn(BaseModel):
    establishment_name: str = Field(min_length=2, max_length=150)
    depot_address: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Password


# Usuários

class CourierOut(ORMModel):
    id: int
    load_capacity_kg: float
    availability: Availability


class EstablishmentOut(ORMModel):
    id: int
    name: str


class UserOut(ORMModel):
    id: int
    full_name: str
    email: str
    role: Role
    active: bool
    created_at: datetime
    establishment: EstablishmentOut
    courier: CourierOut | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Password
    role: Role
    load_capacity_kg: float | None = Field(default=None, gt=0, le=999999)

    @model_validator(mode="after")
    def courier_needs_capacity(self) -> "UserCreate":
        if self.role == "COURIER" and self.load_capacity_kg is None:
            raise ValueError("Informe a capacidade de carga do entregador.")
        return self


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    role: Role
    active: bool = True
    password: str | None = Field(default=None, min_length=8, max_length=72)
    load_capacity_kg: float | None = Field(default=None, gt=0, le=999999)
    availability: Availability | None = None


class CourierOption(BaseModel):
    id: int
    full_name: str
    availability: Availability
    load_capacity_kg: float


# Pedidos

class OrderIn(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    customer_phone: str | None = Field(default=None, max_length=25)
    delivery_address: str = Field(min_length=5, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    weight_kg: float = Field(default=1, gt=0, le=999999)
    priority: int = Field(default=2, ge=1, le=3)
    desired_start: datetime | None = None
    desired_end: datetime | None = None
    assigned_courier_id: int | None = None

    @model_validator(mode="after")
    def window_is_valid(self) -> "OrderIn":
        if self.desired_start and self.desired_end and self.desired_end < self.desired_start:
            raise ValueError("O fim da janela de entrega deve ser posterior ao início.")
        return self


class StatusIn(BaseModel):
    status: OrderStatus


class CustomerOut(ORMModel):
    id: int
    full_name: str
    phone: str | None


class AssignedCourierOut(BaseModel):
    id: int
    full_name: str


class OrderOut(ORMModel):
    id: int
    customer: CustomerOut
    delivery_address: str
    latitude: float
    longitude: float
    weight_kg: float
    priority: int
    desired_start: datetime | None
    desired_end: datetime | None
    status: OrderStatus
    assigned_courier: AssignedCourierOut | None
    created_at: datetime
