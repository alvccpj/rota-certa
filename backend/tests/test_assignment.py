"""Testes comportamentais da atribuição automática com API, banco e autenticação reais."""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select

from api_base import ApiTestCase
from app.main import app
from app.models import Courier, Customer, Establishment, Order, OrderStatusEvent, Route, User
from app.security import create_access_token


class AssignmentTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        with self.session_factory() as db:
            # Cada cenário começa com uma fila vazia, sem depender dos horários do seed.
            db.execute(delete(OrderStatusEvent))
            db.execute(delete(Order))
            self.establishment_id = db.scalar(select(Establishment.id))
            self.customer = db.scalar(select(Customer.id).order_by(Customer.id))
            couriers = list(db.scalars(select(Courier).order_by(Courier.id)))
            self.first, self.second = [courier.id for courier in couriers]
            for courier in couriers:
                courier.load_capacity_kg = Decimal("10")
            db.commit()

    def make_order(self, **changes) -> int:
        data = {
            "establishment_id": self.establishment_id,
            "customer_id": self.customer,
            "delivery_address": "Rua do Teste, 10 - Recife",
            "latitude": Decimal("-8.05"),
            "longitude": Decimal("-34.9"),
            "weight_kg": Decimal("1"),
            "priority": 2,
            "status": "PENDING",
        }
        data.update(changes)
        with self.session_factory() as db:
            order = Order(**data)
            db.add(order)
            db.commit()
            return order.id

    def set_courier(self, courier_id: int, **changes) -> None:
        with self.session_factory() as db:
            courier = db.get(Courier, courier_id)
            for key, value in changes.items():
                target = courier.user if key in ("active", "role") else courier
                setattr(target, key, value)
            db.commit()

    def assign(self, headers=None) -> dict:
        response = self.client.post("/orders/auto-assign", headers=headers or self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def assert_pending(self, *order_ids: int) -> None:
        with self.session_factory() as db:
            for order_id in order_ids:
                order = db.get(Order, order_id)
                self.assertEqual(order.status, "PENDING")
                self.assertIsNone(order.assigned_courier_id)
                self.assertEqual(order.history, [])

    def test_requires_authentication_and_staff_role(self) -> None:
        order_id = self.make_order()
        self.assertEqual(self.client.post("/orders/auto-assign").status_code, 401)
        response = self.client.post("/orders/auto-assign", headers=self.courier)
        self.assertEqual(response.status_code, 403, response.text)
        admin = self.admin
        with self.session_factory() as db:
            db.scalar(select(User).where(User.role == "ADMIN")).active = False
            db.commit()
        self.assertEqual(self.client.post("/orders/auto-assign", headers=admin).status_code, 401)
        self.assert_pending(order_id)

    def test_admin_and_attendant_persist_assignment_and_history_author(self) -> None:
        for headers, role in ((self.admin, "ADMIN"), (self.attendant, "ATTENDANT")):
            with self.subTest(role=role):
                order_id = self.make_order()
                payload = self.assign(headers)
                self.assertEqual(set(payload), {"assigned", "skipped"})
                self.assertEqual(payload["skipped"], [])
                self.assertEqual(len(payload["assigned"]), 1)
                item = payload["assigned"][0]
                self.assertEqual(set(item), {"order_id", "courier_id", "courier_name"})
                self.assertEqual(item["order_id"], order_id)
                with self.session_factory() as db:
                    order = db.get(Order, order_id)
                    actor = db.scalar(select(User).where(User.role == role))
                    self.assertEqual(order.status, "ASSIGNED")
                    self.assertEqual(order.assigned_courier_id, item["courier_id"])
                    self.assertEqual(order.courier.user.full_name, item["courier_name"])
                    self.assertEqual(len(order.history), 1)
                    self.assertEqual(order.history[0].status, "ASSIGNED")
                    self.assertEqual(order.history[0].changed_by, actor.id)
                    self.assertIn("automaticamente", order.history[0].note)

    def test_establishments_cannot_share_orders_or_couriers(self) -> None:
        with self.session_factory() as db:
            other = Establishment(
                name="Outro estabelecimento", depot_address="Rua Nova, 1",
                depot_latitude=Decimal("-8.05"), depot_longitude=Decimal("-34.9"),
            )
            db.add(other)
            db.flush()
            other_id = other.id
            owner = User(
                establishment_id=other_id, full_name="Outra administradora",
                email="outra@example.com", password_hash="unused", role="ADMIN",
            )
            courier_user = User(
                establishment_id=other_id, full_name="Outro entregador",
                email="outro@example.com", password_hash="unused", role="COURIER",
            )
            courier_user.courier = Courier(establishment_id=other_id, load_capacity_kg=Decimal("100"))
            customer = Customer(establishment_id=other_id, full_name="Outro cliente")
            db.add_all([owner, courier_user, customer])
            db.commit()
            other_headers = {"Authorization": f"Bearer {create_access_token(owner)}"}
            other_customer, other_courier = customer.id, courier_user.courier.id

        local_order = self.make_order()
        other_order = self.make_order(establishment_id=other_id, customer_id=other_customer)
        self.set_courier(self.first, availability="OFFLINE")
        self.set_courier(self.second, availability="OFFLINE")
        payload = self.assign()
        self.assertEqual(payload["assigned"], [])
        self.assertEqual([item["order_id"] for item in payload["skipped"]], [local_order])
        self.assert_pending(local_order, other_order)

        payload = self.assign(other_headers)
        self.assertEqual(payload["assigned"], [{
            "order_id": other_order, "courier_id": other_courier, "courier_name": "Outro entregador",
        }])
        self.assert_pending(local_order)
        self.set_courier(self.first, availability="AVAILABLE")
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], [local_order])
        self.assertEqual(payload["assigned"][0]["courier_id"], self.first)

    def test_capacity_counts_active_and_new_load_but_not_finished_orders(self) -> None:
        self.set_courier(self.second, availability="OFFLINE")
        self.make_order(status="ASSIGNED", assigned_courier_id=self.first, weight_kg=Decimal("7.5"))
        for status in ("DELIVERED", "CANCELLED"):
            self.make_order(status=status, assigned_courier_id=self.first, weight_kg=Decimal("100"))
        fits = self.make_order(weight_kg=Decimal("2.5"))
        overflow = self.make_order(weight_kg=Decimal("0.01"))
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], [fits])
        self.assertEqual([item["order_id"] for item in payload["skipped"]], [overflow])
        self.assertIn("capacidade", payload["skipped"][0]["reason"])
        self.assert_pending(overflow)
        with self.session_factory() as db:
            active = list(db.scalars(select(Order).where(
                Order.assigned_courier_id == self.first, Order.status.in_(("ASSIGNED", "IN_ROUTE")),
            )))
            self.assertEqual(sum(order.weight_kg for order in active), Decimal("10"))

    def test_chooses_lower_weight_then_id_and_updates_load_after_each_order(self) -> None:
        self.make_order(status="ASSIGNED", assigned_courier_id=self.first, weight_kg=Decimal("4"))
        # Mais pedidos, mas menor carga em kg: o segundo deve ser escolhido primeiro.
        for _ in range(2):
            self.make_order(status="ASSIGNED", assigned_courier_id=self.second, weight_kg=Decimal("0.5"))
        orders = [self.make_order(weight_kg=Decimal(weight)) for weight in ("2", "2", "1", "1")]
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], orders)
        self.assertEqual([item["courier_id"] for item in payload["assigned"]], [
            self.second, self.second, self.first, self.first,
        ])
        self.assertEqual(payload["skipped"], [])

    def test_uses_courier_with_capacity_even_if_another_has_less_load(self) -> None:
        self.set_courier(self.first, load_capacity_kg=Decimal("1"))
        self.make_order(status="ASSIGNED", assigned_courier_id=self.second, weight_kg=Decimal("2"))
        order_id = self.make_order(weight_kg=Decimal("2"))
        payload = self.assign()
        self.assertEqual(payload["assigned"][0]["order_id"], order_id)
        self.assertEqual(payload["assigned"][0]["courier_id"], self.second)

    def test_excludes_offline_busy_inactive_and_non_courier_users(self) -> None:
        cases = (
            {"availability": "OFFLINE"}, {"availability": "BUSY"},
            {"active": False}, {"role": "ATTENDANT"},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                self.set_courier(self.first, availability="AVAILABLE", active=True, role="COURIER")
                self.set_courier(self.first, **changes)
                order_id = self.make_order()
                payload = self.assign()
                self.assertEqual(payload["assigned"][0]["order_id"], order_id)
                self.assertEqual(payload["assigned"][0]["courier_id"], self.second)

    def test_available_courier_with_in_progress_route_is_busy(self) -> None:
        with self.session_factory() as db:
            db.add(Route(
                establishment_id=self.establishment_id, courier_id=self.first,
                route_date=(datetime.now(timezone.utc) - timedelta(days=1)).date(),
                status="IN_PROGRESS", algorithm="test", execution_mode="SEQUENTIAL",
            ))
            db.commit()
        order_id = self.make_order()
        payload = self.assign()
        self.assertEqual(payload["assigned"][0]["order_id"], order_id)
        self.assertEqual(payload["assigned"][0]["courier_id"], self.second)

    def test_in_route_order_without_route_also_makes_courier_busy(self) -> None:
        active = self.make_order(status="IN_ROUTE", assigned_courier_id=self.first)
        pending = self.make_order()
        with self.session_factory() as db:
            self.assertEqual(list(db.scalars(select(Route.id))), [])
        payload = self.assign()
        self.assertEqual(payload["assigned"][0]["order_id"], pending)
        self.assertEqual(payload["assigned"][0]["courier_id"], self.second)
        with self.session_factory() as db:
            order = db.get(Order, active)
            self.assertEqual((order.status, order.assigned_courier_id), ("IN_ROUTE", self.first))
            self.assertEqual(order.history, [])

    def test_planned_and_finished_routes_do_not_make_courier_busy(self) -> None:
        self.set_courier(self.second, availability="OFFLINE")
        with self.session_factory() as db:
            for status in ("PLANNED", "COMPLETED", "CANCELLED"):
                db.add(Route(
                    establishment_id=self.establishment_id, courier_id=self.first,
                    route_date=datetime.now(timezone.utc).date(), status=status,
                    algorithm="test", execution_mode="SEQUENTIAL",
                ))
            db.commit()
        self.make_order()
        self.assertEqual(self.assign()["assigned"][0]["courier_id"], self.first)

    def test_no_eligible_courier_returns_reason_without_changes(self) -> None:
        self.set_courier(self.first, availability="OFFLINE")
        self.make_order(status="IN_ROUTE", assigned_courier_id=self.second)
        pending = self.make_order()
        payload = self.assign()
        self.assertEqual(payload["assigned"], [])
        self.assertEqual(len(payload["skipped"]), 1)
        self.assertEqual(payload["skipped"][0]["order_id"], pending)
        self.assertIn("disponível", payload["skipped"][0]["reason"])
        self.assert_pending(pending)

    def test_priority_then_deadline_then_id_with_no_deadline_last(self) -> None:
        end = datetime.now(timezone.utc) + timedelta(days=2)
        low = self.make_order(priority=3, desired_end=end)
        no_deadline = self.make_order(priority=2)
        later = self.make_order(priority=2, desired_end=end + timedelta(hours=1))
        early = self.make_order(priority=2, desired_end=end)
        same_deadline = self.make_order(priority=2, desired_end=end)
        high = self.make_order(priority=1, desired_end=end + timedelta(days=1))
        self.set_courier(self.first, load_capacity_kg=Decimal("5"))
        self.set_courier(self.second, availability="OFFLINE")
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], [
            high, early, same_deadline, later, no_deadline,
        ])
        self.assertEqual([item["order_id"] for item in payload["skipped"]], [low])
        self.assert_pending(low)

    def test_expired_window_and_outside_radius_are_skipped_but_batch_continues(self) -> None:
        expired = self.make_order(priority=1, desired_end=datetime.now(timezone.utc) - timedelta(days=1))
        far = self.make_order(priority=1, latitude=Decimal("-8.9"), longitude=Decimal("-35.2"))
        valid = self.make_order()
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], [valid])
        reasons = {item["order_id"]: item["reason"] for item in payload["skipped"]}
        self.assertEqual(set(reasons), {expired, far})
        self.assertIn("já passou", reasons[expired])
        self.assertIn("limite de entrega", reasons[far])
        self.assert_pending(expired, far)

    def test_missing_depot_prevents_assignment_without_radius_validation(self) -> None:
        pending = self.make_order()
        with self.session_factory() as db:
            db.get(Establishment, self.establishment_id).depot_latitude = None
            db.commit()
        response = self.client.post("/orders/auto-assign", headers=self.admin)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("ponto de saída", response.json()["detail"])
        self.assert_pending(pending)

    def test_repeat_does_not_reassign_or_duplicate_history_and_preserves_existing_orders(self) -> None:
        existing = [
            (self.make_order(status=status, assigned_courier_id=self.first), status)
            for status in ("ASSIGNED", "IN_ROUTE", "PENDING", "DELIVERED", "CANCELLED")
        ]
        pending = self.make_order()
        payload = self.assign()
        self.assertEqual([item["order_id"] for item in payload["assigned"]], [pending])
        self.assertEqual(self.assign(self.attendant), {"assigned": [], "skipped": []})
        with self.session_factory() as db:
            for order_id, status in existing:
                order = db.get(Order, order_id)
                self.assertEqual((order.status, order.assigned_courier_id), (status, self.first))
                self.assertEqual(order.history, [])
            order = db.get(Order, pending)
            self.assertEqual(order.assigned_courier_id, payload["assigned"][0]["courier_id"])
            self.assertEqual(len(order.history), 1)

    def test_empty_queue_and_static_route_registration(self) -> None:
        self.assertEqual(self.assign(), {"assigned": [], "skipped": []})
        paths = [route.path for route in app.routes]
        self.assertLess(paths.index("/orders/auto-assign"), paths.index("/orders/{order_id}"))


if __name__ == "__main__":
    unittest.main()
