"""Comparação de desempenho entre os modos sequencial, paralelo em CPU e GPU.

Metodologia:
- todos os modos recebem exatamente a mesma entrada;
- antes de medir, os processos da CPU são iniciados e o kernel CUDA é compilado,
  para que a medição contenha só o cálculo das rotas e a troca de dados;
- cada modo roda ``repetitions`` vezes e vale a mediana dos tempos;
- speedup = tempo sequencial / tempo do modo;
- eficiência = speedup / número de workers (só faz sentido para a CPU; na GPU
  o paralelismo é de milhares de threads e a eficiência fica em branco).
"""

import random
from math import cos, pi, radians, sin, sqrt
from statistics import median
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OptimizationRun, User
from app.optimizer import gpu
from app.optimizer.routing import OptimizationResult, Stop, optimize_routes, same_routes, warm_up_pool
from app.planning import assigned_orders_by_courier, record_run, require_depot, run_out, stop_of
from app.schemas import BenchmarkIn, BenchmarkOut, OptimizationRunOut

RECIFE = Stop("depot", -8.0593, -34.8816)
SYNTHETIC_RADIUS_KM = 8.0
KM_PER_DEGREE = 111.32


def synthetic_routes(depot: Stop, couriers: int, stops_per_courier: int, seed: int) -> list[list[Stop]]:
    """Paradas sorteadas de modo uniforme num raio em volta do depósito (reproduzível pela semente)."""

    rng = random.Random(seed)
    routes = []
    for courier in range(couriers):
        stops = []
        for index in range(stops_per_courier):
            distance = SYNTHETIC_RADIUS_KM * sqrt(rng.random())
            angle = rng.uniform(0, 2 * pi)
            latitude = depot.latitude + distance * cos(angle) / KM_PER_DEGREE
            longitude = depot.longitude + distance * sin(angle) / (KM_PER_DEGREE * cos(radians(depot.latitude)))
            stops.append(Stop(f"{courier + 1}-{index + 1}", latitude, longitude))
        routes.append(stops)
    return routes


def real_routes(db: Session, user: User) -> tuple[Stop, list[list[Stop]]]:
    depot = require_depot(user.establishment)
    groups = assigned_orders_by_courier(db, user.establishment_id)
    if not groups:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Não há pedidos atribuídos para comparar. Use a instância sintética ou atribua pedidos aos entregadores.",
        )
    return depot, [[stop_of(order) for order in orders] for orders in groups.values()]


def measure(depot: Stop, routes: list[list[Stop]], mode: str, workers: int | None, repetitions: int):
    results: list[OptimizationResult] = [optimize_routes(depot, routes, mode, workers) for _ in range(repetitions)]
    return results[-1], median(result.elapsed_ms for result in results)


def run_benchmark(db: Session, user: User, data: BenchmarkIn) -> BenchmarkOut:
    if data.source == "REAL":
        depot, routes = real_routes(db, user)
    else:
        establishment = user.establishment
        depot = RECIFE
        if establishment.depot_latitude is not None and establishment.depot_longitude is not None:
            depot = Stop("depot", float(establishment.depot_latitude), float(establishment.depot_longitude))
        routes = synthetic_routes(depot, data.couriers, data.stops_per_courier, data.seed)

    if data.include_gpu:
        gpu_status = gpu.status()
        if not gpu_status.available:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"O modo GPU não está disponível. {gpu_status.reason} Desmarque a GPU para comparar só a CPU.",
            )
        gpu.warm_up()

    configs: list[tuple[str, int | None]] = [("SEQUENTIAL", 1)]
    configs += [("PARALLEL", workers) for workers in data.worker_counts]
    if data.include_gpu:
        configs.append(("GPU", None))
    measured = []
    for mode, workers in configs:
        # Só um pool fica aberto por vez, então cada um é aquecido logo antes de medir.
        if mode == "PARALLEL" and len(routes) > 1:
            warm_up_pool(min(workers, len(routes)))
        measured.append((mode, *measure(depot, routes, mode, workers, data.repetitions)))
    baseline_result, baseline_ms = measured[0][1], measured[0][2]
    order_count = sum(len(stops) for stops in routes)
    run_group = str(uuid4())
    runs = []
    for mode, result, elapsed_ms in measured:
        speedup = baseline_ms / elapsed_ms if elapsed_ms else None
        efficiency = speedup / result.worker_count if speedup is not None and mode != "GPU" else None
        run = record_run(
            user.establishment_id,
            result,
            purpose="BENCHMARK",
            input_source=data.source,
            order_count=order_count,
            run_group=run_group,
            elapsed_ms=elapsed_ms,
            speedup=speedup,
            efficiency=efficiency,
            same_routes=same_routes(baseline_result, result),
        )
        db.add(run)
        runs.append(run)
    db.commit()
    return BenchmarkOut(
        run_group=run_group,
        source=data.source,
        courier_count=len(routes),
        order_count=order_count,
        repetitions=data.repetitions,
        rows=[run_out(run) for run in runs],
    )


def list_runs(db: Session, user: User, limit: int) -> list[OptimizationRunOut]:
    runs = db.scalars(
        select(OptimizationRun)
        .where(OptimizationRun.establishment_id == user.establishment_id)
        .order_by(OptimizationRun.executed_at.desc(), OptimizationRun.id.desc())
        .limit(limit)
    )
    return [run_out(run) for run in runs]
