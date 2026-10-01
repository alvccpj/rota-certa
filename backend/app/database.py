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


def create_missing_tables() -> None:
    """Cria as tabelas adicionadas depois da Sprint 03 em bancos que já existiam."""

    from app.models import OrderStatusEvent

    if not inspect(engine).has_table(OrderStatusEvent.__tablename__):
        Base.metadata.create_all(engine, tables=[OrderStatusEvent.__table__])
        logger.info("Tabela %s criada.", OrderStatusEvent.__tablename__)


# Sprint 05: modo GPU e métricas da comparação em bancos criados antes dela.
SPRINT_05_UPGRADE = """
ALTER TABLE routes DROP CONSTRAINT IF EXISTS routes_execution_mode_check;
ALTER TABLE routes ADD CONSTRAINT routes_execution_mode_check
    CHECK (execution_mode IN ('SEQUENTIAL', 'PARALLEL', 'GPU'));
ALTER TABLE optimization_runs DROP CONSTRAINT IF EXISTS optimization_runs_execution_mode_check;
ALTER TABLE optimization_runs ADD CONSTRAINT optimization_runs_execution_mode_check
    CHECK (execution_mode IN ('SEQUENTIAL', 'PARALLEL', 'GPU'));
ALTER TABLE optimization_runs
    ADD COLUMN IF NOT EXISTS purpose VARCHAR(20) NOT NULL DEFAULT 'BENCHMARK'
        CHECK (purpose IN ('ROUTE_GENERATION', 'BENCHMARK')),
    ADD COLUMN IF NOT EXISTS input_source VARCHAR(20) NOT NULL DEFAULT 'REAL'
        CHECK (input_source IN ('REAL', 'SYNTHETIC')),
    ADD COLUMN IF NOT EXISTS run_group VARCHAR(36),
    ADD COLUMN IF NOT EXISTS speedup NUMERIC(10, 3),
    ADD COLUMN IF NOT EXISTS efficiency NUMERIC(8, 4),
    ADD COLUMN IF NOT EXISTS same_routes BOOLEAN;
CREATE INDEX IF NOT EXISTS idx_optimization_runs_group ON optimization_runs(establishment_id, run_group);
CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(establishment_id, status);
"""


def upgrade_schema() -> bool:
    """Aplica as alterações da Sprint 05 quando o banco ainda não as tem."""

    if engine.dialect.name != "postgresql":
        return False
    columns = {column["name"] for column in inspect(engine).get_columns("optimization_runs")}
    if "run_group" in columns:
        return False
    with engine.begin() as connection:
        connection.exec_driver_sql(SPRINT_05_UPGRADE)
    logger.info("Banco atualizado para a Sprint 05 (modo GPU e métricas de comparação).")
    return True
