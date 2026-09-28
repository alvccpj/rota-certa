"""Busca de endereços no OpenStreetMap (Nominatim)."""

import httpx

from app.config import settings
from app.schemas import GeocodeResult


class GeocodingUnavailable(Exception):
    """O serviço de busca não respondeu ou respondeu com erro."""


def format_label(item: dict) -> str:
    """Monta "Rua, número - Bairro, Cidade - UF" a partir da resposta do Nominatim."""

    address = item.get("address") or {}
    road = address.get("road") or address.get("pedestrian")
    city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
    if not road or not city:
        return item.get("display_name", "")
    street = ", ".join(part for part in (road, address.get("house_number")) if part)
    district = address.get("suburb") or address.get("neighbourhood") or address.get("quarter")
    state = (address.get("ISO3166-2-lvl4") or "").removeprefix("BR-") or address.get("state")
    label = f"{street} - {district}" if district else street
    return f"{label}, {city} - {state}" if state else f"{label}, {city}"


def search_address(query: str, near: tuple[float, float] | None = None) -> list[GeocodeResult]:
    params: dict[str, str | int] = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "countrycodes": "br",
        "limit": 5,
        "accept-language": "pt-BR",
    }
    if near is not None:
        # Dá preferência a resultados perto do ponto de saída, sem excluir os demais.
        lat, lon = near
        params["viewbox"] = f"{lon - 0.3},{lat + 0.3},{lon + 0.3},{lat - 0.3}"
    try:
        response = httpx.get(
            settings.geocoder_url,
            params=params,
            headers={"User-Agent": settings.geocoder_user_agent},
            timeout=8,
        )
        response.raise_for_status()
        items = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise GeocodingUnavailable from exc
    return [
        GeocodeResult(label=format_label(item), latitude=float(item["lat"]), longitude=float(item["lon"]))
        for item in items
    ]
