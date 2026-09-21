from dataclasses import asdict

from fastapi import FastAPI

from app.optimizer.routing import Stop, compare_modes
from app.optimizer.schemas import OptimizationRequest

app = FastAPI(
    title="RotaCerta API",
    version="0.1.0",
    description="API inicial para cadastro, roteirização e acompanhamento de entregas.",
)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/optimizer/compare", tags=["optimizer"])
def compare_optimizer_modes(request: OptimizationRequest) -> dict[str, object]:
    """Compara o mesmo algoritmo nos modos sequencial e paralelo."""

    depot = Stop(**request.depot.model_dump())
    routes = [
        [Stop(**stop.model_dump()) for stop in route.stops]
        for route in request.routes
    ]
    comparison = compare_modes(depot, routes, request.workers)
    sequential = comparison["sequential"]
    parallel = comparison["parallel"]
    return {
        "courier_ids": [route.courier_id for route in request.routes],
        "sequential": asdict(sequential),
        "parallel": asdict(parallel),
        "speedup": comparison["speedup"],
        "same_routes": comparison["same_routes"],
    }
