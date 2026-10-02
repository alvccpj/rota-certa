"""Núcleo de roteirização do RotaCerta: vizinho mais próximo seguido de 2-opt.

O mesmo algoritmo roda em três modos de execução:

- SEQUENTIAL: um processo calcula as rotas uma depois da outra (linha de base);
- PARALLEL: as rotas dos entregadores são distribuídas entre processos da CPU;
- GPU: um kernel CUDA calcula todas as rotas ao mesmo tempo, um bloco por rota
  (ver ``gpu.py``).

Os três modos usam a mesma matriz de distâncias, o mesmo critério de desempate e
o 2-opt por melhor melhoria, por isso chegam às mesmas rotas. A comparação mede
apenas a forma de execução, não diferenças de algoritmo.
"""

from __future__ import annotations

import atexit
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from threading import RLock
from time import perf_counter
from typing import Literal, Sequence

# O 2-opt não usa álgebra linear e cada processo já é uma unidade de paralelismo.
# Sem este limite o OpenBLAS do NumPy abre uma thread por núcleo em cada processo
# e, com vários processos, a memória se esgota (BrokenProcessPool). Os processos
# do pool herdam estas variáveis ao iniciar.
for _variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_variable, "1")

import numpy as np  # noqa: E402

ExecutionMode = Literal["SEQUENTIAL", "PARALLEL", "GPU"]
ALGORITHM = "NEAREST_NEIGHBOR_2OPT"
EARTH_RADIUS_KM = 6371.0088
# Uma troca do 2-opt só é aplicada se encurtar a rota mais que isto (em km).
IMPROVEMENT_EPSILON = 1e-10


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

    lat1, lon1 = radians(origin.latitude), radians(origin.longitude)
    lat2, lon2 = radians(destination.latitude), radians(destination.longitude)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(value))


def route_distance_km(depot: Stop, route: Sequence[Stop]) -> float:
    """Calcula a distância do depósito às paradas e de volta ao depósito."""

    if not route:
        return 0.0
    points = (depot, *route, depot)
    return sum(haversine_km(points[index], points[index + 1]) for index in range(len(points) - 1))


# Núcleo numérico. O nó 0 é o depósito e os nós 1..n são as paradas, na ordem
# recebida. Uma rota é um vetor de posições [0, p1, ..., pn, 0].

def coordinates(depot: Stop, stops: Sequence[Stop]) -> tuple[np.ndarray, np.ndarray]:
    """Latitudes e longitudes em radianos, com o depósito na posição 0."""

    points = (depot, *stops)
    latitudes = np.radians(np.array([point.latitude for point in points], dtype=np.float64))
    longitudes = np.radians(np.array([point.longitude for point in points], dtype=np.float64))
    return latitudes, longitudes


def distance_matrix(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    """Matriz de distâncias haversine entre todos os pares de nós, em km."""

    lat1, lat2 = latitudes[:, None], latitudes[None, :]
    half_lat = np.sin((lat2 - lat1) / 2)
    half_lon = np.sin((longitudes[None, :] - longitudes[:, None]) / 2)
    value = half_lat * half_lat + np.cos(lat1) * np.cos(lat2) * (half_lon * half_lon)
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(value))


def nearest_neighbor_tour(matrix: np.ndarray) -> np.ndarray:
    """Sai do depósito e vai sempre para a parada mais próxima ainda não visitada.

    Em caso de empate vence a parada de menor índice, o mesmo critério do kernel CUDA.
    """

    count = matrix.shape[0] - 1
    tour = np.zeros(count + 2, dtype=np.int64)
    visited = np.zeros(count + 1, dtype=bool)
    visited[0] = True
    current = 0
    for step in range(1, count + 1):
        row = np.where(visited, np.inf, matrix[current])
        current = int(np.argmin(row))
        visited[current] = True
        tour[step] = current
    return tour


def two_opt_tour(matrix: np.ndarray, tour: np.ndarray) -> np.ndarray:
    """2-opt por melhor melhoria: a cada rodada aplica a inversão que mais encurta a rota.

    Inverter o trecho entre as posições i e j troca as arestas (i-1, i) e (j, j+1)
    por (i-1, j) e (i, j+1). Todas as trocas possíveis são avaliadas de uma vez;
    em caso de empate vence o menor par (i, j), como no kernel CUDA.
    """

    tour = tour.copy()
    count = len(tour) - 2
    if count < 2:
        return tour
    invalid = ~np.triu(np.ones((count, count), dtype=bool), k=1)
    while True:
        previous = tour[:-2]  # nó antes do início do trecho (posição i-1)
        first = tour[1:-1]  # início do trecho (posição i) e também o fim (posição j)
        following = tour[2:]  # nó depois do fim do trecho (posição j+1)
        delta = (
            matrix[previous[:, None], first[None, :]]
            + matrix[first[:, None], following[None, :]]
            - matrix[previous, first][:, None]
            - matrix[first, following][None, :]
        )
        delta[invalid] = np.inf
        best = int(np.argmin(delta))
        if not delta.flat[best] < -IMPROVEMENT_EPSILON:
            return tour
        start, end = divmod(best, count)
        tour[start + 1 : end + 2] = tour[start + 1 : end + 2][::-1].copy()


def tour_length(matrix: np.ndarray, tour: np.ndarray) -> float:
    return float(matrix[tour[:-1], tour[1:]].sum())


def solve_coordinates(latitudes: np.ndarray, longitudes: np.ndarray) -> tuple[list[int], float]:
    """Resolve uma rota a partir das coordenadas e devolve a ordem das paradas (1..n) e os km."""

    matrix = distance_matrix(latitudes, longitudes)
    tour = two_opt_tour(matrix, nearest_neighbor_tour(matrix))
    return [int(node) for node in tour[1:-1]], tour_length(matrix, tour)


