r"""Demonstração persistida sem Docker/PostgreSQL. Execute com o Python de backend/.venv.

    backend\.venv\Scripts\python.exe tools/run_local_demo.py

Não substitui a configuração PostgreSQL da aplicação. Dados locais de demonstração
ficam em backend/rotacerta-demo.db; Ctrl+C encerra ambos os servidores.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-port', type=int, default=8000)
    parser.add_argument('--web-port', type=int, default=5173)
    parser.add_argument('--database', type=Path, default=ROOT / 'backend' / 'rotacerta-demo.db')
    args = parser.parse_args()
    node = shutil.which('node')
    vite = ROOT / 'frontend' / 'node_modules' / 'vite' / 'bin' / 'vite.js'
    if not node or not vite.exists():
        parser.error('Instale Node.js e execute npm ci na pasta frontend antes de iniciar.')
    # Falha antes de inicializar o banco se alguma porta já estiver ocupada.
    import socket
    for port in (args.api_port, args.web_port):
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                parser.error(f'A porta {port} está ocupada. Encerre a instância anterior ou escolha outra porta.')
    db_path = args.database.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ['DATABASE_URL'] = 'sqlite:///' + db_path.as_posix()
    os.environ['CORS_ORIGINS'] = f'http://localhost:{args.web_port},http://127.0.0.1:{args.web_port}'
    os.environ['AUTO_CREATE_SCHEMA'] = 'true'
    os.environ['SEED_DEMO_DATA'] = 'true'
    sys.path.insert(0, str(ROOT / 'backend'))
    from app.database import Base, engine, upgrade_schema
    from app import models  # noqa: F401
    Base.metadata.create_all(engine)
    upgrade_schema()
    engine.dispose()
    env = os.environ.copy()
    env['VITE_API_URL'] = f'http://127.0.0.1:{args.api_port}'
    children = []
    try:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
                                         '--host', '127.0.0.1', '--port', str(args.api_port)],
                                        cwd=ROOT / 'backend', env=env))
        children.append(subprocess.Popen([node, str(vite), '--host', '127.0.0.1',
                                         '--port', str(args.web_port), '--strictPort'],
                                        cwd=ROOT / 'frontend', env=env))
        print(f'Abra http://localhost:{args.web_port} | Acesso de demonstração: consulte o README', flush=True)
        print(f'Banco de demonstração: {db_path}. Ctrl+C para encerrar.', flush=True)
        while all(process.poll() is None for process in children):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
        for process in children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
