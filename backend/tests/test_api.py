"""Testes da API com banco SQLite em memória.

As regras de autenticação, perfis e CRUD não dependem de recursos exclusivos do
PostgreSQL, então os testes rodam sem precisar do banco da aplicação.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.seed import DEMO_PASSWORD, seed_demo_data  # noqa: E402

ORDER = {
    "customer_name": "Cliente Teste",
    "customer_phone": "(81) 90000-0000",
    "delivery_address": "Rua do Teste, 10 - Recife",
    "latitude": -8.05,
    "longitude": -34.9,
    "weight_kg": 2,
    "priority": 1,
}


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        with self.session_factory() as db:
            seed_demo_data(db)

        def override_get_db():
            with self.session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()

    def login(self, email: str, password: str = DEMO_PASSWORD) -> dict[str, str]:
        response = self.client.post("/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    @property
    def admin(self) -> dict[str, str]:
        return self.login("admin@rotacerta.com.br")

    @property
    def attendant(self) -> dict[str, str]:
        return self.login("atendente@rotacerta.com.br")

    @property
    def courier(self) -> dict[str, str]:
        return self.login("entregador@rotacerta.com.br")

    def courier_id(self) -> int:
        couriers = self.client.get("/couriers", headers=self.admin).json()
        return next(c["id"] for c in couriers if c["full_name"] == "Carla Entregadora")

    # Login e sessão

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

    # Cadastro de usuários

    def test_admin_creates_user_who_can_log_in(self) -> None:
        response = self.client.post(
            "/users",
            headers=self.admin,
            json={
                "full_name": "Nova Atendente",
                "email": "nova@rotacerta.com.br",
                "password": "senha-segura",
                "role": "ATTENDANT",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.login("nova@rotacerta.com.br", "senha-segura")

    def test_courier_requires_load_capacity(self) -> None:
        payload = {
            "full_name": "Entregador Sem Carga",
            "email": "semcarga@rotacerta.com.br",
            "password": "senha-segura",
            "role": "COURIER",
        }
        self.assertEqual(self.client.post("/users", headers=self.admin, json=payload).status_code, 422)
        payload["load_capacity_kg"] = 30
        created = self.client.post("/users", headers=self.admin, json=payload)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["courier"]["load_capacity_kg"], 30)

    def test_duplicate_email_is_rejected(self) -> None:
        response = self.client.post(
            "/users",
            headers=self.admin,
            json={
                "full_name": "Duplicado",
                "email": "atendente@rotacerta.com.br",
                "password": "senha-segura",
                "role": "ATTENDANT",
            },
        )
        self.assertEqual(response.status_code, 409)

    def test_deactivated_user_cannot_log_in(self) -> None:
        users = self.client.get("/users", headers=self.admin).json()
        attendant = next(u for u in users if u["role"] == "ATTENDANT")
        self.assertEqual(self.client.delete(f"/users/{attendant['id']}", headers=self.admin).status_code, 204)
        response = self.client.post(
            "/auth/login",
            json={"email": "atendente@rotacerta.com.br", "password": DEMO_PASSWORD},
        )
        self.assertEqual(response.status_code, 403)

    def test_register_creates_isolated_establishment(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={
                "establishment_name": "Mercado Novo",
                "depot_address": "Rua Nova, 1 - Recife",
                "full_name": "Dona do Mercado",
                "email": "dona@mercadonovo.com.br",
                "password": "senha-segura",
            },
        )
        self.assertEqual(response.status_code, 201)
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        self.assertEqual(self.client.get("/orders", headers=headers).json(), [])
        self.assertEqual(len(self.client.get("/users", headers=headers).json()), 1)

    # Controle de perfis

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
        self.assertEqual(self.client.post("/orders", headers=self.courier, json=ORDER).status_code, 403)

    def test_courier_advances_status_in_order(self) -> None:
        order = next(o for o in self.client.get("/orders", headers=self.courier).json() if o["status"] == "ASSIGNED")
        url = f"/orders/{order['id']}/status"
        skip = self.client.patch(url, headers=self.courier, json={"status": "DELIVERED"})
        self.assertEqual(skip.status_code, 409)
        self.assertEqual(self.client.patch(url, headers=self.courier, json={"status": "IN_ROUTE"}).json()["status"], "IN_ROUTE")
        self.assertEqual(self.client.patch(url, headers=self.courier, json={"status": "DELIVERED"}).json()["status"], "DELIVERED")

    # CRUD de pedidos

    def test_order_crud(self) -> None:
        created = self.client.post("/orders", headers=self.attendant, json=ORDER)
        self.assertEqual(created.status_code, 201, created.text)
        order = created.json()
        self.assertEqual(order["status"], "PENDING")
        self.assertEqual(order["customer"]["full_name"], "Cliente Teste")

        fetched = self.client.get(f"/orders/{order['id']}", headers=self.attendant)
        self.assertEqual(fetched.json()["delivery_address"], ORDER["delivery_address"])

        updated = self.client.put(
            f"/orders/{order['id']}",
            headers=self.attendant,
            json={**ORDER, "priority": 3, "assigned_courier_id": self.courier_id()},
        )
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["priority"], 3)
        self.assertEqual(updated.json()["status"], "ASSIGNED")

        self.assertEqual(self.client.delete(f"/orders/{order['id']}", headers=self.attendant).status_code, 403)
        self.assertEqual(self.client.delete(f"/orders/{order['id']}", headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get(f"/orders/{order['id']}", headers=self.admin).status_code, 404)

    def test_order_window_must_be_valid(self) -> None:
        payload = {**ORDER, "desired_start": "2026-09-28T15:00:00Z", "desired_end": "2026-09-28T14:00:00Z"}
        self.assertEqual(self.client.post("/orders", headers=self.admin, json=payload).status_code, 422)

    def test_delivered_order_cannot_be_edited(self) -> None:
        delivered = self.client.get("/orders?status=DELIVERED", headers=self.admin).json()[0]
        response = self.client.put(f"/orders/{delivered['id']}", headers=self.admin, json=ORDER)
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
