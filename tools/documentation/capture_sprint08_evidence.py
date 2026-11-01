"""Executar somente na demonstração isolada iniciada nas portas 8018 e 5188."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/sprint-08'
API = 'http://127.0.0.1:8018'
APP = 'http://127.0.0.1:5188'


def main():
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    client = httpx.Client(base_url=API, timeout=60)
    def login(email):
        r = client.post('/auth/login', json={'email': email, 'password': 'rotacerta123'})
        r.raise_for_status()
        return {'Authorization': 'Bearer ' + r.json()['access_token']}
    admin = login('admin@rotacerta.com.br')
    attendant = login('atendente@rotacerta.com.br')
    courier = login('entregador2@rotacerta.com.br')
    assert client.get('/health').json()['dialect'] == 'sqlite', 'Use apenas banco isolado de demonstração.'
    c = client.post('/customers', headers=admin, json={'full_name': 'Cliente Sprint Oito', 'phone': '(81) 98888-0808'})
    c.raise_for_status()
    future = datetime.now(timezone.utc) + timedelta(hours=2)
    ids = []
    for weight in (1, 100):
        r = client.post('/orders', headers=admin, json={'customer_id': c.json()['id'], 'delivery_address': 'Rua da Aurora, 400 - Recife', 'latitude': -8.059, 'longitude': -34.882, 'weight_kg': weight, 'priority': 1, 'desired_start': future.isoformat(), 'desired_end': (future + timedelta(hours=2)).isoformat()})
        r.raise_for_status()
        ids.append(r.json()['id'])
    log = {'date': datetime.now(timezone.utc).isoformat(), 'database': client.get('/health').json(), 'created_orders': ids}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome')
        def page_for(email, mobile=False):
            page = browser.new_page(viewport={'width': 390 if mobile else 1440, 'height': 844 if mobile else 1000}, locale='pt-BR', timezone_id='America/Fortaleza', device_scale_factor=1)
            page.goto(APP + '/login')
            page.get_by_label('E-mail').fill(email)
            page.get_by_label('Senha', exact=True).fill('rotacerta123')
            page.get_by_role('button', name='Entrar', exact=True).click()
            page.wait_for_url('**/entregas' if mobile else '**/painel')
            return page
        page = page_for('admin@rotacerta.com.br')
        page.goto(APP + '/pedidos')
        button = page.get_by_role('button', name='Atribuir automaticamente', exact=True)
        expect(button).to_be_enabled()
        button.click()
        expect(page.get_by_role('alertdialog')).to_be_visible()
        page.screenshot(path=OUT/'assets/01_confirmacao.png')
        page.get_by_role('button', name='Atribuir pedidos', exact=True).click()
        expect(page.get_by_role('heading', name='Resultado da atribuição automática')).to_be_visible()
        page.screenshot(path=OUT/'assets/02_atribuicao.png')
        assigned = client.get(f'/orders/{ids[0]}', headers=admin).json()
        assert assigned['status'] == 'ASSIGNED'
        assert client.get(f'/orders/{ids[1]}', headers=admin).json()['status'] == 'PENDING'
        log['assignment'] = {'assigned': ids[0], 'capacity_refused': ids[1], 'history': assigned['history']}
        page.goto(APP + '/rotas')
        page.get_by_role('button', name='Gerar rotas', exact=True).click()
        expect(page.locator('.stop-timing').first).to_be_visible(timeout=60000)
        page.screenshot(path=OUT/'assets/03_rotas.png')
        page.locator('.stop-timing').first.scroll_into_view_if_needed()
        page.screenshot(path=OUT/'assets/04_janelas.png')
        routes = client.get('/routes', headers=admin).json()['routes']
        log['routes'] = routes
        delivery = page_for('entregador2@rotacerta.com.br', True)
        delivery.get_by_role('button', name='Iniciar rota', exact=True).click()
        expect(delivery.get_by_role('button', name='Iniciar rota', exact=True)).to_have_count(0)
        delivery.screenshot(path=OUT/'assets/05_entregador.png')
        target = next(s['order_id'] for r in routes if r['courier']['full_name'] == 'Diego Entregador' for s in r['stops'])
        r = client.patch(f'/orders/{target}/status', headers=courier, json={'status':'DELIVERED'})
        r.raise_for_status()
        log['delivery'] = r.json()
        delivery.goto(APP + '/relatorios')
        expect(delivery.get_by_role('heading', name='Esta página não está disponível para o seu perfil')).to_be_visible()
        delivery.screenshot(path=OUT/'assets/06_acesso_negado.png')
        page.goto(APP + '/painel')
        expect(page.get_by_role('heading', name='Olá, Ana')).to_be_visible()
        expect(page.get_by_role('heading', name='Fluxo dos pedidos')).to_be_visible()
        expect(page.locator('.dashboard-loading')).to_have_count(0)
        page.screenshot(path=OUT/'assets/07_painel.png')
        page.goto(APP + f'/pedidos/{target}')
        expect(page.get_by_role('heading', name=f'Pedido #{target}', exact=True)).to_be_visible()
        page.screenshot(path=OUT/'assets/08_historico.png')
        page.goto(APP + '/relatorios')
        expect(page.locator('tbody tr').first).to_be_visible()
        with page.expect_download() as info:
            page.get_by_role('button', name='Exportar CSV', exact=True).click()
        csv = Path(info.value.path()).read_text(encoding='utf-8-sig')
        assert 'Cliente Sprint Oito' in csv
        log['csv_downloaded'] = True
        browser.close()
    log['permissions'] = []
    for label, path, headers, expected in [('Anônimo','/orders',{},401), ('Atendente','/users',attendant,403), ('Entregador','/dashboard/summary',courier,403), ('Administrador','/users',admin,200), ('Atendente','/orders',attendant,200)]:
        response = client.get(path, headers=headers)
        assert response.status_code == expected
        log['permissions'].append({'profile':label,'path':path,'status':response.status_code})
    (OUT/'evidencias/fluxos.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Fluxos, CSV e permissões verificados; 8 capturas salvas.')


if __name__ == '__main__':
    main()
