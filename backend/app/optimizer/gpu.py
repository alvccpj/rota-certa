"""Execução do vizinho mais próximo + 2-opt na GPU com CUDA.

Um único kernel resolve todas as rotas de uma vez: cada rota (entregador) fica
com um bloco de 256 threads, e as threads do bloco dividem entre si

1. o cálculo da matriz de distâncias haversine da rota;
2. a busca da parada mais próxima a cada passo do vizinho mais próximo;
3. a avaliação de todas as trocas do 2-opt a cada rodada.

Em cada etapa, as threads guardam o melhor valor que encontraram e uma redução
em memória compartilhada escolhe o melhor do bloco, com o mesmo desempate da
versão em CPU (menor índice). Por isso as rotas saem iguais às dos outros modos.

O kernel é escrito em CUDA C e compilado pelo NVRTC através do CuPy
(``RawKernel``). Ele não usa as operações prontas do CuPy, que dependem de
headers que o NVRTC não encontra quando o projeto está numa pasta com acento.
O CuPy é opcional: sem ele ou sem GPU NVIDIA, ``status()`` informa o motivo e o
sistema continua com os modos de CPU.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Sequence

import numpy as np

from app.optimizer.routing import EARTH_RADIUS_KM, IMPROVEMENT_EPSILON, Stop, coordinates

THREADS_PER_BLOCK = 256
MAX_ITERATIONS = 1_000_000

KERNEL_SOURCE = r"""
#define THREADS %(threads)d
#define EARTH_RADIUS_KM %(radius).17g
#define EPSILON %(epsilon).17g
#define INF __longlong_as_double(0x7ff0000000000000LL)
#define NO_INDEX 0x7fffffff

__device__ double haversine(double lat1, double lon1, double lat2, double lon2) {
    double half_lat = sin((lat2 - lat1) / 2);
    double half_lon = sin((lon2 - lon1) / 2);
    double value = half_lat * half_lat + cos(lat1) * cos(lat2) * (half_lon * half_lon);
    return 2.0 * EARTH_RADIUS_KM * asin(sqrt(value));
}

/* Redução do bloco: menor valor e, em caso de empate, menor índice. */
__device__ void block_argmin(double* values, int* indexes) {
    for (int stride = THREADS / 2; stride > 0; stride >>= 1) {
        if (threadIdx.x < stride) {
            double other = values[threadIdx.x + stride];
            int other_index = indexes[threadIdx.x + stride];
            if (other < values[threadIdx.x]
                || (other == values[threadIdx.x] && other_index < indexes[threadIdx.x])) {
                values[threadIdx.x] = other;
                indexes[threadIdx.x] = other_index;
            }
        }
        __syncthreads();
    }
}

