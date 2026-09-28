"""Testes do histórico de situação dos pedidos."""

import unittest

from api_base import ApiTestCase

from app.models import OrderStatusEvent


class HistoryTestCase(ApiTestCase):
    def history(self, order_id: int) -> list[dict]:
        response = self.client.get(f"/orders/{order_id}", headers=self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["history"]

    def test_full_lifecycle_is_recorded(self) -> None:
        created = self.client.post("/orders", headers=self.attendant, json=self.order_payload()).json()
        self.client.put(
            f"/orders/{created['id']}",
            headers=self.attendant,
            json=self.order_payload(assigned_courier_id=self.courier_id()),
        )
        url = f"/orders/{created['id']}/status"
        self.client.patch(url, headers=self.courier, json={"status": "IN_ROUTE"})
        self.client.patch(url, headers=self.courier, json={"status": "DELIVERED"})

        history = self.history(created["id"])
        self.assertEqual([event["status"] for event in history], ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED"])
        self.assertEqual(history[0]["changed_by"], "Bruno Atendente")
        self.assertEqual(history[1]["note"], "Atribuído a Carla Entregadora")
        self.assertEqual(history[3]["changed_by"], "Carla Entregadora")

    def test_cancellation_keeps_the_reason(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        response = self.client.patch(
            f"/orders/{order['id']}/status",
            headers=self.admin,
            json={"status": "CANCELLED", "note": "Cliente desistiu da compra"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.history(order["id"])[-1]["note"], "Cliente desistiu da compra")

    def test_same_status_is_rejected(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        response = self.client.patch(f"/orders/{order['id']}/status", headers=self.admin, json={"status": "PENDING"})
        self.assertEqual(response.status_code, 409)

    def test_demo_orders_have_consistent_history(self) -> None:
        delivered = self.client.get("/orders?status=DELIVERED", headers=self.admin).json()[0]
        statuses = [event["status"] for event in self.history(delivered["id"])]
        self.assertEqual(statuses, ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED"])

    def test_deleting_order_removes_its_history(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        self.assertEqual(self.client.delete(f"/orders/{order['id']}", headers=self.admin).status_code, 204)
        with self.session_factory() as db:
            remaining = db.query(OrderStatusEvent).filter_by(order_id=order["id"]).count()
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()
