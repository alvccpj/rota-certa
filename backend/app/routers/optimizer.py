"""Comparação de desempenho do otimizador e histórico das execuções."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import benchmark
from app.database import get_db
from app.models import User
from app.optimizer import gpu
from app.optimizer.routing import Stop, available_cpus, compare_modes
from app.optimizer.schemas import OptimizationRequest
from app.schemas import BenchmarkIn, BenchmarkOut, CapabilitiesOut, OptimizationRunOut
from app.security import ADMIN, ATTENDANT, require_roles

router = APIRouter(prefix="/optimizer", tags=["optimizer"])


@router.get("/capabilities", response_model=CapabilitiesOut)
def capabilities(_: User = Depends(require_roles(ADMIN, ATTENDANT))) -> CapabilitiesOut:
    """Núcleos de CPU disponíveis e se o modo GPU pode ser usado nesta máquina."""

    gpu_status = gpu.status()
    return CapabilitiesOut(
        cpu_count=available_cpus(),
        gpu_available=gpu_status.available,
        gpu_name=gpu_status.device_name,
        gpu_reason=gpu_status.reason,
    )


@router.post("/benchmark", response_model=BenchmarkOut)
def run_benchmark(
    data: BenchmarkIn,
    user: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> BenchmarkOut:
    """Executa os modos sobre a mesma entrada e registra tempo, speedup e eficiência."""

    return benchmark.run_benchmark(db, user, data)


@router.get("/runs", response_model=list[OptimizationRunOut])
def list_runs(
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(require_roles(ADMIN)),
    db: Session = Depends(get_db),
) -> list[OptimizationRunOut]:
    return benchmark.list_runs(db, user, limit)


@router.post("/compare")
def compare_optimizer_modes(request: OptimizationRequest) -> dict[str, object]:
    """Compara o mesmo algoritmo nos modos sequencial e paralelo (entrada livre, da Sprint 02)."""

    depot = Stop(**request.depot.model_dump())
    routes = [
        [Stop(**stop.model_dump()) for stop in route.stops]
        for route in request.routes
    ]
    comparison = compare_modes(depot, routes, request.workers)
    return {
        "courier_ids": [route.courier_id for route in request.routes],
        "sequential": asdict(comparison["sequential"]),
        "parallel": asdict(comparison["parallel"]),
        "speedup": comparison["speedup"],
        "same_routes": comparison["same_routes"],
    }
