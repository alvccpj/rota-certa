import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, model_validator

Role = Literal["ADMIN", "ATTENDANT", "COURIER"]
Availability = Literal["AVAILABLE", "BUSY", "OFFLINE"]
OrderStatus = Literal["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"]

MAX_ORDER_WEIGHT_KG = 500


def clean_text(value: str) -> str:
    return " ".join(value.split())


def person_name(value: str) -> str:
    value = clean_text(value)
    if sum(char.isalpha() for char in value) < 2:
        raise ValueError("Informe um nome com pelo menos duas letras.")
    return value


def phone_br(value: str | None) -> str | None:
    """Aceita telefone com DDD em qualquer formatação e devolve (81) 98800-1001."""

    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        return None
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) not in (10, 11) or digits[0] == "0":
        raise ValueError("Informe o telefone com DDD, por exemplo (81) 98800-1001.")
    return f"({digits[:2]}) {digits[2:-4]}-{digits[-4:]}"


def strong_password(value: str) -> str:
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("A senha precisa ter letras e números.")
    return value


Name = Annotated[str, Field(min_length=2, max_length=150), AfterValidator(person_name)]
Phone = Annotated[str | None, Field(max_length=25), AfterValidator(phone_br)]
Address = Annotated[str, Field(min_length=5, max_length=255), AfterValidator(clean_text)]
Password = Annotated[str, Field(min_length=8, max_length=72), AfterValidator(strong_password)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Autenticação

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RegisterIn(BaseModel):
    establishment_name: Annotated[str, Field(min_length=2, max_length=150), AfterValidator(clean_text)]
    depot_address: Address
    full_name: Name
    email: EmailStr
    password: Password


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
    full_name: Name
    email: EmailStr
    password: Password
    role: Role
    load_capacity_kg: float | None = Field(default=None, gt=0, le=1000)

    @model_validator(mode="after")
    def courier_needs_capacity(self) -> "UserCreate":
        if self.role == "COURIER" and self.load_capacity_kg is None:
            raise ValueError("Informe a capacidade de carga do entregador.")
        return self


class UserUpdate(BaseModel):
    full_name: Name
    email: EmailStr
    role: Role
    active: bool = True
    password: Password | None = None
    load_capacity_kg: float | None = Field(default=None, gt=0, le=1000)
    availability: Availability | None = None


class CourierOption(BaseModel):
    id: int
    full_name: str
    availability: Availability
    load_capacity_kg: float


# Clientes

class CustomerIn(BaseModel):
    full_name: Name
    phone: Phone = None


class CustomerOut(BaseModel):
    id: int
    full_name: str
    phone: str | None
    order_count: int
    last_address: str | None
    last_latitude: float | None
    last_longitude: float | None
    created_at: datetime


# Pedidos

class OrderIn(BaseModel):
    customer_id: int = Field(gt=0)
    delivery_address: Address
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    weight_kg: float = Field(default=1, gt=0, le=MAX_ORDER_WEIGHT_KG)
    priority: int = Field(default=2, ge=1, le=3)
    desired_start: datetime | None = None
    desired_end: datetime | None = None
    assigned_courier_id: int | None = None

    @model_validator(mode="after")
    def window_is_valid(self) -> "OrderIn":
        if self.desired_start and self.desired_end and self.desired_end <= self.desired_start:
            raise ValueError("O fim da janela de entrega deve ser depois do início.")
        return self


class StatusIn(BaseModel):
    status: OrderStatus


class CustomerRef(ORMModel):
    id: int
    full_name: str
    phone: str | None


class AssignedCourierOut(BaseModel):
    id: int
    full_name: str


class OrderOut(BaseModel):
    id: int
    customer: CustomerRef
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
