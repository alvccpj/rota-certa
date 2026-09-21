"""Algoritmos iniciais de roteirização usados pelo RotaCerta.

O mesmo núcleo determinístico é executado nos modos sequencial e paralelo para
permitir uma comparação justa de desempenho, sem alterar a qualidade da rota.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from os import cpu_count
from time import perf_counter
from typing import Literal, Sequence


ExecutionMode = Literal["SEQUENTIAL", "PARALLEL"]


@dataclass(frozen=True, slots=True)
class Stop:
    id: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class RouteResult:
    stop_ids: tuple[str, ...]
    distance_km: float


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    mode: ExecutionMode
    routes: tuple[RouteResult, ...]
    elapsed_ms: float
    worker_count: int

    @property
    def total_distance_km(self) -> float:
        return sum(route.distance_km for route in self.routes)


def haversine_km(origin: Stop, destination: Stop) -> float:
    """Calcula a distância geodésica aproximada entre duas coordenadas."""

    earth_radius_km = 6371.0088
    lat1, lon1 = radians(origin.latitude), radians(origin.longitude)
    lat2, lon2 = radians(destination.latitude), radians(destination.longitude)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(value))


def route_distance_km(depot: Stop, route: Sequence[Stop]) -> float:
    """Calcula a distância do depósito às paradas e de volta ao depósito."""

    if not route:
        return 0.0
    points = (depot, *route, depot)
    return sum(haversine_km(points[index], points[index + 1]) for index in range(len(points) - 1))


def nearest_neighbor(depot: Stop, stops: Sequence[Stop]) -> tuple[Stop, ...]:
    """Cria uma rota determinística escolhendo sempre a parada mais próxima."""

    pending = list(stops)
    ordered: list[Stop] = []
    current = depot
    while pending:
        next_stop = min(
            pending,
            key=lambda stop: (haversine_km(current, stop), stop.id),
        )
        ordered.append(next_stop)
        pending.remove(next_stop)
        current = next_stop
    return tuple(ordered)


def two_opt(depot: Stop, route: Sequence[Stop]) -> tuple[Stop, ...]:
    """Refina a rota por trocas 2-opt até não encontrar melhoria."""

    best = tuple(route)
    best_distance = route_distance_km(depot, best)
    improved = True
    while improved:
        improved = False
        for start in range(len(best) - 1):
            for end in range(start + 2, len(best) + 1):
                candidate = best[:start] + tuple(reversed(best[start:end])) + best[end:]
                candidate_distance = route_distance_km(depot, candidate)
                if candidate_distance + 1e-9 < best_distance:
                    best = candidate
                    best_distance = candidate_distance
                    improved = True
    return best


def optimize_route(depot: Stop, stops: Sequence[Stop]) -> RouteResult:
    """Executa vizinho mais próximo seguido de refinamento 2-opt."""

    route = two_opt(depot, nearest_neighbor(depot, stops))
    return RouteResult(
        stop_ids=tuple(stop.id for stop in route),
        distance_km=route_distance_km(depot, route),
    )


def _optimize_job(job: tuple[Stop, tuple[Stop, ...]]) -> RouteResult:
    depot, stops = job
    return optimize_route(depot, stops)


def optimize_routes(
    depot: Stop,
    routes: Sequence[Sequence[Stop]],
    mode: ExecutionMode = "SEQUENTIAL",
    workers: int | None = None,
) -> OptimizationResult:
    """Otimiza rotas independentes no modo sequencial ou paralelo."""

    jobs = tuple((depot, tuple(stops)) for stops in routes)
    started_at = perf_counter()
    if mode == "PARALLEL" and len(jobs) > 1:
        worker_count = min(workers or cpu_count() or 1, len(jobs))
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            results = tuple(executor.map(_optimize_job, jobs))
    else:
        worker_count = 1
        results = tuple(_optimize_job(job) for job in jobs)
    elapsed_ms = (perf_counter() - started_at) * 1000
    return OptimizationResult(
        mode=mode,
        routes=results,
        elapsed_ms=elapsed_ms,
        worker_count=worker_count,
    )


def compare_modes(
    depot: Stop,
    routes: Sequence[Sequence[Stop]],
    workers: int | None = None,
) -> dict[str, object]:
    """Executa os dois modos sobre a mesma entrada e calcula o speedup."""

    sequential = optimize_routes(depot, routes, "SEQUENTIAL", workers)
    parallel = optimize_routes(depot, routes, "PARALLEL", workers)
    speedup = sequential.elapsed_ms / parallel.elapsed_ms if parallel.elapsed_ms else 0.0
    same_routes = tuple(route.stop_ids for route in sequential.routes) == tuple(
        route.stop_ids for route in parallel.routes
    )
    return {
        "sequential": sequential,
        "parallel": parallel,
        "speedup": speedup,
        "same_routes": same_routes,
    }
