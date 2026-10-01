import os
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.optimizer import gpu  # noqa: E402
from app.optimizer.routing import (  # noqa: E402
    Stop,
    active_pool_workers,
    compare_modes,
    nearest_neighbor,
    optimize_route,
    optimize_routes,
    route_distance_km,
    same_routes,
    two_opt,
)


def random_routes(couriers: int, stops: int, seed: int = 7) -> list[list[Stop]]:
    rng = random.Random(seed)
    return [
        [Stop(f"{c}-{s}", -8.06 + rng.uniform(-0.06, 0.06), -34.88 + rng.uniform(-0.06, 0.06)) for s in range(stops)]
        for c in range(couriers)
    ]


class RoutingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.depot = Stop("depot", -8.0476, -34.8770)
        self.stops = (
            Stop("A", -8.0500, -34.8800),
            Stop("B", -8.0600, -34.8900),
            Stop("C", -8.0550, -34.8820),
        )

    def test_empty_route_has_zero_distance(self) -> None:
        self.assertEqual(route_distance_km(self.depot, ()), 0.0)

    def test_nearest_neighbor_keeps_every_stop_once(self) -> None:
        route = nearest_neighbor(self.depot, self.stops)
        self.assertEqual({stop.id for stop in route}, {"A", "B", "C"})
        self.assertEqual(len(route), len(self.stops))

    def test_two_opt_never_worsens_route(self) -> None:
        initial = tuple(reversed(self.stops))
        improved = two_opt(self.depot, initial)
        self.assertLessEqual(
            route_distance_km(self.depot, improved),
            route_distance_km(self.depot, initial),
        )

    def test_optimize_route_returns_order_and_distance(self) -> None:
        result = optimize_route(self.depot, self.stops)
        self.assertEqual(set(result.stop_ids), {"A", "B", "C"})
        self.assertGreater(result.distance_km, 0)

    def test_parallel_and_sequential_return_same_routes(self) -> None:
        comparison = compare_modes(
            self.depot,
            (self.stops, tuple(reversed(self.stops))),
            workers=2,
        )
        self.assertTrue(comparison["same_routes"])
        self.assertGreaterEqual(comparison["speedup"], 0)

    def test_two_opt_improves_nearest_neighbor_on_larger_routes(self) -> None:
        stops = random_routes(1, 60)[0]
        initial = nearest_neighbor(self.depot, stops)
        self.assertLess(optimize_route(self.depot, stops).distance_km, route_distance_km(self.depot, initial))

    def test_reported_distance_matches_the_route(self) -> None:
        stops = random_routes(1, 30)[0]
        result = optimize_route(self.depot, stops)
        by_id = {stop.id: stop for stop in stops}
        ordered = [by_id[stop_id] for stop_id in result.stop_ids]
        self.assertAlmostEqual(result.distance_km, route_distance_km(self.depot, ordered), places=9)

    def test_parallel_mode_matches_sequential_on_many_routes(self) -> None:
        routes = random_routes(6, 40)
        sequential = optimize_routes(self.depot, routes, "SEQUENTIAL")
        parallel = optimize_routes(self.depot, routes, "PARALLEL", workers=3)
        self.assertEqual(parallel.worker_count, 3)
        self.assertTrue(same_routes(sequential, parallel))
        self.assertAlmostEqual(sequential.total_distance_km, parallel.total_distance_km, places=9)

    def test_only_one_process_pool_stays_open(self) -> None:
        routes = random_routes(4, 10)
        optimize_routes(self.depot, routes, "PARALLEL", workers=2)
        optimize_routes(self.depot, routes, "PARALLEL", workers=3)
        self.assertEqual(active_pool_workers(), 3)

    def test_worker_processes_use_one_blas_thread(self) -> None:
        # Cada processo do pool é uma unidade de paralelismo; threads extras do
        # OpenBLAS em cada um esgotavam a memória com muitos processos.
        self.assertEqual(os.environ["OPENBLAS_NUM_THREADS"], "1")

    def test_empty_and_single_stop_routes(self) -> None:
        result = optimize_routes(self.depot, [[], [self.stops[0]]], "SEQUENTIAL")
        self.assertEqual(result.routes[0].stop_ids, ())
        self.assertEqual(result.routes[0].distance_km, 0.0)
        self.assertEqual(result.routes[1].stop_ids, ("A",))


@unittest.skipUnless(gpu.status().available, "GPU NVIDIA com CUDA não disponível nesta máquina")
class GpuRoutingTestCase(unittest.TestCase):
    def test_gpu_matches_sequential(self) -> None:
        depot = Stop("depot", -8.0593, -34.8816)
        routes = random_routes(8, 80) + [[], [Stop("unica", -8.05, -34.9)]]
        sequential = optimize_routes(depot, routes, "SEQUENTIAL")
        on_gpu = optimize_routes(depot, routes, "GPU")
        self.assertTrue(same_routes(sequential, on_gpu))
        self.assertAlmostEqual(sequential.total_distance_km, on_gpu.total_distance_km, places=6)


if __name__ == "__main__":
    unittest.main()
