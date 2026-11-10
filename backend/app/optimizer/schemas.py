from pydantic import BaseModel, Field, model_validator


class StopInput(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CourierRouteInput(BaseModel):
    courier_id: str = Field(min_length=1, max_length=80)
    stops: list[StopInput] = Field(max_length=500)


class OptimizationRequest(BaseModel):
    depot: StopInput
    routes: list[CourierRouteInput] = Field(min_length=1, max_length=64)
    workers: int | None = Field(default=None, ge=1, le=32)

    @model_validator(mode="after")
    def bounded_workload(self) -> "OptimizationRequest":
        if sum(len(route.stops) for route in self.routes) > 12000:
            raise ValueError("Use no máximo 12.000 paradas no total.")
        return self
