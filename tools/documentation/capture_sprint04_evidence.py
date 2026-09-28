"""Captura as evidências da Sprint 04 com o sistema em execução.

Pré-requisitos: banco recém-criado, API em http://localhost:8000, frontend em
http://localhost:5173, Google Chrome e acesso à internet (mapa e busca de endereço).

O roteiro tem três fases, para demonstrar a persistência dos dados:

    python tools/documentation/capture_sprint04_evidence.py fluxo     # sistema no ar
    python tools/documentation/capture_sprint04_evidence.py sem-api   # API desligada
    python tools/documentation/capture_sprint04_evidence.py reinicio  # banco e API religados

Variáveis opcionais: APP_URL, API_URL e DATABASE_URL.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import psycopg
from playwright.sync_api import Browser, Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "sprint-04" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-04" / "evidencias"
APP_URL = os.environ.get("APP_URL", "http://localhost:5173")
API_URL = os.environ.get("API_URL", "http://localhost:8000")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://rotacerta:rotacerta_dev@localhost:5432/rotacerta"
).replace("postgresql+psycopg://", "postgresql://")
PASSWORD = "rotacerta123"
RECIFE = timezone(timedelta(hours=-3))
CUSTOMER = "Luciana Barros"
STATE_FILE = EVIDENCE / "estado.json"


def now_text() -> str:
    return datetime.now(RECIFE).strftime("%d/%m/%Y %H:%M:%S")


def shot(page: Page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(400)
    page.screenshot(path=ASSETS / name, full_page=full)
    print("imagem", name)


def tall_shot(page: Page, name: str) -> None:
    """Aumenta a janela até caber a página inteira, sem cortar mapas."""

    page.evaluate("document.activeElement && document.activeElement.blur()")
    size = page.viewport_size
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": size["width"], "height": min(max(height, size["height"]), 2200)})
    page.wait_for_timeout(700)
    shot(page, name)
    page.set_viewport_size(size)


def save_text(name: str, text: str, append: bool = False) -> None:
    path = EVIDENCE / name
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as file:
        file.write(text.rstrip() + "\n")
    print("texto", name)


def sql_table(query: str, params: tuple = ()) -> str:
    with psycopg.connect(DATABASE_URL) as connection:
        cursor = connection.execute(query, params)
        headers = [column.name for column in cursor.description]
        rows = [["" if value is None else str(value) for value in row] for row in cursor.fetchall()]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    line = lambda values: " | ".join(v.ljust(w) for v, w in zip(values, widths))  # noqa: E731
    body = [line(headers), "-+-".join("-" * w for w in widths), *(line(r) for r in rows)]
    body.append(f"({len(rows)} {'linha' if len(rows) == 1 else 'linhas'})")
    return "\n".join(body)


def order_sql(order_id: int) -> str:
    order = sql_table(
        """SELECT o.id, c.full_name AS cliente, o.status, u.full_name AS entregador, o.weight_kg AS peso_kg,
                  o.latitude, o.longitude
           FROM orders o
           JOIN customers c ON c.id = o.customer_id
           LEFT JOIN couriers co ON co.id = o.assigned_courier_id
           LEFT JOIN users u ON u.id = co.user_id
           WHERE o.id = %s""",
        (order_id,),
    )
    history = sql_table(
        """SELECT h.status, h.note AS observacao, u.full_name AS autor,
                  to_char(h.changed_at AT TIME ZONE 'America/Recife', 'DD/MM HH24:MI:SS') AS horario
           FROM order_status_history h LEFT JOIN users u ON u.id = h.changed_by
           WHERE h.order_id = %s ORDER BY h.changed_at, h.id""",
        (order_id,),
    )
    return (
        f"-- Pedido #{order_id} na tabela orders\n{order}\n\n"
        f"-- Histórico do pedido #{order_id} na tabela order_status_history\n{history}"
    )


def login(page: Page, email: str) -> None:
    page.goto(f"{APP_URL}/login")
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Senha").fill(PASSWORD)
    page.get_by_role("button", name="Entrar", exact=True).click()
    page.wait_for_url(re.compile(r"/(pedidos|entregas)"))


def sign_out(page: Page) -> None:
    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_role("heading", name="Entrar")).to_be_visible()


def desktop(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1366, "height": 860},
        device_scale_factor=1.5,
        locale="pt-BR",
        timezone_id="America/Recife",
    )
    return context.new_page()


def phone(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        locale="pt-BR",
        timezone_id="America/Recife",
    )
    return context.new_page()


def wait_tiles(page: Page) -> None:
    try:
        page.wait_for_function("document.querySelectorAll('.leaflet-tile-loaded').length >= 4", timeout=15000)
    except Exception:
        print("aviso: o mapa não carregou (sem internet?)")


def navigation_map(page: Page) -> None:
    """Desenha o mapa de navegação entre as telas do módulo."""

    nodes = {
        "login": (40, 60, "Login", "/login"),
        "cadastro": (40, 190, "Cadastrar negócio", "/cadastro"),
        "pedidos": (330, 60, "Pedidos", "/pedidos"),
        "novo": (620, 60, "Novo pedido", "/pedidos/novo"),
        "cliente": (620, 190, "Novo cliente", "/clientes/novo?voltar=…"),
        "detalhe": (910, 60, "Detalhe do pedido", "/pedidos/:id"),
        "editar": (910, 190, "Editar pedido", "/pedidos/:id/editar"),
        "clientes": (330, 190, "Clientes", "/clientes"),
        "usuarios": (330, 320, "Usuários (administrador)", "/usuarios"),
        "usuario": (620, 320, "Novo ou editar usuário", "/usuarios/novo"),
        "entregas": (330, 450, "Minhas entregas (entregador)", "/entregas"),
        "negado": (620, 450, "Acesso negado", "perfil sem permissão"),
        "inexistente": (910, 450, "Página não encontrada", "qualquer outro endereço"),
    }
    edges = [
        ("login", "pedidos"), ("login", "cadastro"), ("pedidos", "novo"), ("novo", "cliente"),
        ("novo", "detalhe"), ("pedidos", "detalhe"), ("detalhe", "editar"), ("pedidos", "clientes"),
        ("clientes", "cliente"), ("pedidos", "usuarios"), ("usuarios", "usuario"), ("login", "entregas"),
        ("entregas", "detalhe"),
    ]
    width, height = 220, 70
    shapes = []
    for a, b in edges:
        ax, ay = nodes[a][0] + width / 2, nodes[a][1] + height / 2
        bx, by = nodes[b][0] + width / 2, nodes[b][1] + height / 2
        shapes.append(
            f"<line x1='{ax}' y1='{ay}' x2='{bx}' y2='{by}' stroke='#9aa6a0' stroke-width='2' marker-end='url(#seta)'/>"
        )
    for key, (x, y, title, route) in nodes.items():
        fill = "#fbe4e2" if key in ("negado", "inexistente") else "#0b5d3b" if key in ("login", "cadastro") else "#ffffff"
        color = "#ffffff" if key in ("login", "cadastro") else "#1f2427"
        shapes.append(
            f"<rect x='{x}' y='{y}' width='{width}' height='{height}' rx='10' fill='{fill}' stroke='#1f2427' stroke-width='1.5'/>"
            f"<text x='{x + 14}' y='{y + 30}' font-size='17' font-weight='700' fill='{color}'>{title}</text>"
            f"<text x='{x + 14}' y='{y + 53}' font-size='14' fill='{color}' font-family='Consolas'>{route}</text>"
        )
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='1170' height='560' font-family='Arial'>"
        "<defs><marker id='seta' viewBox='0 0 10 10' refX='10' refY='5' markerWidth='8' markerHeight='8' orient='auto'>"
        "<path d='M0 0L10 5L0 10z' fill='#9aa6a0'/></marker></defs>"
        "<rect width='100%' height='100%' fill='#eef1ed'/>" + "".join(shapes) + "</svg>"
    )
    page.set_content(f"<body style='margin:0'>{svg}</body>")
    page.locator("svg").screenshot(path=ASSETS / "s04_00_mapa_navegacao.png")
    print("imagem s04_00_mapa_navegacao.png")


def delivery_window() -> tuple[str, str]:
    start = (datetime.now(RECIFE) + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=2)
    return start.strftime("%Y-%m-%dT%H:%M"), end.strftime("%Y-%m-%dT%H:%M")


def phase_flow() -> None:
    save_text("persistencia.txt", f"[{now_text()}] Fase 1: fluxo completo executado com o sistema no ar.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        page.on("dialog", lambda dialog: dialog.dismiss())
        navigation_map(page)

        # Validação do login
        page.goto(f"{APP_URL}/login")
        page.get_by_role("button", name="Entrar", exact=True).click()
        shot(page, "s04_01_login_validacao.png")

        # Atendente: lista e formulário vazio
        login(page, "atendente@rotacerta.com.br")
        page.wait_for_selector("tbody tr")
        shot(page, "s04_02_pedidos.png")
        page.get_by_role("link", name="Novo pedido").click()
        page.get_by_role("button", name="Cadastrar pedido").click()
        wait_tiles(page)
        tall_shot(page, "s04_03_pedido_validacao.png")

        # Cadastro do cliente a partir do pedido
        page.get_by_role("link", name="Cadastrar cliente").click()
        page.get_by_label("Nome").fill(CUSTOMER)
        page.get_by_label("Telefone").fill("98800-2040")
        page.get_by_role("button", name="Cadastrar cliente").click()
        expect(page.locator(".field-error")).to_contain_text("DDD")
        shot(page, "s04_04_cliente_validacao.png")
        page.get_by_label("Telefone").fill("81988002040")
        page.get_by_role("button", name="Cadastrar cliente").click()
        page.wait_for_url(re.compile(r"/pedidos/novo\?cliente=\d+"))

        # Busca de endereço
        page.get_by_label("Endereço").fill("Rua das Graças, Recife")
        page.get_by_role("button", name="Buscar endereço").click()
        page.wait_for_selector(".lookup-results, .alert.info", timeout=20000)
        wait_tiles(page)
        shot(page, "s04_05_busca_endereco.png")
        results = page.locator(".lookup-results button")
        if results.count():
            results.first.click()
        else:
            page.locator(".map-picker").click(position={"x": 260, "y": 100})

        # Regra de capacidade, validada antes de enviar
        start, end = delivery_window()
        page.get_by_label("Peso (kg)").fill("30")
        page.get_by_role("radio", name="Alta").click()
        page.get_by_label("Entregar a partir de").fill(start)
        page.get_by_label("Entregar até").fill(end)
        carla = page.locator("#campo-assigned_courier_id option", has_text="Carla Entregadora").get_attribute("value")
        page.get_by_label("Quem vai entregar").select_option(carla)
        page.get_by_role("button", name="Cadastrar pedido").click()
        expect(page.locator("#campo-assigned_courier_id-erro")).to_contain_text("capacidade")
        tall_shot(page, "s04_06_capacidade.png")

        page.get_by_label("Peso (kg)").fill("2,5")
        page.get_by_role("button", name="Cadastrar pedido").click()
        page.wait_for_url(re.compile(r"/pedidos/\d+$"))
        order_id = int(page.url.rsplit("/", 1)[1])
        expect(page.get_by_role("heading", name="Histórico")).to_be_visible()
        wait_tiles(page)
        tall_shot(page, "s04_07_pedido_criado.png")
        save_text("sql_pedido_criado.txt", order_sql(order_id))

        # Navegação protegida
        page.goto(f"{APP_URL}/usuarios")
        shot(page, "s04_08_acesso_negado.png")
        page.goto(f"{APP_URL}/relatorios-antigos")
        shot(page, "s04_09_pagina_inexistente.png")
        sign_out(page)

        # Entregador no celular
        mobile = phone(browser)
        login(mobile, "entregador@rotacerta.com.br")
        mobile.wait_for_selector(".delivery")
        shot(mobile, "s04_10_entregas_celular.png")
        card = mobile.locator(".delivery", has_text=CUSTOMER)
        card.get_by_role("button", name="Sair para entrega").click()
        expect(mobile.locator(".toast")).to_contain_text("iniciada")
        mobile.get_by_role("radio", name="Fora de serviço").click()
        expect(mobile.locator(".toast")).to_contain_text("Finalize")
        shot(mobile, "s04_11_indisponivel_erro.png")
        mobile.locator(".delivery", has_text=CUSTOMER).get_by_role("link", name="Ver detalhes").click()
        mobile.wait_for_url(re.compile(rf"/pedidos/{order_id}$"))
        expect(mobile.get_by_role("heading", name="Histórico")).to_be_visible()
        mobile.get_by_role("button", name="Confirmar entrega").click()
        expect(mobile.locator(".toast")).to_contain_text("confirmada")
        mobile.wait_for_timeout(800)
        shot(mobile, "s04_12_entregador_detalhe.png", full=True)

        # Administrador: histórico completo, cancelamento, confirmação e erros de regra
        login(page, "admin@rotacerta.com.br")
        page.goto(f"{APP_URL}/pedidos/{order_id}")
        expect(page.locator(".timeline li")).to_have_count(4)
        wait_tiles(page)
        tall_shot(page, "s04_13_historico_completo.png")

        page.goto(f"{APP_URL}/pedidos?situacao=PENDING")
        page.wait_for_selector("tbody tr")
        shot(page, "s04_14_filtro_url.png")
        page.locator("tbody tr", has_text="Fernanda Lima").click()
        page.get_by_role("button", name="Cancelar pedido").click()
        page.get_by_role("button", name="Confirmar cancelamento").click()
        expect(page.locator("#campo-cancel_reason-erro")).to_be_visible()
        shot(page, "s04_15_cancelamento_validacao.png")
        page.get_by_label("Motivo do cancelamento").fill("Cliente pediu o cancelamento por telefone")
        page.get_by_role("button", name="Confirmar cancelamento").click()
        expect(page.locator(".toast")).to_contain_text("cancelado")
        shot(page, "s04_16_pedido_cancelado.png")

        page.get_by_role("link", name="Clientes").click()
        page.wait_for_selector("tbody tr")
        page.locator("tbody tr", has_text="Maria Silva").get_by_role("button", name="Excluir").click()
        expect(page.get_by_role("alertdialog")).to_be_visible()
        shot(page, "s04_17_confirmacao.png")
        page.get_by_role("button", name="Excluir cliente").click()
        expect(page.locator(".toast")).to_contain_text("não pode ser excluído")
        shot(page, "s04_18_cliente_com_pedidos.png")

        maria = page.locator("tbody tr", has_text="Maria Silva")
        maria.get_by_role("link", name="Novo pedido").click()
        page.get_by_label("Latitude").fill("-8.9")
        page.get_by_label("Longitude").fill("-35.2")
        page.get_by_role("button", name="Cadastrar pedido").click()
        expect(page.locator("#campo-location-erro")).to_contain_text("km do ponto de saída")
        wait_tiles(page)
        tall_shot(page, "s04_19_raio_entrega.png")

        # Volta para a página pedida depois do login
        sign_out(page)
        page.goto(f"{APP_URL}/pedidos/{order_id}")
        expect(page.get_by_role("heading", name="Entrar")).to_be_visible()
        requested = page.url
        page.get_by_label("E-mail").fill("admin@rotacerta.com.br")
        page.get_by_label("Senha").fill(PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.wait_for_url(re.compile(rf"/pedidos/{order_id}$"))
        save_text(
            "navegacao.txt",
            f"Sem sessão, o endereço {APP_URL}/pedidos/{order_id} levou para {requested}.\n"
            f"Depois do login, o sistema abriu {page.url}, a página pedida originalmente.",
        )
        browser.close()

    STATE_FILE.write_text(json.dumps({"order_id": order_id}), encoding="utf-8")
    capture_api_rules()
    capture_tests()
    capture_commits()


def capture_api_rules() -> None:
    lines = []

    def record(label: str, response: httpx.Response) -> None:
        body = response.json() if response.content else None
        if isinstance(body, dict) and isinstance(body.get("detail"), list):
            detail = "; ".join(f"{item['loc'][-1]}: {item['msg']}" for item in body["detail"])
        elif isinstance(body, dict):
            detail = body.get("detail", "")
        else:
            detail = ""
        lines.append(f"{label}\n  -> HTTP {response.status_code} {detail}".rstrip())

    with httpx.Client(base_url=API_URL, timeout=15) as client:
        token = client.post("/auth/login", json={"email": "admin@rotacerta.com.br", "password": PASSWORD}).json()
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        customers = client.get("/customers", headers=headers).json()
        maria = next(c for c in customers if c["full_name"] == "Maria Silva")
        couriers = client.get("/couriers", headers=headers).json()
        diego = next(c for c in couriers if c["full_name"] == "Diego Entregador")
        base = {
            "customer_id": maria["id"],
            "delivery_address": "Av. Boa Viagem, 1200 - Boa Viagem, Recife - PE",
            "latitude": -8.1197,
            "longitude": -34.9006,
            "weight_kg": 2,
            "priority": 2,
        }
        record("POST /customers com telefone sem DDD", client.post("/customers", headers=headers, json={"full_name": "Teste", "phone": "98800-1000"}))
        record("POST /customers com nome sem letras", client.post("/customers", headers=headers, json={"full_name": "12"}))
        record("POST /customers repetindo nome e telefone", client.post("/customers", headers=headers, json={"full_name": "maria silva", "phone": "81988001001"}))
        record("POST /users com senha sem números", client.post("/users", headers=headers, json={"full_name": "Novo Usuário", "email": "novo@rotacerta.com.br", "password": "somenteletras", "role": "ATTENDANT"}))
        record("POST /orders com peso de 600 kg", client.post("/orders", headers=headers, json={**base, "weight_kg": 600}))
        record("POST /orders com fim da janela antes do início", client.post("/orders", headers=headers, json={**base, "desired_start": "2030-01-01T15:00:00Z", "desired_end": "2030-01-01T14:00:00Z"}))
        record("POST /orders com horário final no passado", client.post("/orders", headers=headers, json={**base, "desired_start": "2020-01-01T10:00:00Z", "desired_end": "2020-01-01T12:00:00Z"}))
        record("POST /orders fora do raio de entrega", client.post("/orders", headers=headers, json={**base, "latitude": -8.9, "longitude": -35.2}))
        record(f"POST /orders para {diego['full_name']} com 45 kg", client.post("/orders", headers=headers, json={**base, "weight_kg": 45, "assigned_courier_id": diego["id"]}))
        record("DELETE /customers de cliente com pedidos", client.delete(f"/customers/{maria['id']}", headers=headers))
        record("GET /geocode com texto curto", client.get("/geocode", headers=headers, params={"q": "Rua"}))
    save_text("api_validacoes.txt", "\n".join(lines))


def capture_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "backend/tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = "\n".join(line for line in result.stderr.splitlines() if " ... " in line or line.startswith(("Ran ", "OK", "FAILED")))
    save_text("testes.txt", "$ python -m unittest discover backend/tests -v\n" + output)


def capture_commits() -> None:
    log = subprocess.run(
        ["git", "log", "--reverse", "--format=%h %ad %s", "--date=format:%d/%m %H:%M", "master..HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    save_text("commits.txt", "$ git log --reverse master..HEAD\n" + log)


def phase_without_api() -> None:
    save_text("persistencia.txt", f"[{now_text()}] Fase 2: tentativa de uso com a API desligada.", append=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        page.goto(f"{APP_URL}/login")
        page.get_by_label("E-mail").fill("admin@rotacerta.com.br")
        page.get_by_label("Senha").fill(PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        expect(page.locator(".alert.error")).to_contain_text("servidor")
        shot(page, "s04_20_api_fora.png")
        browser.close()


def phase_after_restart() -> None:
    order_id = json.loads(STATE_FILE.read_text(encoding="utf-8"))["order_id"]
    save_text("persistencia.txt", f"[{now_text()}] Fase 3: sistema reaberto; consulta ao pedido #{order_id}.", append=True)
    health = httpx.get(f"{API_URL}/health", timeout=10).json()
    save_text("persistencia.txt", f"GET /health -> {health}", append=True)
    save_text("sql_apos_reinicio.txt", order_sql(order_id))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        login(page, "admin@rotacerta.com.br")
        page.goto(f"{APP_URL}/pedidos/{order_id}")
        expect(page.locator(".timeline li")).to_have_count(4)
        wait_tiles(page)
        tall_shot(page, "s04_21_apos_reinicio.png")
        browser.close()


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    phases = {"fluxo": phase_flow, "sem-api": phase_without_api, "reinicio": phase_after_restart}
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase not in phases:
        raise SystemExit(f"Informe a fase: {', '.join(phases)}")
    phases[phase]()


if __name__ == "__main__":
    main()
