"""Sprint 08: permissões por perfil, isolamento e integridade das entregas."""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt

from api_base import NEW_PASSWORD, ApiTestCase
from app import planning
from app.config import settings
from app.models import Courier, Customer, Establishment, Order, Route, RouteStop, User
from app.security import create_access_token


class PermissionsS08TestCase(ApiTestCase):
    def roles(self):
        return {"ADMIN": self.admin, "ATTENDANT": self.attendant, "COURIER": self.courier}

    def user_body(self, user, **changes):
        return {**{key: user[key] for key in ("full_name", "email", "role", "active")}, **changes}

    def order_body(self, order, **changes):
        body = {key: order[key] for key in (
            "delivery_address", "latitude", "longitude", "weight_kg", "priority", "desired_start", "desired_end"
        )}
        body.update(customer_id=order["customer"]["id"],
                    assigned_courier_id=order["assigned_courier"]["id"] if order["assigned_courier"] else None)
        return {**body, **changes}

    def create_order(self, **changes):
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(**changes))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def detail(self, order_id):
        response = self.client.get(f"/orders/{order_id}", headers=self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def generate(self, headers=None):
        response = self.client.post("/routes/generate", headers=headers or self.admin, json={})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["routes"]

    def start(self, route, headers=None):
        response = self.client.patch(f"/routes/{route['id']}/start", headers=headers or self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def depot_body(self, **changes):
        depot = self.client.get("/establishment/depot", headers=self.admin).json()
        return {"depot_address": depot["address"], "latitude": depot["latitude"],
                "longitude": depot["longitude"], **changes}

    def foreign_tenant(self, route_status="PLANNED"):
        """IDs reais de outro estabelecimento, sem substituir dependências de autorização."""
        with self.session_factory() as db:
            password_hash = db.query(User).first().password_hash
            establishment = Establishment(name="Outro estabelecimento", depot_address="Rua Externa, 10",
                                          depot_latitude=Decimal("-8.059300"), depot_longitude=Decimal("-34.881600"))
            db.add(establishment)
            db.flush()
            admin = User(establishment=establishment, full_name="Admin Externo", email="externo@example.com",
                         password_hash=password_hash, role="ADMIN")
            courier_user = User(establishment=establishment, full_name="Entregador Externo",
                                email="entregador.externo@example.com", password_hash=password_hash, role="COURIER")
            courier_user.courier = Courier(establishment_id=establishment.id, load_capacity_kg=Decimal("30"))
            customer = Customer(establishment_id=establishment.id, full_name="Cliente Externo")
            order = Order(establishment_id=establishment.id, customer=customer, courier=courier_user.courier,
                          delivery_address="Rua Externa, 20", latitude=Decimal("-8.05"),
                          longitude=Decimal("-34.9"), weight_kg=Decimal("2"),
                          status="IN_ROUTE" if route_status == "IN_PROGRESS" else "ASSIGNED")
            route = Route(establishment_id=establishment.id, courier=courier_user.courier,
                          route_date=planning.local_today(), status=route_status, algorithm="NEAREST_NEIGHBOR_2OPT",
                          execution_mode="SEQUENTIAL", stops=[RouteStop(order=order, stop_sequence=1)])
            db.add_all([admin, courier_user, route])
            db.commit()
            return {"user": admin.id, "courier": courier_user.courier.id, "customer": customer.id,
                    "order": order.id, "route": route.id,
                    "headers": {"Authorization": f"Bearer {create_access_token(admin)}"}}

    def test_read_permission_matrix(self):
        own_order = self.client.get("/orders", headers=self.courier).json()[0]
        admin_id = self.client.get("/auth/me", headers=self.admin).json()["id"]
        rows = {
            "/auth/me": {"ADMIN", "ATTENDANT", "COURIER"},
            "/orders": {"ADMIN", "ATTENDANT", "COURIER"},
            f"/orders/{own_order['id']}": {"ADMIN", "ATTENDANT", "COURIER"},
            "/users": {"ADMIN"}, f"/users/{admin_id}": {"ADMIN"},
            "/couriers": {"ADMIN", "ATTENDANT"}, "/customers": {"ADMIN", "ATTENDANT"},
            "/establishment/depot": {"ADMIN", "ATTENDANT"}, "/routes": {"ADMIN", "ATTENDANT"},
            "/routes/me": {"COURIER"}, "/optimizer/runs": {"ADMIN"},
            "/dashboard/summary": {"ADMIN", "ATTENDANT"},
            "/dashboard/report": {"ADMIN", "ATTENDANT"}, "/dashboard/history": {"ADMIN", "ATTENDANT"},
        }
        for path, allowed in rows.items():
            for role, headers in self.roles().items():
                with self.subTest(path=path, role=role):
                    response = self.client.get(path, headers=headers)
                    self.assertEqual(response.status_code, 200 if role in allowed else 403, response.text)

    def test_order_write_permission_matrix(self):
        for role, headers in self.roles().items():
            with self.subTest(role=role):
                body = self.order_payload()
                response = self.client.post("/orders", headers=headers, json=body)
                self.assertEqual(response.status_code, 403 if role == "COURIER" else 201, response.text)
                order = self.create_order()
                url = f"/orders/{order['id']}"
                before = self.detail(order["id"])
                updated = self.client.put(url, headers=headers, json={**body, "priority": 3})
                self.assertEqual(updated.status_code, 403 if role == "COURIER" else 200, updated.text)
                if role == "COURIER":
                    self.assertEqual(self.detail(order["id"]), before)
                deleted = self.client.delete(url, headers=headers)
                self.assertEqual(deleted.status_code, 204 if role == "ADMIN" else 403, deleted.text)

    def test_user_depot_availability_and_generation_write_matrix(self):
        for role, headers in self.roles().items():
            with self.subTest(role=role):
                body = {"full_name": "Usuário Matriz", "email": f"matriz.{role.lower()}@example.com",
                        "password": NEW_PASSWORD, "role": "ATTENDANT"}
                response = self.client.post("/users", headers=headers, json=body)
                self.assertEqual(response.status_code, 201 if role == "ADMIN" else 403, response.text)
                target = self.client.post("/users", headers=self.admin, json={
                    **body, "email": f"alvo.{role.lower()}@example.com",
                }).json()
                url = f"/users/{target['id']}"
                response = self.client.put(url, headers=headers, json=self.user_body(target, full_name="Nome Alterado"))
                self.assertEqual(response.status_code, 200 if role == "ADMIN" else 403, response.text)
                response = self.client.delete(url, headers=headers)
                self.assertEqual(response.status_code, 204 if role == "ADMIN" else 403, response.text)
                response = self.client.put("/establishment/depot", headers=headers, json=self.depot_body())
                self.assertEqual(response.status_code, 200 if role == "ADMIN" else 403, response.text)
                response = self.client.patch("/couriers/me/availability", headers=headers,
                                             json={"availability": "AVAILABLE"})
                self.assertEqual(response.status_code, 200 if role == "COURIER" else 403, response.text)
                response = self.client.post("/routes/generate", headers=headers, json={})
                self.assertEqual(response.status_code, 403 if role == "COURIER" else 200, response.text)

    def test_every_role_can_start_an_authorized_route(self):
        for role, headers in self.roles().items():
            with self.subTest(role=role):
                routes = self.generate()
                route = next(r for r in routes if r["courier"]["id"] == self.courier_id() and r["status"] == "PLANNED")
                started = self.start(route, headers)
                self.assertEqual(started["status"], "IN_PROGRESS")
                for stop in started["stops"]:
                    response = self.client.patch(f"/orders/{stop['order_id']}/status", headers=headers,
                                                 json={"status": "DELIVERED"})
                    self.assertEqual(response.status_code, 200, response.text)
                self.create_order(assigned_courier_id=self.courier_id())

    def test_cross_tenant_direct_ids_are_hidden_for_every_role(self):
        foreign = self.foreign_tenant()
        body = self.order_payload()
        user = self.client.get("/auth/me", headers=self.admin).json()
        rows = [
            ("GET", f"/orders/{foreign['order']}", None, {"ADMIN", "ATTENDANT", "COURIER"}),
            ("PUT", f"/orders/{foreign['order']}", body, {"ADMIN", "ATTENDANT"}),
            ("DELETE", f"/orders/{foreign['order']}", None, {"ADMIN"}),
            ("PATCH", f"/orders/{foreign['order']}/status", {"status": "IN_ROUTE"}, {"ADMIN", "ATTENDANT", "COURIER"}),
            ("GET", f"/users/{foreign['user']}", None, {"ADMIN"}),
            ("PUT", f"/users/{foreign['user']}", self.user_body(user), {"ADMIN"}),
            ("DELETE", f"/users/{foreign['user']}", None, {"ADMIN"}),
            ("GET", f"/customers/{foreign['customer']}", None, {"ADMIN", "ATTENDANT"}),
            ("PUT", f"/customers/{foreign['customer']}", {"full_name": "Nome Indevido"}, {"ADMIN", "ATTENDANT"}),
            ("DELETE", f"/customers/{foreign['customer']}", None, {"ADMIN"}),
            ("PATCH", f"/routes/{foreign['route']}/start", None, {"ADMIN", "ATTENDANT", "COURIER"}),
        ]
        for method, path, payload, allowed in rows:
            for role, headers in self.roles().items():
                with self.subTest(method=method, path=path, role=role):
                    response = self.client.request(method, path, headers=headers, json=payload)
                    self.assertEqual(response.status_code, 404 if role in allowed else 403, response.text)
        with self.session_factory() as db:
            self.assertTrue(db.get(User, foreign["user"]).active)
            self.assertEqual(db.get(Order, foreign["order"]).status, "ASSIGNED")
            self.assertEqual(db.get(Route, foreign["route"]).status, "PLANNED")
            self.assertEqual(db.get(Customer, foreign["customer"]).full_name, "Cliente Externo")

    def test_cross_tenant_foreign_keys_rejected_on_create_and_update(self):
        foreign = self.foreign_tenant()
        order = self.create_order()
        before = self.detail(order["id"])
        for headers in (self.admin, self.attendant):
            for change in ({"customer_id": foreign["customer"]}, {"assigned_courier_id": foreign["courier"]}):
                for method, path in (("POST", "/orders"), ("PUT", f"/orders/{order['id']}")):
                    with self.subTest(method=method, change=change):
                        response = self.client.request(method, path, headers=headers, json=self.order_body(order, **change))
                        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.detail(order["id"]), before)

    def test_lists_are_tenant_scoped(self):
        foreign = self.foreign_tenant()
        for headers in (self.admin, self.attendant):
            for path, foreign_id in (("/orders", foreign["order"]), ("/couriers", foreign["courier"]),
                                     ("/customers", foreign["customer"])):
                self.assertNotIn(foreign_id, [item["id"] for item in self.client.get(path, headers=headers).json()])
            routes = self.client.get("/routes", headers=headers).json()["routes"]
            self.assertNotIn(foreign["route"], [route["id"] for route in routes])
        self.assertNotIn(foreign["user"], [u["id"] for u in self.client.get("/users", headers=self.admin).json()])

    def test_courier_cannot_access_unassigned_or_other_courier_orders_and_routes(self):
        own_id = self.courier_id()
        orders = self.client.get("/orders", headers=self.admin).json()
        for order in orders:
            if order["assigned_courier"] and order["assigned_courier"]["id"] == own_id:
                continue
            with self.subTest(order=order["id"]):
                self.assertEqual(self.client.get(f"/orders/{order['id']}", headers=self.courier).status_code, 404)
                response = self.client.patch(f"/orders/{order['id']}/status", headers=self.courier,
                                             json={"status": "IN_ROUTE"})
                self.assertEqual(response.status_code, 404, response.text)
        other = next(r for r in self.generate() if r["courier"]["id"] != own_id)
        self.assertEqual(self.client.patch(f"/routes/{other['id']}/start", headers=self.courier).status_code, 404)

    def test_courier_without_courier_record_cannot_see_unassigned_orders(self):
        headers = self.attendant
        with self.session_factory() as db:
            user = db.query(User).filter_by(email="atendente@rotacerta.com.br").one()
            user.role = "COURIER"
            db.commit()
        pending = self.client.get("/orders?status=PENDING", headers=self.admin).json()[0]
        for path in ("/orders", "/orders?status=PENDING"):
            response = self.client.get(path, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), [])
        self.assertEqual(self.client.get(f"/orders/{pending['id']}", headers=headers).status_code, 404)
        response = self.client.patch(f"/orders/{pending['id']}/status", headers=headers, json={"status": "IN_ROUTE"})
        self.assertEqual(response.status_code, 404, response.text)
        self.assertIsNone(self.client.get("/routes/me", headers=headers).json()["route"])

    def test_admin_cannot_delete_deactivate_or_demote_self(self):
        admin = self.client.get("/auth/me", headers=self.admin).json()
        url = f"/users/{admin['id']}"
        self.assertEqual(self.client.delete(url, headers=self.admin).status_code, 409)
        for change in ({"active": False}, {"role": "ATTENDANT"}, {"role": "COURIER", "load_capacity_kg": 30}):
            response = self.client.put(url, headers=self.admin, json=self.user_body(admin, **change))
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(self.client.get("/auth/me", headers=self.admin).json(), admin)

    def test_missing_invalid_expired_and_disabled_tokens_are_rejected(self):
        disabled = self.attendant
        user = self.client.get("/auth/me", headers=disabled).json()
        self.assertEqual(self.client.delete(f"/users/{user['id']}", headers=self.admin).status_code, 204)
        admin = self.client.get("/auth/me", headers=self.admin).json()
        expired = jwt.encode({"sub": str(admin["id"]), "role": "ADMIN",
                              "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                             settings.jwt_secret, algorithm="HS256")
        order = self.create_order()
        rows = [
            ("GET", path, None) for path in ("/auth/me", "/users", f"/users/{admin['id']}", "/couriers",
                                           "/orders", f"/orders/{order['id']}", "/routes", "/routes/me", "/establishment/depot")
        ] + [
            ("POST", "/orders", self.order_body(order)), ("PUT", f"/orders/{order['id']}", self.order_body(order)),
            ("DELETE", f"/orders/{order['id']}", None),
            ("PATCH", f"/orders/{order['id']}/status", {"status": "IN_ROUTE"}),
            ("PUT", f"/users/{admin['id']}", self.user_body(admin)), ("DELETE", f"/users/{admin['id']}", None),
            ("POST", "/users", {"full_name": "Novo Usuário", "email": "novo@example.com", "role": "ATTENDANT",
                                 "password": NEW_PASSWORD}),
            ("PUT", "/establishment/depot", self.depot_body()), ("POST", "/routes/generate", {}),
            ("PATCH", "/routes/99999/start", None),
            ("PATCH", "/couriers/me/availability", {"availability": "AVAILABLE"}),
        ]
        for headers in ({}, {"Authorization": "Bearer invalid"}, {"Authorization": f"Bearer {expired}"}, disabled):
            for method, path, body in rows:
                with self.subTest(method=method, path=path, authenticated=bool(headers)):
                    response = self.client.request(method, path, headers=headers, json=body)
                    self.assertEqual(response.status_code, 401, response.text)
                    self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_old_token_loses_admin_privileges_immediately_after_demotion(self):
        created = self.client.post("/users", headers=self.admin, json={
            "full_name": "Segundo Admin", "email": "segundo@example.com", "password": NEW_PASSWORD, "role": "ADMIN",
        }).json()
        old_token = self.login(created["email"], NEW_PASSWORD)
        self.assertEqual(self.client.get("/users", headers=old_token).status_code, 200)
        response = self.client.put(f"/users/{created['id']}", headers=self.admin,
                                   json=self.user_body(created, role="ATTENDANT"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/users", headers=old_token).status_code, 403)
        self.assertEqual(self.client.get("/auth/me", headers=old_token).json()["role"], "ATTENDANT")
        self.assertEqual(self.client.get("/orders", headers=old_token).status_code, 200)

    def test_capacity_cannot_fall_below_combined_assigned_and_in_route_load(self):
        courier = next(u for u in self.client.get("/users", headers=self.admin).json() if u["email"] == "entregador@rotacerta.com.br")
        url = f"/users/{courier['id']}"
        # A carga de Carla é 6 kg: 5 atribuídos e 1 em rota. Dados pessoais também devem ficar intactos.
        response = self.client.put(url, headers=self.admin,
                                   json=self.user_body(courier, full_name="Não Deve Persistir", load_capacity_kg=5.99))
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.client.get(url, headers=self.admin).json(), courier)
        for capacity in (6, 30):
            response = self.client.put(url, headers=self.admin, json=self.user_body(courier, load_capacity_kg=capacity))
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["courier"]["load_capacity_kg"], capacity)

    def test_capacity_ignores_finished_orders_and_can_be_omitted(self):
        courier = next(u for u in self.client.get("/users", headers=self.admin).json() if u["email"] == "entregador2@rotacerta.com.br")
        load = next(c["active_load_kg"] for c in self.client.get("/couriers", headers=self.admin).json()
                    if c["id"] == courier["courier"]["id"])
        url = f"/users/{courier['id']}"
        response = self.client.put(url, headers=self.admin, json=self.user_body(courier, load_capacity_kg=load))
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.put(url, headers=self.admin, json=self.user_body(courier, full_name="Diego Atualizado"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["courier"]["load_capacity_kg"], load)

    def assert_unsafe_edits_rejected(self, order):
        before = self.detail(order["id"])
        other_courier = next(c["id"] for c in self.client.get("/couriers", headers=self.admin).json()
                             if c["id"] != order["assigned_courier"]["id"])
        changes = [
            {"assigned_courier_id": other_courier}, {"assigned_courier_id": None},
            {"customer_id": self.customer_id("Outro Cliente")}, {"delivery_address": "Rua Alterada, 100"},
            {"latitude": order["latitude"] + 0.001}, {"longitude": order["longitude"] + 0.001},
            {"weight_kg": order["weight_kg"] + 0.1},
        ]
        for headers in (self.admin, self.attendant):
            for change in changes:
                with self.subTest(change=change):
                    response = self.client.put(f"/orders/{order['id']}", headers=headers,
                                               json=self.order_body(order, **change))
                    self.assertEqual(response.status_code, 409, response.text)
                    self.assertEqual(self.detail(order["id"]), before)

    def test_in_route_order_without_generated_route_rejects_unsafe_edits(self):
        order = self.client.get("/orders?status=IN_ROUTE", headers=self.admin).json()[0]
        self.assert_unsafe_edits_rejected(order)
        response = self.client.put(f"/orders/{order['id']}", headers=self.admin,
                                   json=self.order_body(order, priority=3))
        self.assertEqual(response.status_code, 200, response.text)

    def test_started_route_details_and_stops_survive_rejected_edits(self):
        route = self.start(self.generate()[0])
        order = self.detail(route["stops"][0]["order_id"])
        self.assert_unsafe_edits_rejected(order)
        listed = self.client.get("/routes", headers=self.admin).json()["routes"]
        self.assertEqual(next(r for r in listed if r["id"] == route["id"]), route)

    def test_individually_started_route_protects_remaining_assigned_stop(self):
        route = self.generate()[0]
        first, second = route["stops"][:2]
        response = self.client.patch(f"/orders/{first['order_id']}/status", headers=self.admin, json={"status": "IN_ROUTE"})
        self.assertEqual(response.status_code, 200, response.text)
        remaining = self.detail(second["order_id"])
        self.assertEqual(remaining["status"], "ASSIGNED")
        self.assert_unsafe_edits_rejected(remaining)
        response = self.client.patch(f"/orders/{second['order_id']}/status", headers=self.admin, json={"status": "PENDING"})
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.detail(second["order_id"]), remaining)

    def test_finished_stop_cannot_be_reopened_or_deleted_in_active_or_finished_route(self):
        route = self.start(self.generate()[0])
        for index, stop in enumerate(route["stops"]):
            target = "DELIVERED" if index == 0 else "CANCELLED"
            response = self.client.patch(f"/orders/{stop['order_id']}/status", headers=self.admin,
                                         json={"status": target, "note": "Cancelado para teste de histórico"})
            self.assertEqual(response.status_code, 200, response.text)
            before = self.detail(stop["order_id"])
            response = self.client.patch(f"/orders/{stop['order_id']}/status", headers=self.admin, json={"status": "PENDING"})
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(self.client.delete(f"/orders/{stop['order_id']}", headers=self.admin).status_code, 409)
            self.assertEqual(self.detail(stop["order_id"]), before)
        with self.session_factory() as db:
            saved = db.get(Route, route["id"])
            self.assertEqual(saved.status, "COMPLETED")
            self.assertEqual(len(saved.stops), len(route["stops"]))
            self.assertEqual([s.status for s in saved.stops], ["COMPLETED"] + ["FAILED"] * (len(saved.stops) - 1))
        # Gerar novas rotas também não pode apagar as paradas históricas.
        self.generate()
        with self.session_factory() as db:
            self.assertEqual(len(db.get(Route, route["id"]).stops), len(route["stops"]))

    def test_cancelled_route_stop_cannot_be_reopened(self):
        route = self.start(self.generate()[0])
        for stop in route["stops"]:
            response = self.client.patch(f"/orders/{stop['order_id']}/status", headers=self.admin,
                                         json={"status": "CANCELLED", "note": "Cliente cancelou a entrega"})
            self.assertEqual(response.status_code, 200, response.text)
        response = self.client.patch(f"/orders/{route['stops'][0]['order_id']}/status", headers=self.admin,
                                     json={"status": "PENDING"})
        self.assertEqual(response.status_code, 409, response.text)
        with self.session_factory() as db:
            self.assertEqual(db.get(Route, route["id"]).status, "CANCELLED")
            self.assertEqual(len(db.get(Route, route["id"]).stops), len(route["stops"]))

    def test_order_without_route_history_can_still_be_reopened(self):
        order = self.create_order()
        url = f"/orders/{order['id']}/status"
        for target in ("CANCELLED", "PENDING"):
            response = self.client.patch(url, headers=self.attendant,
                                         json={"status": target, "note": "Correção solicitada pelo cliente"})
            self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["assigned_courier"])

    def test_depot_change_invalidates_only_local_plans_and_keeps_orders(self):
        foreign = self.foreign_tenant(route_status="IN_PROGRESS")
        routes = self.generate()
        before = self.client.get("/orders", headers=self.admin).json()
        response = self.client.put("/establishment/depot", headers=self.admin, json=self.depot_body(latitude=-8.06))
        self.assertEqual(response.status_code, 200, response.text)
        overview = self.client.get("/routes", headers=self.admin).json()
        self.assertEqual(overview["routes"], [])
        self.assertEqual(overview["waiting_orders"], sum(len(r["stops"]) for r in routes))
        self.assertEqual(self.client.get("/orders", headers=self.admin).json(), before)
        with self.session_factory() as db:
            self.assertEqual(db.get(Route, foreign["route"]).status, "IN_PROGRESS")
            self.assertEqual(db.query(RouteStop).count(), 1)

    def test_depot_unchanged_at_storage_precision_preserves_plans(self):
        routes = self.generate()
        body = self.depot_body()
        body["latitude"] += 0.0000001
        body["depot_address"] = "  " + body["depot_address"] + "  "
        response = self.client.put("/establishment/depot", headers=self.admin, json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/routes", headers=self.admin).json()["routes"], routes)

    def test_depot_change_blocked_with_active_route_without_partial_deletion(self):
        routes = self.generate()
        self.start(routes[0])
        before = self.client.get("/routes", headers=self.admin).json()
        original = self.depot_body()
        for change in ({"latitude": -8.06}, {"longitude": -34.89}, {"depot_address": "Rua Nova, 100"}):
            response = self.client.put("/establishment/depot", headers=self.admin, json={**original, **change})
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(self.client.get("/routes", headers=self.admin).json(), before)
        response = self.client.put("/establishment/depot", headers=self.admin, json=original)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/routes", headers=self.admin).json(), before)

    def test_depot_change_preserves_completed_route_history(self):
        route = self.start(self.generate()[0])
        for stop in route["stops"]:
            response = self.client.patch(f"/orders/{stop['order_id']}/status", headers=self.admin, json={"status": "DELIVERED"})
            self.assertEqual(response.status_code, 200, response.text)
        before = next(r for r in self.client.get("/routes", headers=self.admin).json()["routes"] if r["id"] == route["id"])
        response = self.client.put("/establishment/depot", headers=self.admin, json=self.depot_body(latitude=-8.06))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/routes", headers=self.admin).json()["routes"], [before])

    def test_changed_delivery_window_invalidates_planned_route(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        for field in ("desired_start", "desired_end"):
            with self.subTest(field=field):
                order = self.create_order(assigned_courier_id=self.courier_id(),
                                          desired_start=future.isoformat(), desired_end=(future + timedelta(hours=2)).isoformat())
                routes = self.generate()
                own = next(r for r in routes if r["courier"]["id"] == self.courier_id())
                other_ids = {r["id"] for r in routes if r["id"] != own["id"]}
                changed = future + timedelta(hours=1 if field == "desired_start" else 3)
                response = self.client.put(f"/orders/{order['id']}", headers=self.admin,
                                           json=self.order_body(order, **{field: changed.isoformat()}))
                self.assertEqual(response.status_code, 200, response.text)
                listed = self.client.get("/routes", headers=self.admin).json()["routes"]
                self.assertEqual({r["id"] for r in listed}, other_ids)
                self.assertEqual(self.detail(order["id"])["status"], "ASSIGNED")

    def test_equivalent_window_timezones_do_not_invalidate_planned_route(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        end = future + timedelta(hours=2)
        order = self.create_order(assigned_courier_id=self.courier_id(),
                                  desired_start=future.isoformat(), desired_end=end.isoformat())
        routes = self.generate()
        local = timezone(timedelta(hours=-3))
        response = self.client.put(f"/orders/{order['id']}", headers=self.admin, json=self.order_body(
            order, desired_start=future.astimezone(local).isoformat(), desired_end=end.astimezone(local).isoformat(),
        ))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get("/routes", headers=self.admin).json()["routes"], routes)


if __name__ == "__main__":
    unittest.main()
