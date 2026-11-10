"""Regressões encontradas na revisão de código da Sprint 11."""

import unittest
from unittest.mock import patch

import httpx

from api_base import ApiTestCase
from app.optimizer.schemas import OptimizationRequest
from pydantic import ValidationError


class GeocoderBoundaryTestCase(ApiTestCase):
    def search(self, payload):
        response = httpx.Response(200, json=payload, request=httpx.Request("GET", "https://geocoder.test/search"))
        with patch("app.geocoding.httpx.get", return_value=response):
            return self.client.get("/geocode", headers=self.admin, params={"q": "Rua do Teste"})

    def test_invalid_upstream_structure_returns_manual_map_guidance(self):
        for payload in ({"error": "temporariamente indisponível"}, [None], [{"display_name": "Local sem coordenadas"}],
                        [{"lat": "-8", "lon": "-34", "address": "inválido"}],
                        [{"lat": "-8", "lon": "-34", "address": []}],
                        [{"lat": "-8", "lon": "-34", "address": {"road": "Rua", "city": "Recife", "ISO3166-2-lvl4": 12}}]):
            with self.subTest(payload=payload):
                response = self.search(payload)
                self.assertEqual(response.status_code, 503, response.text)
                self.assertIn("Marque o local de entrega", response.json()["detail"])

    def test_invalid_upstream_coordinates_do_not_reach_the_map(self):
        for latitude, longitude in (("nan", "0"), ("91", "0"), ("0", "181"), ("texto", "0")):
            with self.subTest(latitude=latitude, longitude=longitude):
                response = self.search([{"lat": latitude, "lon": longitude, "display_name": "Local"}])
                self.assertEqual(response.status_code, 503, response.text)

    def test_empty_search_and_valid_coordinates_remain_supported(self):
        self.assertEqual(self.search([]).json(), [])
        response = self.search([{"lat": "0", "lon": "0", "display_name": "Ponto no equador"}])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()[0]["latitude"], 0)


class CompareLimitsTestCase(unittest.TestCase):
    stop = {"id": "ponto", "latitude": -8.05, "longitude": -34.9}

    def request(self, routes):
        return OptimizationRequest.model_validate({"depot": self.stop, "routes": routes, "workers": 2})

    def test_public_comparator_rejects_more_than_64_routes(self):
        with self.assertRaises(ValidationError):
            self.request([{"courier_id": str(i), "stops": []} for i in range(65)])

    def test_public_comparator_rejects_more_than_500_stops_per_route(self):
        with self.assertRaises(ValidationError):
            self.request([{"courier_id": "um", "stops": [self.stop] * 501}])

    def test_public_comparator_rejects_more_than_12000_stops_in_total(self):
        with self.assertRaises(ValidationError):
            self.request([{"courier_id": str(i), "stops": [self.stop] * 500} for i in range(25)])

    def test_comparator_accepts_exact_limits(self):
        data = self.request([{"courier_id": str(i), "stops": [self.stop] * 500} for i in range(24)])
        self.assertEqual(sum(len(route.stops) for route in data.routes), 12000)


if __name__ == "__main__":
    unittest.main()
