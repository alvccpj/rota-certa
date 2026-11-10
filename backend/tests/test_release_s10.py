"""Concorrência real no PostgreSQL; o schema de ApiTestCase é descartável."""

import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from api_base import ApiTestCase, TEST_DATABASE_URL
from app.main import app
from app.models import Courier, Customer, Establishment, Order, OrderStatusEvent


@unittest.skipUnless(TEST_DATABASE_URL, "Concorrência exige PostgreSQL e TEST_DATABASE_URL.")
class ReleaseConcurrencyTestCase(ApiTestCase):
    def setUp(self):
        super().setUp()
        with self.session_factory() as db:
            db.execute(delete(OrderStatusEvent))
            db.execute(delete(Order))
            self.establishment_id = db.scalar(select(Establishment.id))
            self.customer_id = db.scalar(select(Customer.id).order_by(Customer.id))
            for courier in db.scalars(select(Courier)):
                courier.load_capacity_kg = Decimal("10")
            db.commit()

    def simultaneous(self, count=8):
        headers = self.admin
        barrier = Barrier(count)

        def request(_):
            client = TestClient(app)
            try:
                barrier.wait(timeout=15)
                response = client.post("/orders/auto-assign", headers=headers)
                self.assertEqual(response.status_code, 200, response.text)
                return response.json()
            finally:
                client.close()

        with ThreadPoolExecutor(max_workers=count) as pool:
            return list(pool.map(request, range(count)))

    def test_concurrent_batches_preserve_capacity_and_single_history(self):
        for batch in range(3):
            with self.session_factory() as db:
                db.execute(delete(OrderStatusEvent))
                db.execute(delete(Order))
                for i in range(30):
                    db.add(Order(
                        establishment_id=self.establishment_id, customer_id=self.customer_id,
                        delivery_address=f"Rua da Concorrência, {i + 1} - Recife",
                        latitude=Decimal("-8.05"), longitude=Decimal("-34.9"),
                        weight_kg=Decimal("1"), priority=2, status="PENDING",
                    ))
                db.commit()
            responses = self.simultaneous()
            assigned_ids = [item["order_id"] for result in responses for item in result["assigned"]]
            self.assertEqual(len(assigned_ids), 20)
            self.assertEqual(len(set(assigned_ids)), 20)
            with self.session_factory() as db:
                loads = db.execute(select(Order.assigned_courier_id, func.sum(Order.weight_kg))
                    .where(Order.status == "ASSIGNED").group_by(Order.assigned_courier_id)).all()
                self.assertEqual(len(loads), 2)
                self.assertTrue(all(weight == Decimal("10") for _, weight in loads))
                histories = db.execute(select(OrderStatusEvent.order_id, func.count())
                    .group_by(OrderStatusEvent.order_id)).all()
                self.assertEqual(len(histories), 20)
                self.assertTrue(all(count == 1 for _, count in histories))
                self.assertEqual(db.scalar(select(func.count()).select_from(Order)
                    .where(Order.status == "PENDING")), 10)
            print(json.dumps({"rodada": batch + 1, "requisicoes_simultaneas": 8,
                "pedidos": 30, "atribuidos_unicos": 20, "pendentes": 10,
                "cargas_kg": [float(weight) for _, weight in loads],
                "eventos_sem_duplicacao": len(histories)}, ensure_ascii=False), flush=True)

    def test_concurrent_empty_queue_is_idempotent(self):
        self.assertTrue(all(result == {"assigned": [], "skipped": []}
                            for result in self.simultaneous()))
        with self.session_factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(OrderStatusEvent)), 0)


if __name__ == "__main__":
    unittest.main()
