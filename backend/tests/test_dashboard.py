"""Testes do painel, dos relatórios e do histórico operacional integrado."""

from datetime import date, timedelta

from api_base import ApiTestCase


class DashboardTestCase(ApiTestCase):
    def test_summary_consolidates_seed_data(self) -> None:
        response = self.client.get("/dashboard/summary", headers=self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()

        self.assertEqual(payload["orders"]["total"], 14)
        self.assertEqual(payload["orders"]["pending"], 2)
        self.assertEqual(payload["orders"]["assigned"], 10)
        self.assertEqual(payload["orders"]["in_route"], 1)
        self.assertEqual(payload["orders"]["delivered"], 1)
        self.assertAlmostEqual(payload["orders"]["completion_rate"], 7.1)
        self.assertEqual(payload["couriers"]["total"], 2)
        self.assertEqual(payload["couriers"]["available"], 2)
        self.assertEqual(payload["routes"]["total"], 0)
        self.assertEqual(len(payload["recent_orders"]), 8)

    def test_generated_routes_are_reflected_in_summary(self) -> None:
        generated = self.client.post("/routes/generate", headers=self.admin, json={})
        self.assertEqual(generated.status_code, 200, generated.text)

        payload = self.client.get("/dashboard/summary", headers=self.attendant).json()
        self.assertEqual(payload["routes"]["total"], 2)
        self.assertEqual(payload["routes"]["planned"], 2)
        self.assertGreater(payload["routes"]["total_distance_km"], 0)
        self.assertEqual(payload["performance"]["run_count"], 1)
        self.assertEqual(payload["performance"]["latest_mode"], "SEQUENTIAL")

    def test_report_supports_status_and_period_filters(self) -> None:
        today = date.today().isoformat()
        delivered = self.client.get(
            "/dashboard/report",
            headers=self.admin,
            params={"start": today, "end": today, "status": "DELIVERED"},
        )
        self.assertEqual(delivered.status_code, 200, delivered.text)
        self.assertEqual(len(delivered.json()), 1)
        self.assertEqual(delivered.json()[0]["customer_name"], "Paulo Mendes")

        old_day = (date.today() - timedelta(days=30)).isoformat()
        empty = self.client.get(
            "/dashboard/report", headers=self.attendant, params={"start": old_day, "end": old_day}
        )
        self.assertEqual(empty.status_code, 200, empty.text)
        self.assertEqual(empty.json(), [])

    def test_report_supports_search_courier_and_priority_filters(self) -> None:
        by_address = self.client.get(
            "/dashboard/report", headers=self.admin, params={"q": "Boa Viagem"}
        )
        self.assertEqual(by_address.status_code, 200, by_address.text)
        self.assertEqual([row["customer_name"] for row in by_address.json()], ["Maria Silva"])

        carla = self.courier_id()
        filtered = self.client.get(
            "/dashboard/report",
            headers=self.attendant,
            params={"courier_id": carla, "priority": 1, "status": "ASSIGNED"},
        )
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertGreaterEqual(len(filtered.json()), 1)
        self.assertTrue(all(row["courier_name"] == "Carla Entregadora" for row in filtered.json()))
        self.assertTrue(all(row["priority"] == 1 for row in filtered.json()))
        self.assertTrue(all(row["status"] == "ASSIGNED" for row in filtered.json()))

    def test_operational_history_combines_order_events_and_optimizer_runs(self) -> None:
        initial = self.client.get("/dashboard/history", headers=self.admin)
        self.assertEqual(initial.status_code, 200, initial.text)
        self.assertGreater(len(initial.json()), 14)
        self.assertTrue(all(row["event_type"] == "ORDER_STATUS" for row in initial.json()))

        generated = self.client.post("/routes/generate", headers=self.admin, json={})
        self.assertEqual(generated.status_code, 200, generated.text)
        combined = self.client.get("/dashboard/history", headers=self.attendant)
        self.assertEqual(combined.status_code, 200, combined.text)
        self.assertTrue(any(row["event_type"] == "OPTIMIZATION" for row in combined.json()))

    def test_operational_history_supports_search_type_and_status_filters(self) -> None:
        delivered = self.client.get(
            "/dashboard/history",
            headers=self.admin,
            params={"type": "ORDER_STATUS", "status": "DELIVERED", "q": "Paulo"},
        )
        self.assertEqual(delivered.status_code, 200, delivered.text)
        self.assertEqual(len(delivered.json()), 1)
        self.assertEqual(delivered.json()[0]["customer_name"], "Paulo Mendes")
        self.assertEqual(delivered.json()[0]["actor_name"], "Diego Entregador")

    def test_period_validation(self) -> None:
        response = self.client.get(
            "/dashboard/summary",
            headers=self.admin,
            params={"start": "2026-10-10", "end": "2026-10-01"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("data final", response.json()["detail"])

        too_wide = self.client.get(
            "/dashboard/summary",
            headers=self.admin,
            params={"start": "2025-01-01", "end": "2026-10-01"},
        )
        self.assertEqual(too_wide.status_code, 422)
        self.assertIn("366 dias", too_wide.json()["detail"])

    def test_dashboard_is_restricted_to_staff(self) -> None:
        self.assertEqual(self.client.get("/dashboard/summary", headers=self.courier).status_code, 403)
        self.assertEqual(self.client.get("/dashboard/report", headers=self.courier).status_code, 403)
        self.assertEqual(self.client.get("/dashboard/history", headers=self.courier).status_code, 403)