extern "C" __global__ void solve_routes(
    const double* latitudes,          /* radianos; nó 0 de cada rota é o depósito */
    const double* longitudes,
    const int* node_offset,           /* início dos nós de cada rota */
    const int* node_count,            /* paradas + depósito */
    const long long* matrix_offset,   /* início da matriz de cada rota */
    double* matrix,
    int* tours,                       /* rota de cada bloco: n + 2 posições, a partir de node_offset + bloco */
    unsigned char* visited,
    double* lengths,
    int max_iterations)
{
    __shared__ double best_values[THREADS];
    __shared__ int best_indexes[THREADS];
    __shared__ int current;
    __shared__ int stop;
    __shared__ int swap_start;
    __shared__ int swap_end;

    const int route = blockIdx.x;
    const int tid = threadIdx.x;
    const int m = node_count[route];
    const int n = m - 1;
    const double* lat = latitudes + node_offset[route];
    const double* lon = longitudes + node_offset[route];
    double* d = matrix + matrix_offset[route];
    int* tour = tours + node_offset[route] + route;
    unsigned char* seen = visited + node_offset[route];

    /* 1. Matriz de distâncias. */
    for (long long k = tid; k < (long long)m * m; k += THREADS) {
        int a = (int)(k / m);
        int b = (int)(k %% m);
        d[k] = haversine(lat[a], lon[a], lat[b], lon[b]);
    }
    for (int k = tid; k < m; k += THREADS) seen[k] = k == 0;
    if (tid == 0) {
        tour[0] = 0;
        tour[n + 1] = 0;
        current = 0;
    }
    __syncthreads();

    /* 2. Vizinho mais próximo. */
    for (int step = 1; step <= n; ++step) {
        double best = INF;
        int best_index = NO_INDEX;
        for (int s = 1 + tid; s <= n; s += THREADS) {
            double value = d[current * m + s];
            if (!seen[s] && value < best) {
                best = value;
                best_index = s;
            }
        }
        best_values[tid] = best;
        best_indexes[tid] = best_index;
        __syncthreads();
        block_argmin(best_values, best_indexes);
        if (tid == 0) {
            int next = best_indexes[0];
            tour[step] = next;
            seen[next] = 1;
            current = next;
        }
        __syncthreads();
    }

    /* 3. 2-opt por melhor melhoria. O par (i, j) é codificado como (i-1)*n + (j-1). */
    for (int iteration = 0; iteration < max_iterations; ++iteration) {
        double best = INF;
        int best_index = NO_INDEX;
        for (int k = tid; k < n * n; k += THREADS) {
            int i = k / n + 1;
            int j = k %% n + 1;
            if (j <= i) continue;
            int before = tour[i - 1], first = tour[i], last = tour[j], after = tour[j + 1];
            double delta = d[before * m + last] + d[first * m + after]
                - d[before * m + first] - d[last * m + after];
            if (delta < best) {
                best = delta;
                best_index = k;
            }
        }
        best_values[tid] = best;
        best_indexes[tid] = best_index;
        __syncthreads();
        block_argmin(best_values, best_indexes);
        if (tid == 0) {
            stop = !(best_values[0] < -EPSILON);
            if (!stop) {
                swap_start = best_indexes[0] / n + 1;
                swap_end = best_indexes[0] %% n + 1;
            }
        }
        __syncthreads();
        if (stop) break;
        int half = (swap_end - swap_start + 1) / 2;
        for (int q = tid; q < half; q += THREADS) {
            int temp = tour[swap_start + q];
            tour[swap_start + q] = tour[swap_end - q];
            tour[swap_end - q] = temp;
        }
        __syncthreads();
    }

    if (tid == 0) {
        double total = 0.0;
        for (int q = 0; q <= n; ++q) total += d[tour[q] * m + tour[q + 1]];
        lengths[route] = total;
    }
}
""" % {"threads": THREADS_PER_BLOCK, "radius": EARTH_RADIUS_KM, "epsilon": IMPROVEMENT_EPSILON}


@dataclass(frozen=True, slots=True)
class GpuStatus:
    available: bool
    device_name: str | None = None
    reason: str | None = None


_lock = Lock()
_kernel = None
_status: GpuStatus | None = None


def _load_kernel():
    import cupy

    # --fmad=false evita que o compilador junte multiplicação e soma numa só
    # operação, o que mudaria o arredondamento em relação ao NumPy.
    kernel = cupy.RawKernel(KERNEL_SOURCE, "solve_routes", options=("--fmad=false",))
    kernel.compile()
    return kernel


def status() -> GpuStatus:
    """Verifica uma única vez se há CuPy, GPU NVIDIA e se o kernel compila."""

    global _kernel, _status
    with _lock:
        if _status is not None:
            return _status
        try:
            import cupy
        except ImportError:
            _status = GpuStatus(False, reason="O CuPy não está instalado. Veja backend/requirements-gpu.txt.")
            return _status
        try:
            if cupy.cuda.runtime.getDeviceCount() < 1:
                raise RuntimeError
            name = cupy.cuda.runtime.getDeviceProperties(0)["name"]
            device_name = name.decode() if isinstance(name, bytes) else str(name)
        except Exception:
            _status = GpuStatus(False, reason="Nenhuma GPU NVIDIA com CUDA foi encontrada nesta máquina.")
            return _status
        try:
            _kernel = _load_kernel()
        except Exception as exc:
            _status = GpuStatus(False, device_name, f"O kernel CUDA não pôde ser compilado: {exc}")
            return _status
        _status = GpuStatus(True, device_name)
        return _status


def solve_routes(depot: Stop, routes: Sequence[Sequence[Stop]]) -> tuple[list[tuple[list[int], float]], int]:
    """Resolve todas as rotas num único lançamento do kernel.

    Devolve, para cada rota, a ordem das paradas (1..n) e a distância em km, e o
    total de threads lançadas.
    """

    current = status()
    if not current.available:
        raise RuntimeError(current.reason)
    if not routes:
        return [], 0

    import cupy

    latitudes, longitudes, node_offset, node_count, matrix_offset = [], [], [], [], []
    nodes = 0
    matrix_size = 0
    for stops in routes:
        lat, lon = coordinates(depot, stops)
        latitudes.append(lat)
        longitudes.append(lon)
        node_offset.append(nodes)
        node_count.append(len(lat))
        matrix_offset.append(matrix_size)
        nodes += len(lat)
        matrix_size += len(lat) * len(lat)

    route_count = len(routes)
    lat_gpu = cupy.asarray(np.concatenate(latitudes))
    lon_gpu = cupy.asarray(np.concatenate(longitudes))
    node_offset_gpu = cupy.asarray(np.array(node_offset, dtype=np.int32))
    node_count_gpu = cupy.asarray(np.array(node_count, dtype=np.int32))
    matrix_offset_gpu = cupy.asarray(np.array(matrix_offset, dtype=np.int64))
    matrix_gpu = cupy.empty(matrix_size, dtype=cupy.float64)
    tours_gpu = cupy.empty(nodes + route_count, dtype=cupy.int32)
    visited_gpu = cupy.empty(nodes, dtype=cupy.uint8)
    lengths_gpu = cupy.empty(route_count, dtype=cupy.float64)

    _kernel(
        (route_count,),
        (THREADS_PER_BLOCK,),
        (
            lat_gpu,
            lon_gpu,
            node_offset_gpu,
            node_count_gpu,
            matrix_offset_gpu,
            matrix_gpu,
            tours_gpu,
            visited_gpu,
            lengths_gpu,
            np.int32(MAX_ITERATIONS),
        ),
    )
    tours = cupy.asnumpy(tours_gpu)
    lengths = cupy.asnumpy(lengths_gpu)

    solved = []
    for route, (offset, count) in enumerate(zip(node_offset, node_count)):
        tour = tours[offset + route : offset + route + count + 1]
        order = [int(node) for node in tour[1:-1]]
        solved.append((order, float(lengths[route]) if order else 0.0))
    return solved, route_count * THREADS_PER_BLOCK


def warm_up() -> None:
    """Executa uma rota pequena para tirar da medição a inicialização do CUDA."""

    if status().available:
        solve_routes(Stop("depot", -8.05, -34.88), [[Stop("a", -8.06, -34.89), Stop("b", -8.04, -34.87)]])
