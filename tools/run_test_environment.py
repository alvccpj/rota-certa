r"""Ambiente de testes da Sprint 09: API e frontend ligados a um PostgreSQL isolado.

    backend\.venv\Scripts\python.exe tools/run_test_environment.py

Recria o schema `sprint09_testes` no banco `rotacerta` (o schema `public`, usado no
desenvolvimento, não é tocado), sobe a API em 127.0.0.1:8019 com os dados de
demonstração e o frontend em 127.0.0.1:5189. Com o ambiente no ar, os casos de teste
são executados por tools/documentation/capture_sprint09_evidence.py. Ctrl+C encerra.

Variável opcional: POSTGRES_URL (padrão postgresql://rotacerta:rotacerta_dev@localhost:5432/rotacerta).
"""
import argparse
import os
import re
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sprint09_testes"
API_PORT, WEB_PORT = 8019, 5189
POSTGRES_URL = os.environ.get("POSTGRES_URL", "postgresql://rotacerta:rotacerta_dev@localhost:5432/rotacerta")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default=SCHEMA, help="Schema descartável, com prefixo sprint e sufixo _testes.")
    parser.add_argument("--api-port", type=int, default=API_PORT)
    parser.add_argument("--web-port", type=int, default=WEB_PORT)
    args = parser.parse_args()
    if not re.fullmatch(r"sprint[0-9]+_testes", args.schema):
        parser.error("Use um schema descartável no formato sprint10_testes; public nunca é permitido.")
    schema, api_port, web_port = args.schema, args.api_port, args.web_port
    node = shutil.which("node")
    vite = ROOT / "frontend" / "node_modules" / "vite" / "bin" / "vite.js"
    if not node or not vite.exists():
        sys.exit("Instale Node.js e execute npm ci na pasta frontend antes de iniciar.")
    for port in (api_port, web_port):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                sys.exit(f"A porta {port} está ocupada. Encerre a instância anterior.")
    with psycopg.connect(POSTGRES_URL, autocommit=True) as connection:
        connection.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        connection.execute(f"CREATE SCHEMA {schema}")
    print(f"Schema {schema} recriado; a API cria as tabelas e os dados de demonstração.", flush=True)

    env = os.environ.copy()
    env.update({
        "DATABASE_URL": POSTGRES_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        + f"?options=-csearch_path%3D{schema}",
        "CORS_ORIGINS": f"http://127.0.0.1:{web_port},http://localhost:{web_port}",
        "AUTO_CREATE_SCHEMA": "true",
        "SEED_DEMO_DATA": "true",
        "VITE_API_URL": f"http://127.0.0.1:{api_port}",
    })
    children = []
    try:
        children.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(api_port)],
            cwd=ROOT / "backend", env=env))
        children.append(subprocess.Popen(
            [node, str(vite), "--host", "127.0.0.1", "--port", str(web_port), "--strictPort"],
            cwd=ROOT / "frontend", env=env))
        print(f"API http://127.0.0.1:{api_port} | Sistema http://127.0.0.1:{web_port} | Acesso de demonstração: consulte o README",
              flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    main()
