"""Ensaio técnico real, sem falas humanas. Use o schema descartável sprint120_testes.

Pré-condição: run_test_environment.py --schema sprint120_testes --api-port 8023 --web-port 5193.
O roteiro altera apenas a base apontada pela API; execute somente no ambiente de ensaio.
"""
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import psycopg
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/sprint-12'
API = os.environ.get('REHEARSAL_API_URL', 'http://127.0.0.1:8023')
APP = os.environ.get('REHEARSAL_APP_URL', 'http://127.0.0.1:5193')
RECIFE = ZoneInfo('America/Recife')


def main():
    started = time.perf_counter()
    result = {'executado_em': datetime.now(RECIFE).isoformat(timespec='seconds'),
              'tipo': 'Ensaio técnico automatizado na aplicação real, sem narração humana',
              'versao': '1.0.0', 'api': API, 'frontend': APP, 'etapas': []}
    http = httpx.Client(base_url=API, timeout=120)
    health = http.get('/health').json()
    assert health['dialect'] == 'postgresql' and health['database'] == 'connected', health
    with psycopg.connect(os.environ.get('REHEARSAL_DATABASE_URL',
            'postgresql://arthur@127.0.0.1:5540/rotacerta_rc?options=-csearch_path%3Dsprint120_testes')) as connection:
        assert connection.execute('SELECT current_schema()').fetchone()[0] == 'sprint120_testes'
    health['schema_conferido_sql'] = 'sprint120_testes'
    result['ambiente'] = health
    assert http.get('/openapi.json').json()['info']['version'] == '1.0.0'
    token = http.post('/auth/login', json={'email': 'admin@rotacerta.com.br', 'password': 'rotacerta123'}).json()['access_token']
    headers = {'Authorization': 'Bearer ' + token}
    errors = []

    def get(path):
        r = http.get(path, headers=headers); r.raise_for_status(); return r.json()

    @contextmanager
    def stage(name):
        began = time.perf_counter()
        yield
        result['etapas'].append({'etapa': name, 'duracao_s': round(time.perf_counter()-began, 3), 'situacao': 'Aprovado'})
        print(name + ': Aprovado', flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome')
        context = browser.new_context(viewport={'width': 1600, 'height': 900}, locale='pt-BR', timezone_id='America/Recife', accept_downloads=True)
        page = context.new_page()
        page.on('pageerror', lambda err: errors.append(str(err)))

        def snap(name):
            page.wait_for_load_state('networkidle')
            page.screenshot(path=str(OUT / 'assets' / name))

        def login(email):
            page.goto(APP + '/login')
            page.get_by_label('E-mail').fill(email)
            page.get_by_label('Senha', exact=True).fill('rotacerta123')
            page.get_by_role('button', name='Entrar', exact=True).click()
            page.wait_for_url(lambda url: '/login' not in url)
            expect(page.get_by_role('button', name='Sair', exact=True)).to_be_visible()

        with stage('01 Ambiente, autenticação, painel e perfis'):
            login('admin@rotacerta.com.br')
            page.goto(APP + '/painel')
            expect(page.get_by_role('heading', name='Olá, Ana')).to_be_visible()
            snap('ensaio_01_painel.png')
            page.goto(APP + '/usuarios')
            expect(page.get_by_role('heading', name='Usuários', exact=True)).to_be_visible()
            assert len(get('/users')) == 4

        with stage('02 Cadastro de cliente e pedido real'):
            page.goto(APP + '/clientes/novo')
            page.get_by_label('Nome').fill('Cliente Apresentação Final')
            page.get_by_label('Telefone').fill('81999991212')
            page.get_by_role('button', name='Cadastrar cliente').click()
            page.wait_for_url(re.compile(r'/clientes(\?.*)?$'))
            customer = next(c for c in get('/customers') if c['full_name'] == 'Cliente Apresentação Final')
            page.goto(APP + '/pedidos/novo')
            page.get_by_label('Cliente').select_option(str(customer['id']))
            page.get_by_label('Endereço').fill('Rua do Bom Jesus, 197 - Recife Antigo, Recife')
            page.get_by_label('Latitude').fill('-8.0631')
            page.get_by_label('Longitude').fill('-34.8711')
            page.get_by_label('Peso (kg)').fill('2,5')
            page.get_by_role('radio', name='Alta').click()
            for label, hours in [('Entregar a partir de', 1), ('Entregar até', 5)]:
                page.get_by_label(label).fill((datetime.now(RECIFE)+timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M'))
            page.get_by_role('button', name='Cadastrar pedido').click()
            page.wait_for_url(re.compile(r'/pedidos/\d+$'))
            order_id = int(page.url.rsplit('/', 1)[1])
            assert get(f'/orders/{order_id}')['status'] == 'PENDING'
            snap('ensaio_02_pedido.png')

        with stage('03 Atribuição automática com persistência'):
            page.goto(APP + '/pedidos')
            page.get_by_role('button', name='Atribuir automaticamente').click()
            page.get_by_role('button', name='Atribuir pedidos', exact=True).click()
            expect(page.get_by_role('heading', name='Resultado da atribuição automática')).to_be_visible()
            order = get(f'/orders/{order_id}')
            assert order['status'] == 'ASSIGNED', order
            courier = order['assigned_courier']['full_name']
            snap('ensaio_03_atribuicao.png')

        with stage('04 Rotas reais, heurística e mapa'):
            page.goto(APP + '/rotas')
            page.get_by_role('radio', name='Sequencial', exact=True).click()
            page.get_by_role('button', name='Gerar rotas').click()
            expect(page.locator('.stop-timing').first).to_be_visible(timeout=60000)
            routes = get('/routes')['routes']
            assert routes and any(s['order_id'] == order_id for r in routes for s in r['stops'])
            result['rotas'] = [{'id': r['id'], 'km': r['total_distance_km'], 'paradas': len(r['stops'])} for r in routes]
            page.locator('.routes-layout').scroll_into_view_if_needed()
            snap('ensaio_04_rotas.png')

        with stage('05 Entregador inicia rota e confirma entrega'):
            page.get_by_role('button', name='Sair', exact=True).click()
            login('entregador@rotacerta.com.br' if courier == 'Carla Entregadora' else 'entregador2@rotacerta.com.br')
            page.get_by_role('button', name='Iniciar rota').click()
            expect(page.get_by_role('button', name='Iniciar rota')).to_have_count(0)
            page.goto(APP + f'/pedidos/{order_id}')
            page.get_by_role('button', name='Confirmar entrega', exact=True).click()
            expect(page.get_by_text('Entrega confirmada.').first).to_be_visible()
            final = get(f'/orders/{order_id}')
            assert final['status'] == 'DELIVERED' and final['history'][-1]['changed_by'] == courier
            result['pedido'] = {'id': order_id, 'status_final': final['status'], 'autor_entrega': courier,
                                'historico': [e['status'] for e in final['history']]}
            snap('ensaio_05_entrega.png')

        with stage('06 Relatório, CSV e histórico operacional'):
            page.get_by_role('button', name='Sair', exact=True).click()
            login('admin@rotacerta.com.br')
            page.goto(APP + '/relatorios')
            expect(page.get_by_role('heading', name='Relatórios', exact=True)).to_be_visible()
            with page.expect_download() as download:
                page.get_by_role('button', name='Exportar CSV').click()
            assert download.value.suggested_filename.endswith('.csv')
            snap('ensaio_06_relatorio.png')
            page.goto(APP + '/historico')
            expect(page.get_by_role('heading', name='Histórico operacional', exact=True)).to_be_visible()
            snap('ensaio_07_historico.png')

        with stage('07 Comparação CPU real: mesma entrada, tempo e igualdade'):
            response = http.post('/optimizer/benchmark', headers=headers, json={
                'source': 'SYNTHETIC', 'couriers': 8, 'stops_per_courier': 60,
                'worker_counts': [1, 2, 4], 'include_gpu': False, 'repetitions': 3, 'seed': 12})
            response.raise_for_status()
            benchmark = response.json()
            assert len(benchmark['rows']) == 4 and all(r['same_routes'] is not False for r in benchmark['rows'])
            result['benchmark'] = benchmark
            result['hardware'] = get('/optimizer/capabilities')
            page.goto(APP + '/desempenho')
            expect(page.get_by_role('heading', name='Desempenho do otimizador', exact=True)).to_be_visible()
            expect(page.locator('.results')).to_be_visible()
            page.locator('.results').evaluate("el => el.scrollIntoView({block: 'start'})")
            snap('ensaio_08_desempenho.png')

        with stage('08 Navegação vertical 9:16 para preparação do vídeo'):
            page.set_viewport_size({'width': 450, 'height': 800})
            page.goto(APP + '/painel')
            expect(page.get_by_role('heading', name='Olá, Ana')).to_be_visible()
            snap('ensaio_09_vertical.png')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        result['erros_javascript'] = errors
        context.close(); browser.close()
    http.close()
    result['duracao_tecnica_s'] = round(time.perf_counter()-started, 3)
    result['tempo_roteiro_com_falas_planejado_s'] = 570
    result['limite_horizontal_s'] = 600
    result['limites'] = 'Tempo medido apenas da execução técnica automatizada; não comprova tempo de fala, participação dos integrantes ou ensaio humano completo. A entrada sintética é usada apenas para medir o otimizador; cadastro/atribuição/rota/entrega usam pedidos persistidos reais de demonstração.'
    result['situacao'] = 'Aprovado'
    (OUT / 'evidencias/ensaio_tecnico.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(f"Ensaio técnico: {result['duracao_tecnica_s']} s. Falas humanas pendentes.")


if __name__ == '__main__':
    main()
