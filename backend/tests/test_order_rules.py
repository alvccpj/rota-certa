"""Testes das regras de atribuição e das validações do pedido."""

import unittest
from datetime import datetime, timedelta, timezone

from api_base import ApiTestCase
from app.models import Order


class OrderRulesTestCase(ApiTestCase):
    @property
    def diego(self) -> dict[str, str]:
        return self._cached("entregador2@rotacerta.com.br")

    def test_couriers_list_shows_current_load(self) -> None:
        carla = next(c for c in self.client.get("/couriers", headers=self.admin).json() if c["full_name"] == "Carla Entregadora")
        self.assertAlmostEqual(carla["active_load_kg"], 6.0)
        self.assertEqual(carla["active_orders"], 6)

    def test_offline_courier_cannot_receive_orders(self) -> None:
        response = self.client.patch("/couriers/me/availability", headers=self.diego, json={"availability": "OFFLINE"})
        self.assertEqual(response.status_code, 200, response.text)
        payload = self.order_payload(assigned_courier_id=self.courier_id("Diego Entregador"))
        created = self.client.post("/orders", headers=self.admin, json=payload)
        self.assertEqual(created.status_code, 422)
        self.assertIn("fora de serviço", created.json()["detail"])

    def test_courier_with_route_in_progress_cannot_go_offline(self) -> None:
        response = self.client.patch("/couriers/me/availability", headers=self.courier, json={"availability": "OFFLINE"})
        self.assertEqual(response.status_code, 409)

    def test_courier_capacity_is_respected(self) -> None:
        carla = self.courier_id()
        too_heavy = self.client.post("/orders", headers=self.admin, json=self.order_payload(weight_kg=19.5, assigned_courier_id=carla))
        self.assertEqual(too_heavy.status_code, 409)
        self.assertIn("25 kg", too_heavy.json()["detail"])
        fits = self.client.post("/orders", headers=self.admin, json=self.order_payload(weight_kg=19, assigned_courier_id=carla))
        self.assertEqual(fits.status_code, 201, fits.text)

    def test_delivery_must_be_inside_radius(self) -> None:
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(latitude=-8.9, longitude=-35.2))
        self.assertEqual(response.status_code, 422)
        self.assertIn("km do ponto de saída", response.json()["detail"])

    def test_window_cannot_end_in_the_past(self) -> None:
        payload = self.order_payload(desired_start="2020-01-01T10:00:00Z", desired_end="2020-01-01T12:00:00Z")
        response = self.client.post("/orders", headers=self.admin, json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("já passou", response.json()["detail"])

    def test_weight_has_upper_limit(self) -> None:
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(weight_kg=501))
        self.assertEqual(response.status_code, 422)

    def test_edit_rejects_new_expired_window_and_accepts_future_window(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        end = datetime.now(timezone.utc) - timedelta(days=1)
        payload = self.order_payload(desired_start=(end - timedelta(hours=1)).isoformat(), desired_end=end.isoformat())
        response = self.client.put(f"/orders/{order['id']}", headers=self.admin, json=payload)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIsNone(self.client.get(f"/orders/{order['id']}", headers=self.admin).json()["desired_end"])
        future = datetime.now(timezone.utc) + timedelta(days=1)
        payload.update(desired_start=future.isoformat(), desired_end=(future + timedelta(hours=1)).isoformat())
        self.assertEqual(self.client.put(f"/orders/{order['id']}", headers=self.admin, json=payload).status_code, 200)

    def test_edit_preserves_expired_window_but_rejects_changing_its_start(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        end = datetime.now(timezone.utc) - timedelta(days=1)
        start = end - timedelta(hours=1)
        with self.session_factory() as db:
            saved = db.get(Order, order["id"])
            saved.desired_start, saved.desired_end = start, end
            db.commit()
        # Mesmo instante com outro fuso deve contar como janela preservada.
        local = timezone(timedelta(hours=-3))
        payload = self.order_payload(priority=3, desired_start=start.astimezone(local).isoformat(),
                                     desired_end=end.astimezone(local).isoformat())
        response = self.client.put(f"/orders/{order['id']}", headers=self.admin, json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        payload["desired_start"] = (start - timedelta(hours=1)).isoformat()
        response = self.client.put(f"/orders/{order['id']}", headers=self.admin, json=payload)
        self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
