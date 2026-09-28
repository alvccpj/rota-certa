from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import geocoding
from app.models import User
from app.schemas import GeocodeResult
from app.security import ADMIN, ATTENDANT, require_roles

router = APIRouter(tags=["geocoding"])


@router.get("/geocode", response_model=list[GeocodeResult])
def geocode(
    q: str = Query(min_length=5, max_length=200),
    user: User = Depends(require_roles(ADMIN, ATTENDANT)),
) -> list[GeocodeResult]:
    """Sugere coordenadas para um endereço digitado no cadastro do pedido."""

    establishment = user.establishment
    near = None
    if establishment.depot_latitude is not None and establishment.depot_longitude is not None:
        near = (float(establishment.depot_latitude), float(establishment.depot_longitude))
    try:
        return geocoding.search_address(q.strip(), near)
    except geocoding.GeocodingUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "A busca de endereço está indisponível agora. Marque o local de entrega direto no mapa.",
        )
