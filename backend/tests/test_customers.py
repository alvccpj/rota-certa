"""Testes do cadastro de clientes."""

import unittest

from api_base import ApiTestCase


class CustomersTestCase(ApiTestCase):
    def test_customer_crud(self) -> None:
        created = self.client.post(
            "/customers",
            headers=self.attendant,
            json={"full_name": "  Rita   de Cássia ", "phone": "81 98877-6655"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        customer = created.json()
        self.assertEqual(customer["full_name"], "Rita de Cássia")
        self.assertEqual(customer["phone"], "(81) 98877-6655")
        self.assertEqual(customer["order_count"], 0)

        found = self.client.get("/customers", headers=self.attendant, params={"q": "rita"}).json()
        self.assertEqual([c["id"] for c in found], [customer["id"]])

        updated = self.client.put(
            f"/customers/{customer['id']}",
            headers=self.attendant,
            json={"full_name": "Rita de Cássia Lima", "phone": "(81) 3222-1100"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["phone"], "(81) 3222-1100")

        self.assertEqual(self.client.delete(f"/customers/{customer['id']}", headers=self.attendant).status_code, 403)
        self.assertEqual(self.client.delete(f"/customers/{customer['id']}", headers=self.admin).status_code, 204)
        self.assertEqual(self.client.get(f"/customers/{customer['id']}", headers=self.admin).status_code, 404)

    def test_phone_must_have_area_code(self) -> None:
        response = self.client.post(
            "/customers",
            headers=self.admin,
            json={"full_name": "Sem DDD", "phone": "98877-6655"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("DDD", response.text)

    def test_name_needs_letters(self) -> None:
        response = self.client.post("/customers", headers=self.admin, json={"full_name": "12"})
        self.assertEqual(response.status_code, 422)

    def test_duplicate_customer_is_rejected(self) -> None:
        payload = {"full_name": "maria silva", "phone": "(81) 98800-1001"}
        self.assertEqual(self.client.post("/customers", headers=self.admin, json=payload).status_code, 409)

    def test_customer_with_orders_cannot_be_deleted(self) -> None:
        maria = self.client.get("/customers", headers=self.admin, params={"q": "Maria"}).json()[0]
        self.assertEqual(maria["order_count"], 1)
        self.assertIn("Boa Viagem", maria["last_address"])
        response = self.client.delete(f"/customers/{maria['id']}", headers=self.admin)
        self.assertEqual(response.status_code, 409)
        self.assertIn("não pode ser excluído", response.json()["detail"])

    def test_courier_cannot_access_customers(self) -> None:
        self.assertEqual(self.client.get("/customers", headers=self.courier).status_code, 403)


if __name__ == "__main__":
    unittest.main()
