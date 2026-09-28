"""Base dos testes da API com banco SQLite em memória.

As regras de autenticação, perfis e cadastros não dependem de recursos
exclusivos do PostgreSQL, então os testes rodam sem o banco da aplicação.
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
from app.seed import DEMO_PASSWORD, seed_demo_data  # noqa: E402

NEW_PASSWORD = "senhaSegura123"


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
        self._tokens: dict[str, dict[str, str]] = {}

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()

    def login(self, email: str, password: str = DEMO_PASSWORD) -> dict[str, str]:
        response = self.client.post("/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def _cached(self, email: str) -> dict[str, str]:
        if email not in self._tokens:
            self._tokens[email] = self.login(email)
        return self._tokens[email]

    @property
    def admin(self) -> dict[str, str]:
        return self._cached("admin@rotacerta.com.br")

    @property
    def attendant(self) -> dict[str, str]:
        return self._cached("atendente@rotacerta.com.br")

    @property
    def courier(self) -> dict[str, str]:
        return self._cached("entregador@rotacerta.com.br")

    def courier_id(self, name: str = "Carla Entregadora") -> int:
        couriers = self.client.get("/couriers", headers=self.admin).json()
        return next(c["id"] for c in couriers if c["full_name"] == name)

    def customer_id(self, name: str = "Cliente Teste") -> int:
        existing = self.client.get("/customers", headers=self.admin, params={"q": name}).json()
        if existing:
            return existing[0]["id"]
        response = self.client.post(
            "/customers",
            headers=self.admin,
            json={"full_name": name, "phone": "(81) 90000-0000"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def order_payload(self, **changes) -> dict:
        payload = {
            "customer_id": changes.pop("customer_id", None) or self.customer_id(),
            "delivery_address": "Rua do Teste, 10 - Recife",
            "latitude": -8.05,
            "longitude": -34.9,
            "weight_kg": 2,
            "priority": 1,
        }
        payload.update(changes)
        return payload
