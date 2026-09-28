"""Testes da busca de endereço, sem acessar a internet."""

import unittest
from unittest.mock import patch

from api_base import ApiTestCase

from app.geocoding import GeocodingUnavailable, format_label
from app.schemas import GeocodeResult

NOMINATIM_ITEM = {
    "lat": "-8.0452",
    "lon": "-34.8980",
    "display_name": "210, Rua das Graças, Graças, Recife, Região Metropolitana do Recife, Pernambuco, Brasil",
    "address": {
        "house_number": "210",
        "road": "Rua das Graças",
        "suburb": "Graças",
        "city": "Recife",
        "state": "Pernambuco",
        "ISO3166-2-lvl4": "BR-PE",
    },
}


class GeocodingTestCase(ApiTestCase):
    def test_label_follows_brazilian_format(self) -> None:
        self.assertEqual(format_label(NOMINATIM_ITEM), "Rua das Graças, 210 - Graças, Recife - PE")

    def test_label_falls_back_to_display_name(self) -> None:
        item = {"display_name": "Praça do Marco Zero, Recife", "address": {}}
        self.assertEqual(format_label(item), "Praça do Marco Zero, Recife")

    def test_search_uses_depot_as_reference(self) -> None:
        result = [GeocodeResult(label="Rua das Graças, 210 - Graças, Recife - PE", latitude=-8.0452, longitude=-34.898)]
        with patch("app.geocoding.search_address", return_value=result) as search:
            response = self.client.get("/geocode", headers=self.attendant, params={"q": "Rua das Graças, 210"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["latitude"], -8.0452)
        _, near = search.call_args.args
        self.assertAlmostEqual(near[0], -8.0593)

    def test_unavailable_service_returns_guidance(self) -> None:
        with patch("app.geocoding.search_address", side_effect=GeocodingUnavailable):
            response = self.client.get("/geocode", headers=self.attendant, params={"q": "Rua das Graças, 210"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Marque o local de entrega", response.json()["detail"])

    def test_query_needs_minimum_length(self) -> None:
        self.assertEqual(self.client.get("/geocode", headers=self.attendant, params={"q": "Rua"}).status_code, 422)

    def test_courier_cannot_search(self) -> None:
        response = self.client.get("/geocode", headers=self.courier, params={"q": "Rua das Graças"})
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
