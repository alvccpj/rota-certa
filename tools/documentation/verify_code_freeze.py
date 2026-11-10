"""Cria ou confere o manifesto SHA-256 do código congelado, sem depender do GitHub."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'docs/sprint-12/evidencias/code_freeze.json'


def source_paths():
    roots = ['backend/app', 'frontend/src', 'database']
    files = [p for root in roots for p in (ROOT / root).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    files += [ROOT / p for p in ['backend/requirements.txt', 'backend/requirements-gpu.txt',
              'backend/Dockerfile', 'backend/.env.example', 'frontend/package.json',
              'frontend/package-lock.json', 'frontend/Dockerfile', 'frontend/.env.example',
              'frontend/index.html', 'frontend/vite.config.ts', 'frontend/tsconfig.json',
              'frontend/tsconfig.app.json', 'frontend/tsconfig.node.json',
              'compose.yaml', 'backend/requirements-dev.txt', 'backend/requirements-docs.txt',
              'frontend/.dockerignore', 'backend/.dockerignore', 'frontend/nginx.conf', 'docs/api/openapi.json'] if (ROOT / p).is_file()]
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Somente durante a preparação da nova versão; não recriar após publicar a tag.')
    args = parser.parse_args()
    current = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths()}
    if args.write:
        assert json.loads((ROOT / 'frontend/package.json').read_text())['version'] == '1.0.0'
        assert json.loads((ROOT / 'docs/api/openapi.json').read_text())['info']['version'] == '1.0.0'
        result = {'versao': '1.0.0', 'tag': 'v1.0.0',
                  'gerado_em': datetime.now(ZoneInfo('America/Recife')).isoformat(timespec='seconds'),
                  'escopo': 'Código da aplicação, DDL, dependências e configurações listadas; inclui o contrato OpenAPI. Não inclui artefatos locais, a suíte backend nem todos os documentos.',
                  'sha256': current}
        MANIFEST.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    expected = json.loads(MANIFEST.read_text())['sha256']
    assert current == expected, 'Código divergente do congelamento. Inspecione o diff; não recrie o manifesto para ocultar alterações.'
    print(f'Code Freeze v1.0.0: {len(current)} arquivos íntegros.')


if __name__ == '__main__':
    main()
