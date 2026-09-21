import unittest

from backend.app.optimizer.routing import (
    Stop,
    compare_modes,
    nearest_neighbor,
    optimize_route,
    route_distance_km,
    two_opt,
)


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


if __name__ == "__main__":
    unittest.main()
