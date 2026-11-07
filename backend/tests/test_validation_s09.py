"""Sprint 09: regressões dos bugs encontrados nos testes de validação.

Cada teste reproduz a entrada que falhava antes da correção (BUG-01 a BUG-04
do documento da Sprint 09) e confirma a resposta esperada.
"""

from datetime import datetime, timedelta, timezone

from api_base import ApiTestCase


def tomorrow_at(hour: int) -> datetime:
    day = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    return datetime(day.year, day.month, day.day, hour, tzinfo=timezone.utc)


class BlankTextTestCase(ApiTestCase):
    """BUG-01: texto só com espaços passava no tamanho mínimo e era salvo vazio."""

    def assert_field_error(self, response, field: str, message: str) -> None:
        self.assertEqual(response.status_code, 422, response.text)
        issues = {issue["loc"][-1]: issue["msg"] for issue in response.json()["detail"]}
        self.assertIn(field, issues)
        self.assertIn(message, issues[field])

    def test_order_address_with_only_spaces_is_rejected(self) -> None:
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(delivery_address="        "))
        self.assert_field_error(response, "delivery_address", "Informe o endereço com rua, número e bairro.")

    def test_order_address_is_measured_after_collapsing_spaces(self) -> None:
        response = self.client.post("/orders", headers=self.admin, json=self.order_payload(delivery_address="  a     b  "))
        self.assert_field_error(response, "delivery_address", "Informe o endereço com rua, número e bairro.")

    def test_valid_address_is_still_normalized(self) -> None:
        response = self.client.post(
            "/orders", headers=self.admin, json=self.order_payload(delivery_address="  Rua   do Sol,  10 ")
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["delivery_address"], "Rua do Sol, 10")

    def test_register_rejects_blank_business_name_and_depot(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={
                "establishment_name": "      ",
                "depot_address": "       ",
                "full_name": "Maria Silva",
                "email": "maria.s09@exemplo.com.br",
                "password": "abc12345",
            },
        )
        self.assertEqual(response.status_code, 422, response.text)
        fields = {issue["loc"][-1] for issue in response.json()["detail"]}
        self.assertEqual(fields, {"establishment_name", "depot_address"})
        login = self.client.post("/auth/login", json={"email": "maria.s09@exemplo.com.br", "password": "abc12345"})
        self.assertEqual(login.status_code, 401, "o cadastro inválido não pode criar a conta")

    def test_depot_address_with_only_spaces_is_rejected(self) -> None:
        response = self.client.put(
            "/establishment/depot",
            headers=self.admin,
            json={"depot_address": "         ", "latitude": -8.05, "longitude": -34.9},
        )
        self.assert_field_error(response, "depot_address", "Informe o endereço com rua, número e bairro.")
        depot = self.client.get("/routes", headers=self.admin).json()["depot"]
        self.assertTrue(depot["address"].strip(), "o ponto de saída anterior deve ser mantido")


class WindowTimezoneTestCase(ApiTestCase):
    """BUG-02: janela com uma data sem fuso e outra com fuso gerava erro 500."""

    def test_mixed_naive_and_aware_window_is_accepted(self) -> None:
        start = tomorrow_at(13)  # 13h UTC, enviada sem fuso
        end = tomorrow_at(18).astimezone(timezone(timedelta(hours=-3)))  # 15h em Recife = 18h UTC
        response = self.client.post(
            "/orders",
            headers=self.admin,
            json=self.order_payload(
                desired_start=start.replace(tzinfo=None).isoformat(), desired_end=end.isoformat()
            ),
        )
        self.assertEqual(response.status_code, 201, response.text)
        saved = response.json()
        self.assertEqual(datetime.fromisoformat(saved["desired_start"]), start)
        self.assertEqual(datetime.fromisoformat(saved["desired_end"]), end)

    def test_mixed_window_is_compared_in_utc(self) -> None:
        start = tomorrow_at(19)  # 19h UTC sem fuso
        end = tomorrow_at(18).astimezone(timezone(timedelta(hours=-3)))  # 18h UTC: antes do início
        response = self.client.post(
            "/orders",
            headers=self.admin,
            json=self.order_payload(
                desired_start=start.replace(tzinfo=None).isoformat(), desired_end=end.isoformat()
            ),
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("O fim da janela de entrega deve ser depois do início.", response.text)


class SeedWindowTestCase(ApiTestCase):
    """BUG-07: no SQLite as janelas da demonstração ficavam 3 horas antes do previsto."""

    def test_demo_windows_keep_recife_local_time(self) -> None:
        recife = timezone(timedelta(hours=-3))
        orders = sorted(self.client.get("/orders", headers=self.admin).json(), key=lambda order: order["id"])
        self.assertTrue(orders)
        for index, order in enumerate(orders[:3]):
            with self.subTest(order=order["id"]):
                start = datetime.fromisoformat(order["desired_start"]).astimezone(recife)
                self.assertEqual(start.hour, 9 + index, "a primeira janela começa às 9h de Recife")
                end = datetime.fromisoformat(order["desired_end"]).astimezone(recife)
                self.assertEqual(end - start, timedelta(hours=2))


class DatabaseValueTestCase(ApiTestCase):
    """BUG-03 e BUG-04: valores que o banco não aceita geravam erro 500."""

    def test_huge_ids_return_validation_error(self) -> None:
        for method, path, body in [
            ("GET", "/orders/99999999999999999999", None),
            ("PUT", "/customers/9223372036854775808", {"full_name": "Fulano de Tal"}),
            ("GET", "/users/99999999999999999999", None),
        ]:
            with self.subTest(path=path):
                response = self.client.request(method, path, headers=self.admin, json=body)
                self.assertEqual(response.status_code, 422, response.text)
                self.assertIn("fora do formato aceito", response.json()["detail"])

    def test_control_characters_are_removed_from_names(self) -> None:
        response = self.client.post("/customers", headers=self.admin, json={"full_name": "Jo\u0000ão\u0007 Silva"})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["full_name"], "João Silva")

    def test_cancellation_reason_made_of_control_characters_is_rejected(self) -> None:
        order = self.client.post("/orders", headers=self.admin, json=self.order_payload()).json()
        response = self.client.patch(
            f"/orders/{order['id']}/status",
            headers=self.admin,
            json={"status": "CANCELLED", "note": "\u0000\u0000\u0000\u0000\u0000\u0000"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn("motivo do cancelamento", response.text)
