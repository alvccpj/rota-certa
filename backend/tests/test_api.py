"""Testes de login, cadastro de usuários, perfis e CRUD de pedidos."""

import unittest

from api_base import NEW_PASSWORD, ApiTestCase

from app.models import User
from app.seed import DEMO_PASSWORD


class AuthTestCase(ApiTestCase):
    def test_login_returns_token_and_profile(self) -> None:
        response = self.client.post(
            "/auth/login",
            json={"email": "ADMIN@rotacerta.com.br", "password": DEMO_PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "ADMIN")
        me = self.client.get("/auth/me", headers=self.admin)
        self.assertEqual(me.json()["email"], "admin@rotacerta.com.br")

    def test_login_rejects_wrong_password(self) -> None:
        response = self.client.post(
            "/auth/login",
            json={"email": "admin@rotacerta.com.br", "password": "senha-errada"},
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_routes_require_token(self) -> None:
        self.assertEqual(self.client.get("/orders").status_code, 401)
        invalid = {"Authorization": "Bearer token-invalido"}
        self.assertEqual(self.client.get("/orders", headers=invalid).status_code, 401)

    def test_password_is_stored_as_hash(self) -> None:
        with self.session_factory() as db:
            user = db.query(User).filter_by(email="admin@rotacerta.com.br").one()
        self.assertNotEqual(user.password_hash, DEMO_PASSWORD)
        self.assertTrue(user.password_hash.startswith("$argon2"))

    def test_register_creates_isolated_establishment(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={
                "establishment_name": "Mercado Novo",
                "depot_address": "Rua Nova, 1 - Recife",
                "full_name": "Dona do Mercado",
                "email": "dona@mercadonovo.com.br",
                "password": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        self.assertEqual(self.client.get("/orders", headers=headers).json(), [])
        self.assertEqual(len(self.client.get("/users", headers=headers).json()), 1)
        self.assertEqual(self.client.get("/customers", headers=headers).json(), [])


class UsersTestCase(ApiTestCase):
    def new_user(self, **changes) -> dict:
        payload = {
            "full_name": "Nova Atendente",
            "email": "nova@rotacerta.com.br",
            "password": NEW_PASSWORD,
            "role": "ATTENDANT",
        }
        payload.update(changes)
        return payload

    def test_admin_creates_user_who_can_log_in(self) -> None:
        response = self.client.post("/users", headers=self.admin, json=self.new_user())
        self.assertEqual(response.status_code, 201, response.text)
        self.login("nova@rotacerta.com.br", NEW_PASSWORD)

    def test_password_needs_letters_and_numbers(self) -> None:
        response = self.client.post("/users", headers=self.admin, json=self.new_user(password="somenteletras"))
        self.assertEqual(response.status_code, 422)
        self.assertIn("letras e números", response.text)

    def test_courier_requires_load_capacity(self) -> None:
        payload = self.new_user(email="semcarga@rotacerta.com.br", role="COURIER")
        self.assertEqual(self.client.post("/users", headers=self.admin, json=payload).status_code, 422)
        payload["load_capacity_kg"] = 30
        created = self.client.post("/users", headers=self.admin, json=payload)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["courier"]["load_capacity_kg"], 30)

    def test_duplicate_email_is_rejected(self) -> None:
        payload = self.new_user(email="atendente@rotacerta.com.br")
        self.assertEqual(self.client.post("/users", headers=self.admin, json=payload).status_code, 409)

    def test_deactivated_user_cannot_log_in(self) -> None:
        users = self.client.get("/users", headers=self.admin).json()
        attendant = next(u for u in users if u["role"] == "ATTENDANT")
        self.assertEqual(self.client.delete(f"/users/{attendant['id']}", headers=self.admin).status_code, 204)
        response = self.client.post(
            "/auth/login",
            json={"email": "atendente@rotacerta.com.br", "password": DEMO_PASSWORD},
        )
        self.assertEqual(response.status_code, 403)


class ProfilesTestCase(ApiTestCase):
    def test_only_admin_manages_users(self) -> None:
        self.assertEqual(self.client.get("/users", headers=self.attendant).status_code, 403)
        self.assertEqual(self.client.get("/users", headers=self.courier).status_code, 403)
        self.assertEqual(self.client.get("/users", headers=self.admin).status_code, 200)

    def test_courier_sees_only_own_orders(self) -> None:
        all_orders = self.client.get("/orders", headers=self.admin).json()
        own_orders = self.client.get("/orders", headers=self.courier).json()
        self.assertEqual(len(all_orders), 6)
        self.assertEqual(len(own_orders), 2)
        self.assertTrue(all(o["assigned_courier"]["full_name"] == "Carla Entregadora" for o in own_orders))

    def test_courier_cannot_create_orders(self) -> None:
        payload = self.order_payload()
        self.assertEqual(self.client.post("/orders", headers=self.courier, json=payload).status_code, 403)

    def test_courier_advances_status_in_order(self) -> None:
        order = next(o for o in self.client.get("/orders", headers=self.courier).json() if o["status"] == "ASSIGNED")
        url = f"/orders/{order['id']}/status"
        skip = self.client.patch(url, headers=self.courier, json={"status": "DELIVERED"})
        self.assertEqual(skip.status_code, 409)
        self.assertEqual(self.client.patch(url, headers=self.courier, json={"status": "IN_ROUTE"}).json()["status"], "IN_ROUTE")
        self.assertEqual(self.client.patch(url, headers=self.courier, json={"status": "DELIVERED"}).json()["status"], "DELIVERED")


class OrdersTestCase(ApiTestCase):
    def test_order_crud(self) -> None:
        payload = self.order_payload()
        created = self.client.post("/orders", headers=self.attendant, json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        order = created.json()
        self.assertEqual(order["status"], "PENDING")
        self.assertEqual(order["customer"]["full_name"], "Cliente Teste")

        fetched = self.client.get(f"/orders/{order['id']}", headers=self.attendant)
        self.assertEqual(fetched.json()["delivery_address"], payload["delivery_address"])

        updated = self.client.put(
            f"/orders/{order['id']}",
            headers=self.attendant,
            json={**payload, "priority": 3, "assigned_courier_id": self.courier_id("Diego Entregador")},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["priority"], 3)
        self.assertEqual(updated.json()["status"], "ASSIGNED")

        self.assertEqual(self.client.delete(f"/orders/{order['id']}", headers=self.attendant).status_code, 403)
        self.assertEqual(self.client.delete(f"/orders/{order['id']}", headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get(f"/orders/{order['id']}", headers=self.admin).status_code, 404)

    def test_order_requires_customer_from_establishment(self) -> None:
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(customer_id=9999))
        self.assertEqual(response.status_code, 422)

    def test_order_window_must_be_valid(self) -> None:
        payload = self.order_payload(desired_start="2030-09-28T15:00:00Z", desired_end="2030-09-28T14:00:00Z")
        self.assertEqual(self.client.post("/orders", headers=self.admin, json=payload).status_code, 422)

    def test_delivered_order_cannot_be_edited(self) -> None:
        delivered = self.client.get("/orders?status=DELIVERED", headers=self.admin).json()[0]
        response = self.client.put(f"/orders/{delivered['id']}", headers=self.admin, json=self.order_payload())
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
