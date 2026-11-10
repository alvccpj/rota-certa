"""Verificações de contrato, DDL e integração da Release Candidate (somente leitura).

Defina DATABASE_URL para o schema de testes e opcionalmente API_URL.
"""

import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.database import Base
from app import models  # noqa: F401


def main():
    engine = create_engine(os.environ["DATABASE_URL"])
    assert engine.dialect.name == "postgresql", "Verifique a RC no PostgreSQL real."
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    assert tables == sorted(Base.metadata.tables), tables
    result = {"executado_em": datetime.now(ZoneInfo("America/Recife")).isoformat(timespec="seconds"),
              "ambiente": {"sistema": platform.system(), "arquitetura": platform.machine(),
                           "python": platform.python_version(), "processadores_logicos": os.cpu_count()},
              "tabelas": {}, "integridade": []}
    with engine.connect() as db:
        result["schema"] = db.scalar(text("SELECT current_schema()"))
        result["postgresql"] = db.scalar(text("SHOW server_version"))
        for table in tables:
            columns = inspector.get_columns(table)
            assert {column["name"] for column in columns} == set(Base.metadata.tables[table].columns.keys()), table
            result["tabelas"][table] = {
                "colunas": [{"nome": c["name"], "tipo": str(c["type"]), "nulo": c["nullable"]} for c in columns],
                "chave_primaria": inspector.get_pk_constraint(table),
                "chaves_estrangeiras": inspector.get_foreign_keys(table),
                "restricoes_check": inspector.get_check_constraints(table),
                "restricoes_unique": inspector.get_unique_constraints(table),
                "indices": inspector.get_indexes(table),
                "registros": db.scalar(text(f'SELECT count(*) FROM "{table}"')),
            }
            for fk in inspector.get_foreign_keys(table):
                child, parent = fk["constrained_columns"][0], fk["referred_columns"][0]
                target = fk["referred_table"]
                query = (f'SELECT count(*) FROM "{table}" c WHERE c."{child}" IS NOT NULL '
                         f'AND NOT EXISTS (SELECT 1 FROM "{target}" p WHERE p."{parent}" = c."{child}")')
                count = db.scalar(text(query))
                assert count == 0, (table, child, count)
                result["integridade"].append({"relacionamento": f"{table}.{child} -> {target}.{parent}", "orfaos": count})
        tenant_checks = {
            "pedido e cliente": "SELECT count(*) FROM orders o JOIN customers c ON c.id=o.customer_id WHERE o.establishment_id<>c.establishment_id",
            "pedido e entregador": "SELECT count(*) FROM orders o JOIN couriers c ON c.id=o.assigned_courier_id WHERE o.establishment_id<>c.establishment_id",
            "rota e entregador": "SELECT count(*) FROM routes r JOIN couriers c ON c.id=r.courier_id WHERE r.establishment_id<>c.establishment_id",
            "parada e pedido": "SELECT count(*) FROM route_stops s JOIN routes r ON r.id=s.route_id JOIN orders o ON o.id=s.order_id WHERE r.establishment_id<>o.establishment_id",
        }
        result["isolamento"] = {name: db.scalar(text(query)) for name, query in tenant_checks.items()}
        assert not any(result["isolamento"].values()), result["isolamento"]
    # Outra conexão e outra sessão HTTP, depois de todos os commits do roteiro.
    with httpx.Client(base_url=os.environ.get("API_URL", "http://127.0.0.1:8020"), timeout=30) as client:
        contract = client.get("/openapi.json")
        contract.raise_for_status()
        saved = json.loads((ROOT / "docs/api/openapi.json").read_text(encoding="utf-8"))
        assert contract.json() == saved, "Reexporte o contrato OpenAPI."
        login = client.post("/auth/login", json={"email": "admin@rotacerta.com.br", "password": "rotacerta123"})
        login.raise_for_status()
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        tenant = login.json()["user"]["establishment"]["id"]
        orders = client.get("/orders", headers=headers).json()
        with engine.connect() as db:
            stored = db.execute(text("SELECT id,status FROM orders WHERE establishment_id=:id ORDER BY id"), {"id": tenant}).all()
        assert {o["id"]: o["status"] for o in orders} == dict(stored)
        result["integracao"] = {"contrato_igual_ao_servido": True,
                               "operacoes_http": sum(len(v) for v in saved["paths"].values()),
                               "pedidos_api_e_sql_mesmos_ids_e_status": len(stored),
                               "nova_sessao_leu_dados_persistidos": True,
                               "health": client.get("/health").json()}
    result["situacao"] = "Aprovado"
    destination = ROOT / "docs/sprint-10/evidencias/banco_e_contrato.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    engine.dispose()
    print(f"{len(tables)} tabelas, {len(result['integridade'])} relacionamentos sem órfãos, contrato sincronizado e API/SQL consistentes.")


if __name__ == "__main__":
    main()
