from pydantic import BaseModel, Field


class StopInput(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CourierRouteInput(BaseModel):
    courier_id: str = Field(min_length=1, max_length=80)
    stops: list[StopInput]


class OptimizationRequest(BaseModel):
    depot: StopInput
    routes: list[CourierRouteInput] = Field(min_length=1)
    workers: int | None = Field(default=None, ge=1, le=32)