def _to_result(stops: Sequence[Stop], order: Sequence[int], distance: float) -> RouteResult:
    return RouteResult(
        stop_ids=tuple(stops[node - 1].id for node in order),
        distance_km=distance if order else 0.0,
    )


def nearest_neighbor(depot: Stop, stops: Sequence[Stop]) -> tuple[Stop, ...]:
    """Ordem das paradas pelo vizinho mais próximo, sem refinamento."""

    matrix = distance_matrix(*coordinates(depot, stops))
    return tuple(stops[node - 1] for node in nearest_neighbor_tour(matrix)[1:-1])


def two_opt(depot: Stop, route: Sequence[Stop]) -> tuple[Stop, ...]:
    """Refina com 2-opt uma rota já ordenada."""

    matrix = distance_matrix(*coordinates(depot, route))
    initial = np.arange(len(route) + 2, dtype=np.int64)
    initial[-1] = 0
    return tuple(route[node - 1] for node in two_opt_tour(matrix, initial)[1:-1])


def optimize_route(depot: Stop, stops: Sequence[Stop]) -> RouteResult:
    """Executa vizinho mais próximo seguido de refinamento 2-opt."""

    order, distance = solve_coordinates(*coordinates(depot, stops))
    return _to_result(stops, order, distance)


# Execução paralela na CPU. O pool fica aberto entre as chamadas, assim a medição
# não inclui o custo de criar processos (alto no Windows). Existe um pool por vez e
# as execuções paralelas acontecem uma de cada vez: duas ao mesmo tempo dividiriam
# os núcleos entre si e distorceriam as medições.

_pool: ProcessPoolExecutor | None = None
_pool_workers = 0
_pool_lock = RLock()


def available_cpus() -> int:
    return os.cpu_count() or 1


def _pool_for(workers: int) -> ProcessPoolExecutor:
    """Devolve o pool com a quantidade pedida de processos, encerrando o anterior."""

    global _pool, _pool_workers
    if _pool is None or _pool_workers != workers:
        if _pool is not None:
            _pool.shutdown(wait=True)
        _pool = ProcessPoolExecutor(max_workers=workers)
        _pool_workers = workers
    return _pool


def run_parallel(jobs: Sequence[tuple[np.ndarray, np.ndarray]], workers: int) -> list[tuple[list[int], float]]:
    # Uma fatia de rotas por processo: menos mensagens entre os processos do que
    # enviar uma rota de cada vez (na medição, 4 processos caíram de 134 para 82 ms).
    chunk = -(-len(jobs) // workers)
    with _pool_lock:
        return list(_pool_for(workers).map(_solve_job, jobs, chunksize=chunk))


def active_pool_workers() -> int:
    """Quantidade de processos do pool aberto (0 se nenhum)."""

    return _pool_workers if _pool is not None else 0


def warm_up_pool(workers: int) -> None:
    """Garante que todos os processos do pool já iniciaram e carregaram o NumPy."""

    latitudes, longitudes = np.zeros(3), np.array([0.0, 0.001, 0.002])
    run_parallel([(latitudes, longitudes)] * workers * 2, workers)


def shutdown_pools() -> None:
    global _pool, _pool_workers
    if not _pool_lock.acquire(timeout=5):
        return
    try:
        if _pool is not None:
            _pool.shutdown(wait=False, cancel_futures=True)
        _pool, _pool_workers = None, 0
    finally:
        _pool_lock.release()


atexit.register(shutdown_pools)


def _solve_job(job: tuple[np.ndarray, np.ndarray]) -> tuple[list[int], float]:
    return solve_coordinates(*job)


def optimize_routes(
    depot: Stop,
    routes: Sequence[Sequence[Stop]],
    mode: ExecutionMode = "SEQUENTIAL",
    workers: int | None = None,
) -> OptimizationResult:
    """Otimiza rotas independentes no modo pedido e mede o tempo total."""

    routes = [tuple(stops) for stops in routes]
    started_at = perf_counter()
    if mode == "GPU":
        from app.optimizer import gpu

        solved, worker_count = gpu.solve_routes(depot, routes)
    else:
        jobs = [coordinates(depot, stops) for stops in routes]
        if mode == "PARALLEL" and len(jobs) > 1:
            worker_count = min(workers or available_cpus(), len(jobs))
            solved = run_parallel(jobs, worker_count)
        else:
            worker_count = 1
            solved = [_solve_job(job) for job in jobs]
    results = tuple(_to_result(stops, order, distance) for stops, (order, distance) in zip(routes, solved))
    elapsed_ms = (perf_counter() - started_at) * 1000
    return OptimizationResult(mode=mode, routes=results, elapsed_ms=elapsed_ms, worker_count=worker_count)


def same_routes(first: OptimizationResult, second: OptimizationResult) -> bool:
    return [route.stop_ids for route in first.routes] == [route.stop_ids for route in second.routes]


def compare_modes(
    depot: Stop,
    routes: Sequence[Sequence[Stop]],
    workers: int | None = None,
) -> dict[str, object]:
    """Executa os modos sequencial e paralelo sobre a mesma entrada e calcula o speedup."""

    sequential = optimize_routes(depot, routes, "SEQUENTIAL", workers)
    parallel = optimize_routes(depot, routes, "PARALLEL", workers)
    speedup = sequential.elapsed_ms / parallel.elapsed_ms if parallel.elapsed_ms else 0.0
    return {
        "sequential": sequential,
        "parallel": parallel,
        "speedup": speedup,
        "same_routes": same_routes(sequential, parallel),
    }
