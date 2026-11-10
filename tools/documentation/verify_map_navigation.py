"""Regressão real de navegação durante reenquadramento dos mapas (BUG-13)."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/sprint-12/evidencias/regressao_mapas.json')
    args = parser.parse_args()
    errors, steps = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome')
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        page.on('pageerror', lambda error: errors.append({'erro': str(error), 'stack': error.stack, 'url': page.url}))
        app = os.environ.get('APP_URL', 'http://127.0.0.1:5192')
        page.goto(app+'/login')
        page.get_by_label('E-mail').fill('admin@rotacerta.com.br')
        page.get_by_label('Senha', exact=True).fill('rotacerta123')
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.wait_for_url('**/painel')
        for i in range(10):
            page.goto(app+'/pedidos/novo')
            expect(page.get_by_label('Latitude')).to_be_enabled()
            page.get_by_label('Latitude').fill('-8.0631')
            page.get_by_label('Longitude').fill('-34.8711')
            # Troca via React Router enquanto o Leaflet ainda pode estar animando.
            page.get_by_role('navigation', name='Seções').get_by_role('link', name='Pedidos', exact=True).click()
            page.wait_for_timeout(500)
            steps.append({'ciclo': i+1, 'tela': 'pedido -> pedidos', 'erros_acumulados': len(errors)})
        for i in range(5):
            page.goto(app+'/rotas')
            expect(page.locator('.route-map .leaflet-container')).to_be_visible()
            page.get_by_role('navigation', name='Seções').get_by_role('link', name='Pedidos', exact=True).click()
            page.wait_for_timeout(500)
            steps.append({'ciclo': i+1, 'tela': 'rotas -> pedidos', 'erros_acumulados': len(errors)})
        browser.close()
    data = {'executado_em': datetime.now(ZoneInfo('America/Recife')).isoformat(timespec='seconds'),
            'casos': steps, 'erros_javascript': errors, 'situacao': 'Reprovado' if errors else 'Aprovado'}
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(f'{len(steps)} navegações; {len(errors)} erros JavaScript; {data["situacao"]}.')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
