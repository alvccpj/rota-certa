"""Testes do terceiro módulo: painel operacional e relatório integrado."""

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
