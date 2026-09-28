import logging
from collections.abc import Iterator

import psycopg
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger("uvicorn.error")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def database_status(db: Session) -> dict[str, str]:
    """Executa uma consulta simples para confirmar a comunicação com o banco."""

    db.execute(text("SELECT 1"))
    version = db.bind.dialect.server_version_info or ()
    return {
        "database": "connected",
        "dialect": db.bind.dialect.name,
        "server_version": ".".join(str(part) for part in version),
    }


def apply_schema_if_missing() -> bool:
    """Executa database/schema.sql quando o PostgreSQL ainda não possui as tabelas.

    No Docker Compose o próprio PostgreSQL aplica o esquema na primeira
    inicialização; este passo cobre a execução local sem Docker.
    """

    if engine.dialect.name != "postgresql" or inspect(engine).has_table("users"):
        return False
    if not settings.schema_path.exists():
        logger.warning("Tabelas ausentes e %s não encontrado.", settings.schema_path)
        return False
    conninfo = engine.url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(conninfo, autocommit=True) as connection:
        connection.execute(settings.schema_path.read_text(encoding="utf-8"))
    logger.info("Esquema do banco criado a partir de %s.", settings.schema_path)
    return True
