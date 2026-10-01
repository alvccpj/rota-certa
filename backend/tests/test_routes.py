"""Testes do módulo de roteirização: geração, regras de negócio e acompanhamento das rotas."""

import unittest
from unittest.mock import patch

from api_base import ApiTestCase

from app.models import Establishment
from app.optimizer.gpu import GpuStatus


class RoutesTestCase(ApiTestCase):
    @property
    def diego(self) -> dict[str, str]:
        return self._cached("entregador2@rotacerta.com.br")

    def generate(self, headers=None, **body):
        return self.client.post("/routes/generate", headers=headers or self.admin, json=body)

    def routes_by_courier(self, payload: dict) -> dict[str, dict]:
        return {route["courier"]["full_name"]: route for route in payload["routes"]}

    def assigned_order(self, courier: str = "Carla Entregadora", **changes) -> int:
        payload = self.order_payload(assigned_courier_id=self.courier_id(courier), **changes)
        response = self.client.post("/orders", headers=self.admin, json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def test_generate_creates_one_route_per_courier_with_every_assigned_order(self) -> None:
        extra = self.assigned_order(latitude=-8.07, longitude=-34.91)
        response = self.generate()
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        routes = self.routes_by_courier(payload)
        self.assertEqual(set(routes), {"Carla Entregadora", "Diego Entregador"})
        carla = routes["Carla Entregadora"]
        self.assertEqual(carla["status"], "PLANNED")
        self.assertIn(extra, [stop["order_id"] for stop in carla["stops"]])
        self.assertEqual([stop["sequence"] for stop in carla["stops"]], list(range(1, len(carla["stops"]) + 1)))
        self.assertTrue(all(stop["order_status"] == "ASSIGNED" for stop in carla["stops"]))
        self.assertGreater(carla["total_distance_km"], 0)
        self.assertGreater(carla["estimated_duration_min"], 0)
        self.assertEqual(payload["waiting_orders"], 0)
        self.assertEqual(payload["run"]["purpose"], "ROUTE_GENERATION")
        self.assertEqual(payload["run"]["order_count"], 11)

    def test_routes_are_persisted_and_listed(self) -> None:
        generated = self.generate().json()
        listed = self.client.get("/routes", headers=self.attendant)
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual(
            sorted(route["id"] for route in listed.json()["routes"]),
            sorted(route["id"] for route in generated["routes"]),
        )
        runs = self.client.get("/optimizer/runs", headers=self.admin).json()
        self.assertEqual(runs[0]["id"], generated["run"]["id"])

    def test_route_distance_matches_the_sum_of_its_legs(self) -> None:
        self.assigned_order(latitude=-8.07, longitude=-34.91)
        self.assigned_order(latitude=-8.03, longitude=-34.92)
        carla = self.routes_by_courier(self.generate().json())["Carla Entregadora"]
        legs = sum(stop["distance_from_previous_km"] for stop in carla["stops"])
        self.assertLess(legs, carla["total_distance_km"])  # falta só a volta ao depósito

    def test_generating_again_replaces_planned_routes(self) -> None:
        self.generate()
        second = self.generate(mode="PARALLEL", workers=2).json()
        self.assertEqual(len(second["routes"]), 2)
        listed = self.client.get("/routes", headers=self.admin).json()["routes"]
        self.assertEqual(len(listed), 2)
        self.assertTrue(all(route["execution_mode"] == "PARALLEL" for route in listed))

    def test_offline_courier_is_left_out_with_reason(self) -> None:
        self.client.patch("/couriers/me/availability", headers=self.diego, json={"availability": "OFFLINE"})
        payload = self.generate().json()
        self.assertEqual(list(self.routes_by_courier(payload)), ["Carla Entregadora"])
        self.assertEqual(payload["skipped"][0]["courier"]["full_name"], "Diego Entregador")
        self.assertIn("fora de serviço", payload["skipped"][0]["reason"])

    def test_generation_requires_depot_location(self) -> None:
        with self.session_factory() as db:
            establishment = db.query(Establishment).first()
            establishment.depot_latitude = None
            establishment.depot_longitude = None
            db.commit()
        response = self.generate()
        self.assertEqual(response.status_code, 409)
        self.assertIn("ponto de saída", response.json()["detail"])

    def test_generation_without_assigned_orders_is_rejected(self) -> None:
        for order in self.client.get("/orders", headers=self.admin, params={"status": "ASSIGNED"}).json():
            self.client.patch(f"/orders/{order['id']}/status", headers=self.admin, json={"status": "CANCELLED"})
        response = self.generate()
        self.assertEqual(response.status_code, 409)
        self.assertIn("Não há pedidos atribuídos", response.json()["detail"])

    def test_gpu_mode_reports_when_unavailable(self) -> None:
        unavailable = GpuStatus(False, reason="Nenhuma GPU NVIDIA com CUDA foi encontrada nesta máquina.")
        with patch("app.optimizer.gpu.status", return_value=unavailable):
            response = self.generate(mode="GPU")
        self.assertEqual(response.status_code, 409)
        self.assertIn("GPU não está disponível", response.json()["detail"])

    def test_admin_sets_depot_location(self) -> None:
        body = {"depot_address": "Av. Conde da Boa Vista, 100 - Recife", "latitude": -8.06, "longitude": -34.89}
        self.assertEqual(self.client.put("/establishment/depot", headers=self.attendant, json=body).status_code, 403)
        response = self.client.put("/establishment/depot", headers=self.admin, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/routes", headers=self.admin).json()["depot"]["latitude"], -8.06)

    def test_courier_sees_and_starts_own_route(self) -> None:
        self.generate()
        mine = self.client.get("/routes/me", headers=self.courier).json()["route"]
        self.assertEqual(mine["courier"]["full_name"], "Carla Entregadora")

        diego_route = self.client.get("/routes/me", headers=self.diego).json()["route"]
        self.assertEqual(self.client.patch(f"/routes/{diego_route['id']}/start", headers=self.courier).status_code, 404)

        started = self.client.patch(f"/routes/{mine['id']}/start", headers=self.courier)
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["status"], "IN_PROGRESS")
        self.assertTrue(all(stop["order_status"] == "IN_ROUTE" for stop in started.json()["stops"]))
        order = self.client.get(f"/orders/{mine['stops'][0]['order_id']}", headers=self.courier).json()
        self.assertIn("rota", order["history"][-1]["note"])
        self.assertEqual(self.client.patch(f"/routes/{mine['id']}/start", headers=self.courier).status_code, 409)

    def test_route_in_progress_is_kept_when_generating_again(self) -> None:
        self.generate()
        route_id = self.client.get("/routes/me", headers=self.courier).json()["route"]["id"]
        self.client.patch(f"/routes/{route_id}/start", headers=self.courier)
        self.assigned_order(latitude=-8.07, longitude=-34.91)
        payload = self.generate().json()
        self.assertEqual(payload["skipped"][0]["courier"]["full_name"], "Carla Entregadora")
        self.assertIn("rota em andamento", payload["skipped"][0]["reason"])
        self.assertEqual(self.routes_by_courier(payload)["Carla Entregadora"]["id"], route_id)

    def test_route_completes_when_every_stop_is_delivered(self) -> None:
        self.generate()
        route = self.client.get("/routes/me", headers=self.diego).json()["route"]
        self.client.patch(f"/routes/{route['id']}/start", headers=self.diego)
        for stop in route["stops"]:
            response = self.client.patch(
                f"/orders/{stop['order_id']}/status", headers=self.diego, json={"status": "DELIVERED"}
            )
            self.assertEqual(response.status_code, 200, response.text)
        overview = self.client.get("/routes", headers=self.admin).json()
        diego = self.routes_by_courier(overview)["Diego Entregador"]
        self.assertEqual(diego["status"], "COMPLETED")
        self.assertTrue(all(stop["status"] == "COMPLETED" for stop in diego["stops"]))

    def test_changing_courier_discards_planned_route(self) -> None:
        self.generate()
        carla = self.client.get("/routes/me", headers=self.courier).json()["route"]
        order_id = carla["stops"][0]["order_id"]
        order = self.client.get(f"/orders/{order_id}", headers=self.admin).json()
        payload = self.order_payload(
            customer_id=order["customer"]["id"],
            delivery_address=order["delivery_address"],
            latitude=order["latitude"],
            longitude=order["longitude"],
            assigned_courier_id=self.courier_id("Diego Entregador"),
        )
        self.assertEqual(self.client.put(f"/orders/{order_id}", headers=self.admin, json=payload).status_code, 200)
        self.assertIsNone(self.client.get("/routes/me", headers=self.courier).json()["route"])
        overview = self.client.get("/routes", headers=self.admin).json()
        self.assertEqual(list(self.routes_by_courier(overview)), ["Diego Entregador"])
        self.assertEqual(overview["waiting_orders"], 5)  # o pedido trocado e os 4 que sobraram da rota descartada

    def test_order_in_started_route_cannot_be_deleted(self) -> None:
        self.generate()
        route = self.client.get("/routes/me", headers=self.courier).json()["route"]
        order_id = route["stops"][0]["order_id"]
        self.client.patch(f"/routes/{route['id']}/start", headers=self.courier)
        response = self.client.delete(f"/orders/{order_id}", headers=self.admin)
        self.assertEqual(response.status_code, 409)

    def test_order_in_planned_route_can_be_deleted(self) -> None:
        self.generate()
        route = self.client.get("/routes/me", headers=self.courier).json()["route"]
        response = self.client.delete(f"/orders/{route['stops'][0]['order_id']}", headers=self.admin)
        self.assertEqual(response.status_code, 204, response.text)
        self.assertIsNone(self.client.get("/routes/me", headers=self.courier).json()["route"])

    def test_profiles_are_enforced(self) -> None:
        self.assertEqual(self.generate(headers=self.courier).status_code, 403)
        self.assertEqual(self.client.get("/routes", headers=self.courier).status_code, 403)
        self.assertEqual(self.client.get("/routes/me", headers=self.admin).status_code, 403)
        self.assertEqual(self.client.post("/optimizer/benchmark", headers=self.attendant, json={}).status_code, 403)
        self.assertEqual(self.client.get("/optimizer/runs", headers=self.attendant).status_code, 403)


class BenchmarkTestCase(ApiTestCase):
    SMALL = {
        "source": "SYNTHETIC",
        "couriers": 4,
        "stops_per_courier": 15,
        "worker_counts": [2, 1],
        "include_gpu": False,
        "repetitions": 1,
    }

    def test_benchmark_compares_modes_and_records_metrics(self) -> None:
        response = self.client.post("/optimizer/benchmark", headers=self.admin, json=self.SMALL)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        rows = payload["rows"]
        self.assertEqual([(row["execution_mode"], row["worker_count"]) for row in rows],
                         [("SEQUENTIAL", 1), ("PARALLEL", 1), ("PARALLEL", 2)])
        self.assertEqual(payload["order_count"], 60)
        self.assertAlmostEqual(rows[0]["speedup"], 1.0)
        self.assertAlmostEqual(rows[0]["efficiency"], 1.0)
        self.assertTrue(all(row["same_routes"] for row in rows))
        self.assertAlmostEqual(rows[2]["efficiency"], rows[2]["speedup"] / 2, places=2)
        self.assertEqual(len({row["total_distance_km"] for row in rows}), 1)
        history = self.client.get("/optimizer/runs", headers=self.admin).json()
        self.assertEqual({run["run_group"] for run in history[:3]}, {payload["run_group"]})

    def test_benchmark_on_real_orders(self) -> None:
        body = {**self.SMALL, "source": "REAL"}
        response = self.client.post("/optimizer/benchmark", headers=self.admin, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["courier_count"], 2)
        self.assertTrue(all(row["input_source"] == "REAL" for row in response.json()["rows"]))

    def test_benchmark_size_is_limited(self) -> None:
        body = {**self.SMALL, "couriers": 64, "stops_per_courier": 500}
        self.assertEqual(self.client.post("/optimizer/benchmark", headers=self.admin, json=body).status_code, 422)

    def test_capabilities(self) -> None:
        response = self.client.get("/optimizer/capabilities", headers=self.attendant)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertGreaterEqual(response.json()["cpu_count"], 1)


if __name__ == "__main__":
    unittest.main()
