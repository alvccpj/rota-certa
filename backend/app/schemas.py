import re
from datetime import date, datetime
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
    active_load_kg: float
    active_orders: int


class AvailabilityIn(BaseModel):
    availability: Availability


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
    note: Annotated[str, Field(max_length=255), AfterValidator(clean_text)] | None = None


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


class HistoryOut(BaseModel):
    status: OrderStatus
    note: str | None
    changed_by: str | None
    changed_at: datetime


class OrderDetailOut(OrderOut):
    history: list[HistoryOut]


# Busca de endereço

class GeocodeResult(BaseModel):
    label: str
    latitude: float
    longitude: float


# Ponto de saída das entregas

class DepotIn(BaseModel):
    depot_address: Address
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class DepotOut(BaseModel):
    address: str
    latitude: float | None
    longitude: float | None


# Rotas

ExecutionMode = Literal["SEQUENTIAL", "PARALLEL", "GPU"]
RouteStatus = Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
StopStatus = Literal["PENDING", "ARRIVED", "COMPLETED", "FAILED"]
MAX_WORKERS = 64


class RouteGenerateIn(BaseModel):
    mode: ExecutionMode = "SEQUENTIAL"
    workers: int | None = Field(default=None, ge=1, le=MAX_WORKERS)


class RouteStopOut(BaseModel):
    sequence: int
    status: StopStatus
    order_id: int
    order_status: OrderStatus
    customer_name: str
    customer_phone: str | None
    delivery_address: str
    latitude: float
    longitude: float
    priority: int
    weight_kg: float
    distance_from_previous_km: float | None
    estimated_arrival: datetime | None


class RouteOut(BaseModel):
    id: int
    courier: AssignedCourierOut
    route_date: date
    status: RouteStatus
    algorithm: str
    execution_mode: ExecutionMode
    total_distance_km: float | None
    estimated_duration_min: int | None
    created_at: datetime
    stops: list[RouteStopOut]


class SkippedCourierOut(BaseModel):
    courier: AssignedCourierOut
    reason: str


class OptimizationRunOut(BaseModel):
    id: int
    executed_at: datetime
    purpose: Literal["ROUTE_GENERATION", "BENCHMARK"]
    input_source: Literal["REAL", "SYNTHETIC"]
    run_group: str | None
    algorithm: str
    execution_mode: ExecutionMode
    worker_count: int
    order_count: int
    courier_count: int
    execution_time_ms: float
    total_distance_km: float
    speedup: float | None
    efficiency: float | None
    same_routes: bool | None


class RoutesOverviewOut(BaseModel):
    depot: DepotOut
    routes: list[RouteOut]
    waiting_orders: int


class RouteGenerationOut(RoutesOverviewOut):
    skipped: list[SkippedCourierOut]
    run: OptimizationRunOut


class MyRouteOut(BaseModel):
    depot: DepotOut
    route: RouteOut | None


# Comparação de desempenho

class CapabilitiesOut(BaseModel):
    cpu_count: int
    gpu_available: bool
    gpu_name: str | None
    gpu_reason: str | None


class BenchmarkIn(BaseModel):
    source: Literal["REAL", "SYNTHETIC"] = "SYNTHETIC"
    couriers: int = Field(default=16, ge=1, le=64)
    stops_per_courier: int = Field(default=200, ge=2, le=500)
    worker_counts: list[Annotated[int, Field(ge=1, le=MAX_WORKERS)]] = Field(
        default_factory=lambda: [1, 2, 4, 8], min_length=1, max_length=8
    )
    include_gpu: bool = True
    repetitions: int = Field(default=3, ge=1, le=5)
    seed: int = Field(default=42, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def limit_size(self) -> "BenchmarkIn":
        if self.source == "SYNTHETIC" and self.couriers * self.stops_per_courier > 12_000:
            raise ValueError("Use no máximo 12.000 paradas no total (entregadores × paradas por entregador).")
        self.worker_counts = sorted(set(self.worker_counts))
        return self


class BenchmarkOut(BaseModel):
    run_group: str
    source: Literal["REAL", "SYNTHETIC"]
    courier_count: int
    order_count: int
    repetitions: int
    rows: list[OptimizationRunOut]
