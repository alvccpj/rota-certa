from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import (
    SessionLocal,
    apply_schema_if_missing,
    create_missing_tables,
    database_status,
    get_db,
    logger,
    upgrade_schema,
)
from app.optimizer.routing import shutdown_pools
from app.routers import auth, customers, geocoding, optimizer, orders, routes, users
from app.seed import DEMO_PASSWORD, seed_demo_data


def prepare_database() -> None:
    try:
        if settings.auto_create_schema:
            apply_schema_if_missing()
            create_missing_tables()
            upgrade_schema()
        if settings.seed_demo_data:
            with SessionLocal() as db:
                if seed_demo_data(db):
                    logger.info("Dados de demonstração criados. Senha dos usuários: %s", DEMO_PASSWORD)
    except Exception as exc:  # A API continua no ar e /health informa a falha.
        logger.error("Não foi possível preparar o banco de dados: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    prepare_database()
    yield
    shutdown_pools()


app = FastAPI(
    title="RotaCerta API",
    version="0.5.0",
    description="API para cadastro, roteirização e acompanhamento de entregas.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(geocoding.router)
app.include_router(routes.router)
app.include_router(optimizer.router)


@app.get("/health", tags=["system"])
def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        return JSONResponse({"status": "ok", **database_status(db)})
    except SQLAlchemyError:
        return JSONResponse({"status": "degraded", "database": "unavailable"}, status_code=503)

