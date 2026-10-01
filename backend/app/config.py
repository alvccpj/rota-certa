from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações lidas de variáveis de ambiente ou de backend/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta"
    jwt_secret: str = "rotacerta-chave-local-de-desenvolvimento-troque-em-producao"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_delivery_radius_km: float = 30
    # Usados para estimar a duração da rota e o horário de chegada em cada parada.
    average_speed_kmh: float = 25
    service_minutes_per_stop: float = 5
    local_utc_offset_hours: int = -3
    geocoder_url: str = "https://nominatim.openstreetmap.org/search"
    geocoder_user_agent: str = "RotaCerta/0.4 (+https://github.com/alvccpj/rota-certa)"
    auto_create_schema: bool = True
    seed_demo_data: bool = True
    schema_path: Path = Path(__file__).resolve().parents[2] / "database" / "schema.sql"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
