"""Executa os casos de teste da Sprint 09 e salva as evidências.

Roda contra a aplicação real (API + frontend) ligada a um PostgreSQL com os dados
de demonstração recém-criados. Use um schema isolado para não alterar o banco de
desenvolvimento (passo a passo em docs/sprint-09/README.md, seção "Como reproduzir").

    backend\\.venv\\Scripts\\python.exe tools/documentation/capture_sprint09_evidence.py

Variáveis opcionais: API_URL (padrão http://127.0.0.1:8019) e APP_URL (padrão
http://127.0.0.1:5189). Cada caso registra procedimento, resultado esperado,
resultado obtido e situação. Uma falha é registrada e os demais casos continuam.
"""

import json
import os
import re
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "sprint-09"
ASSETS = OUT / "assets"
EVIDENCE = OUT / "evidencias"
API = os.environ.get("API_URL", "http://127.0.0.1:8019")
APP = os.environ.get("APP_URL", "http://127.0.0.1:5189")
PASSWORD = "rotacerta123"
RECIFE = timezone(timedelta(hours=-3))
STAMP = datetime.now().strftime("%H%M%S")

ADMIN = "admin@rotacerta.com.br"
ATTENDANT = "atendente@rotacerta.com.br"
COURIERS = {"Carla Entregadora": "entregador@rotacerta.com.br", "Diego Entregador": "entregador2@rotacerta.com.br"}

results: list[dict] = []
state: dict = {}


def record(case_id: str, kind: str, module: str, title: str, procedure: list[str], expected: str, shot: str | None = None):
    """Decorador: executa o caso, guarda o resultado obtido e a situação."""

    def run(fn):
        started = time.perf_counter()
        entry = {
            "id": case_id, "tipo": kind, "modulo": module, "titulo": title,
            "procedimento": procedure, "esperado": expected, "evidencia": None,
        }
        try:
            entry["obtido"] = fn()
            entry["situacao"] = "Aprovado"
        except Exception as exc:  # o caso falho é registrado e os demais continuam
            entry["obtido"] = f"{type(exc).__name__}: {exc}".strip()[:600]
            entry["situacao"] = "Reprovado"
            entry["detalhe"] = traceback.format_exc(limit=3)[-1500:]
        if shot and (ASSETS / shot).exists():
            entry["evidencia"] = f"assets/{shot}"
        entry["duracao_s"] = round(time.perf_counter() - started, 2)
        results.append(entry)
        print(f"{case_id:4} {entry['situacao']:9} {title}")
        return fn

    return run


def snap(page: Page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(350)
    page.screenshot(path=str(ASSETS / name), full_page=full)


class Api:
    def __init__(self) -> None:
        self.http = httpx.Client(base_url=API, timeout=120)
        self.tokens: dict[str, dict[str, str]] = {}

    def auth(self, email: str, password: str = PASSWORD) -> dict[str, str]:
        if email not in self.tokens:
            response = self.http.post("/auth/login", json={"email": email, "password": password})
            response.raise_for_status()
            self.tokens[email] = {"Authorization": "Bearer " + response.json()["access_token"]}
        return self.tokens[email]

    def call(self, method: str, path: str, who: str | None = ADMIN, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", None) or (self.auth(who) if who else {})
        return self.http.request(method, path, headers=headers, **kwargs)


def future(hours: float) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def local_input(value: datetime) -> str:
    """Valor aceito por <input type=datetime-local> no fuso de Recife."""

    return value.astimezone(RECIFE).strftime("%Y-%m-%dT%H:%M")


def detail(response: httpx.Response) -> str:
    data = response.json()
    if isinstance(data.get("detail"), list):
        return "; ".join(f"{'.'.join(map(str, issue['loc'][1:]))}: {issue['msg']}" for issue in data["detail"])
    return str(data.get("detail"))


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    api = Api()
    health = api.http.get("/health").json()
    assert health.get("dialect") == "postgresql", f"Use a API ligada ao PostgreSQL: {health}"
    capabilities = api.call("GET", "/optimizer/capabilities").json()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")

        def new_page(mobile: bool = False) -> Page:
            context = browser.new_context(
                viewport={"width": 390, "height": 844} if mobile else {"width": 1366, "height": 900},
                device_scale_factor=1, locale="pt-BR", timezone_id="America/Recife", accept_downloads=True,
            )
            return context.new_page()

        def ui_login(page: Page, email: str, password: str = PASSWORD) -> None:
            if "/login" not in page.url:
                page.goto(APP + "/login")
            page.get_by_label("E-mail").fill(email)
            page.get_by_label("Senha", exact=True).fill(password)
            page.get_by_role("button", name="Entrar", exact=True).click()

        def logged(email: str, mobile: bool = False) -> Page:
            page = new_page(mobile)
            ui_login(page, email)
            page.wait_for_url(re.compile(r"/(painel|entregas)$"))
            return page

        def path_of(page: Page) -> str:
            return re.sub(r"^https?://[^/]+", "", page.url)

        admin = logged(ADMIN)

        # ------------------------------------------------------------------ Funcionais
        @record("F01", "Funcional", "Autenticação", "Login com credenciais válidas",
                ["Abrir /login", f"Informar {ADMIN} e a senha de demonstração", "Clicar em Entrar"],
                "Usuário autenticado e levado ao painel com saudação pelo nome.", "f01_login_painel.png")
        def _():
            page = new_page()
            ui_login(page, ADMIN)
            page.wait_for_url("**/painel")
            expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()
            expect(page.locator(".dashboard-loading")).to_have_count(0, timeout=20000)
            snap(page, "f01_login_painel.png")
            token = page.evaluate("JSON.parse(localStorage.getItem('rotacerta.session')).access_token")
            me = api.call("GET", "/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
            state["login_page"] = page
            return f"Redirecionado para {path_of(page)}; saudação 'Olá, Ana'; /auth/me confirma {me['email']} ({me['role']})."

        @record("F02", "Funcional", "Autenticação", "Encerrar sessão",
                ["Com a sessão do F01, clicar em Sair", "Tentar abrir /painel pelo endereço"],
                "Sessão removida; /painel volta a exigir login.")
        def _():
            page = state["login_page"]
            page.get_by_role("button", name="Sair").click()
            page.wait_for_url("**/login")
            stored = page.evaluate("localStorage.getItem('rotacerta.session')")
            page.goto(APP + "/painel")
            page.wait_for_url("**/login")
            assert stored is None
            return f"Após Sair: {path_of(page)}; sessão local apagada ({stored!r}); /painel redirecionou ao login."

        @record("F03", "Funcional", "Autenticação", "Cadastro de novo negócio",
                ["Abrir /cadastro", "Preencher negócio, endereço de saída, nome, e-mail e senha válidos", "Clicar em Criar conta"],
                "Conta de administrador criada para um estabelecimento isolado, já autenticada no painel.", "f03_cadastro_negocio.png")
        def _():
            page = new_page()
            page.goto(APP + "/cadastro")
            email = f"paula.{STAMP}@padarianove.com.br"
            page.get_by_label("Nome do negócio").fill("Padaria Sprint Nove")
            page.get_by_label("Endereço de saída das entregas").fill("Rua do Hospício, 100 - Boa Vista, Recife")
            page.get_by_label("Seu nome").fill("Paula Teste")
            page.get_by_label("E-mail").fill(email)
            page.get_by_label("Senha", exact=True).fill("padaria123")
            page.get_by_role("button", name="Criar conta").click()
            page.wait_for_url("**/painel")
            expect(page.locator(".brand")).to_contain_text("Padaria Sprint Nove")
            snap(page, "f03_cadastro_negocio.png")
            state["other_admin"] = email
            api.auth(email, "padaria123")
            orders = api.call("GET", "/orders", who=email).json()
            return f"Conta criada e autenticada em {path_of(page)}; topo mostra 'Padaria Sprint Nove'; o novo negócio começa com {len(orders)} pedidos."

        @record("F04", "Funcional", "Clientes", "Cadastro de cliente",
                ["Abrir Clientes > Novo cliente", "Informar nome e telefone sem formatação", "Clicar em Cadastrar cliente"],
                "Cliente salvo e listado com telefone no formato (81) 99999-0909.", "f04_cliente_cadastrado.png")
        def _():
            admin.goto(APP + "/clientes/novo")
            admin.get_by_label("Nome").fill("Helena Sprint Nove")
            admin.get_by_label("Telefone").fill("81 99999 0909")
            admin.get_by_role("button", name="Cadastrar cliente").click()
            admin.wait_for_url(re.compile(r"/clientes(\?.*)?$"))
            row = admin.locator("tr").filter(has_text="Helena Sprint Nove")
            expect(row).to_contain_text("(81) 99999-0909")
            snap(admin, "f04_cliente_cadastrado.png")
            customer = next(c for c in api.call("GET", "/customers", params={"q": "Helena Sprint"}).json())
            state["customer"] = customer
            return f"Cliente #{customer['id']} listado com telefone {customer['phone']}."

        @record("F05", "Funcional", "Clientes", "Pesquisa de clientes",
                ["Em Clientes, digitar 'Helena' na busca"], "Somente clientes cujo nome ou telefone contém o termo são exibidos.")
        def _():
            admin.goto(APP + "/clientes")
            admin.get_by_placeholder("Buscar por nome ou telefone").fill("Helena")
            admin.wait_for_timeout(900)
            rows = admin.locator("tbody tr")
            texts = rows.all_inner_texts()
            assert texts and all("Helena" in text for text in texts), texts
            return f"{len(texts)} linha(s) exibida(s), todas contendo 'Helena'."

        @record("F06", "Funcional", "Clientes", "Edição de cliente",
                ["Na linha do cliente, clicar em Editar", "Trocar o telefone", "Clicar em Salvar alterações"],
                "Alteração persistida no banco e refletida na lista.")
        def _():
            admin.goto(APP + "/clientes")
            admin.locator("tr").filter(has_text="Helena Sprint Nove").get_by_role("link", name="Editar").click()
            admin.get_by_label("Telefone").fill("(81) 3333-0909")
            admin.get_by_role("button", name="Salvar alterações").click()
            admin.wait_for_url(re.compile(r"/clientes(\?.*)?$"))
            saved = api.call("GET", f"/customers/{state['customer']['id']}").json()
            assert saved["phone"] == "(81) 3333-0909", saved
            return f"API retorna telefone {saved['phone']} para o cliente #{saved['id']}."

        @record("F07", "Funcional", "Pedidos", "Cadastro de pedido",
                ["Abrir Pedidos > Novo pedido", "Escolher o cliente, endereço, latitude/longitude, peso '3,5', prioridade Alta e janela futura",
                 "Clicar em Cadastrar pedido"],
                "Pedido salvo como Pendente com os dados informados; tela do pedido aberta.", "f07_pedido_cadastrado.png")
        def _():
            admin.goto(APP + "/pedidos/novo")
            admin.get_by_label("Cliente").select_option(str(state["customer"]["id"]))
            admin.get_by_label("Endereço").fill("Rua do Bom Jesus, 197 - Recife Antigo, Recife")
            admin.get_by_label("Latitude").fill("-8.0631")
            admin.get_by_label("Longitude").fill("-34.8711")
            admin.get_by_label("Peso (kg)").fill("3,5")
            admin.get_by_role("radio", name="Alta").click()
            admin.get_by_label("Entregar a partir de").fill(local_input(future(1)))
            admin.get_by_label("Entregar até").fill(local_input(future(5)))
            admin.get_by_role("button", name="Cadastrar pedido").click()
            admin.wait_for_url(re.compile(r"/pedidos/\d+$"))
            order_id = int(path_of(admin).rsplit("/", 1)[1])
            expect(admin.get_by_role("heading", name=f"Pedido #{order_id}", exact=True)).to_be_visible()
            snap(admin, "f07_pedido_cadastrado.png")
            order = api.call("GET", f"/orders/{order_id}").json()
            assert (order["status"], order["weight_kg"], order["priority"]) == ("PENDING", 3.5, 1), order
            state["order"] = order_id
            return f"Pedido #{order_id}: situação {order['status']}, peso {order['weight_kg']} kg, prioridade {order['priority']}."

        @record("F08", "Funcional", "Pedidos", "Consulta de pedidos com filtro",
                ["Em Pedidos, clicar no filtro Pendente"], "A lista mostra apenas pedidos pendentes e o filtro fica no endereço da página.")
        def _():
            admin.goto(APP + "/pedidos")
            admin.get_by_role("group", name="Filtrar por situação").get_by_role("button", name=re.compile("^Pendente")).click()
            admin.wait_for_url(re.compile(r"situacao=PENDING"))
            rows = admin.locator("tbody tr").all_inner_texts()
            pending = [o for o in api.call("GET", "/orders").json() if o["status"] == "PENDING"]
            assert rows and all("Pendente" in row for row in rows), rows
            assert len(rows) == len(pending), (len(rows), len(pending))
            return f"{len(rows)} linhas exibidas, todas Pendente; API confirma {len(pending)} pendentes; endereço {path_of(admin)}."

        @record("F09", "Funcional", "Pedidos", "Edição de pedido",
                ["Abrir o pedido do F07 > Editar pedido", "Alterar o peso para 4", "Clicar em Salvar alterações"],
                "Novo peso persistido e exibido no pedido.")
        def _():
            admin.goto(APP + f"/pedidos/{state['order']}")
            admin.get_by_role("link", name="Editar pedido").click()
            admin.get_by_label("Peso (kg)").fill("4")
            admin.get_by_role("button", name="Salvar alterações").click()
            admin.wait_for_url(re.compile(rf"/pedidos/{state['order']}$"))
            saved = api.call("GET", f"/orders/{state['order']}").json()
            assert saved["weight_kg"] == 4.0, saved
            return f"API retorna peso {saved['weight_kg']} kg para o pedido #{state['order']}."

        @record("F10", "Funcional", "Pedidos", "Exclusão de pedido com confirmação",
                ["Criar pedido pendente", "Abrir o pedido e clicar em Excluir", "Confirmar em Excluir pedido"],
                "Diálogo de confirmação exibido; após confirmar, o pedido deixa de existir (HTTP 404).", "f10_confirmar_exclusao.png")
        def _():
            created = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua da Moeda, 50 - Recife",
                "latitude": -8.0638, "longitude": -34.8725, "weight_kg": 1, "priority": 3}).json()
            admin.goto(APP + f"/pedidos/{created['id']}")
            admin.get_by_role("button", name="Excluir", exact=True).click()
            expect(admin.get_by_role("alertdialog")).to_be_visible()
            snap(admin, "f10_confirmar_exclusao.png")
            admin.get_by_role("button", name="Excluir pedido").click()
            admin.wait_for_url(re.compile(r"/pedidos(\?.*)?$"))
            status = api.call("GET", f"/orders/{created['id']}").status_code
            assert status == 404
            return f"Pedido #{created['id']} excluído; consulta posterior retorna HTTP {status}."

        @record("F11", "Funcional", "Usuários", "Cadastro de usuário atendente",
                ["Abrir Usuários > Novo usuário", "Informar nome, e-mail, senha e perfil Atendente", "Clicar em Cadastrar usuário"],
                "Usuário criado e capaz de entrar com o perfil Atendente.")
        def _():
            email = f"lucas.{STAMP}@rotacerta.com.br"
            admin.goto(APP + "/usuarios/novo")
            admin.get_by_label("Nome completo").fill("Lucas Atendente Nove")
            admin.get_by_label("E-mail").fill(email)
            admin.get_by_label("Senha", exact=True).fill("lucas12345")
            admin.get_by_role("radio", name=re.compile("Atendente")).click()
            admin.get_by_role("button", name="Cadastrar usuário").click()
            admin.wait_for_url(re.compile(r"/usuarios$"))
            login = api.http.post("/auth/login", json={"email": email, "password": "lucas12345"})
            assert login.status_code == 200, login.text
            state["new_user"] = email
            return f"Login do novo usuário: HTTP {login.status_code}, perfil {login.json()['user']['role']}."

        @record("F12", "Funcional", "Usuários", "Desativação de usuário",
                ["Na lista de usuários, clicar em Desativar na linha do F11", "Confirmar"],
                "Usuário marcado como inativo e impedido de entrar.")
        def _():
            admin.goto(APP + "/usuarios")
            admin.locator("tr").filter(has_text="Lucas Atendente Nove").get_by_role("button", name="Desativar").click()
            admin.get_by_role("alertdialog").get_by_role("button", name="Desativar").click()
            expect(admin.locator("tr.inactive").filter(has_text="Lucas Atendente Nove")).to_be_visible()
            login = api.http.post("/auth/login", json={"email": state["new_user"], "password": "lucas12345"})
            assert login.status_code in (401, 403), login.text
            return f"Linha marcada como inativa; novo login retorna HTTP {login.status_code}: {detail(login)}"

        @record("F13", "Funcional", "Clientes", "Exclusão de cliente sem pedidos",
                ["Criar cliente sem pedidos", "Clicar em Excluir na linha", "Confirmar em Excluir cliente"],
                "Cliente removido (HTTP 404 na consulta seguinte).")
        def _():
            created = api.call("POST", "/customers", json={"full_name": f"Cliente Temporario {STAMP}"}).json()
            admin.goto(APP + "/clientes")
            admin.locator("tr").filter(has_text=created["full_name"]).get_by_role("button", name="Excluir").click()
            admin.get_by_role("button", name="Excluir cliente").click()
            expect(admin.locator("tr").filter(has_text=created["full_name"])).to_have_count(0)
            status = api.call("GET", f"/customers/{created['id']}").status_code
            assert status == 404
            return f"Cliente #{created['id']} removido da lista; consulta retorna HTTP {status}."

        @record("F14", "Funcional", "Atribuição", "Atribuição automática",
                ["Em Pedidos, clicar em Atribuir automaticamente", "Confirmar em Atribuir pedidos"],
                "Pedidos pendentes elegíveis recebem entregador; resultado e motivos exibidos.", "f14_atribuicao.png")
        def _():
            admin.goto(APP + "/pedidos")
            admin.get_by_role("button", name="Atribuir automaticamente").click()
            admin.get_by_role("button", name="Atribuir pedidos").click()
            expect(admin.get_by_role("heading", name="Resultado da atribuição automática")).to_be_visible()
            snap(admin, "f14_atribuicao.png")
            order = api.call("GET", f"/orders/{state['order']}").json()
            assert order["status"] == "ASSIGNED" and order["assigned_courier"], order
            state["courier_name"] = order["assigned_courier"]["full_name"]
            return f"Pedido #{state['order']} atribuído a {state['courier_name']}; histórico: '{order['history'][-1]['note']}'."

        @record("F15", "Funcional", "Rotas", "Geração de rotas no modo sequencial",
                ["Abrir Rotas", "Escolher Sequencial e clicar em Gerar rotas"],
                "Uma rota planejada por entregador, com paradas ordenadas, distância e previsão.", "f15_rotas_sequencial.png")
        def _():
            admin.goto(APP + "/rotas")
            admin.get_by_role("radio", name="Sequencial").click()
            admin.get_by_role("button", name="Gerar rotas").click()
            expect(admin.locator(".stop-timing").first).to_be_visible(timeout=60000)
            snap(admin, "f15_rotas_sequencial.png")
            routes = api.call("GET", "/routes").json()["routes"]
            state["sequential_km"] = {r["courier"]["full_name"]: r["total_distance_km"] for r in routes}
            summary = ", ".join(f"{r['courier']['full_name']}: {len(r['stops'])} paradas, {r['total_distance_km']} km" for r in routes)
            assert routes and all(r["execution_mode"] == "SEQUENTIAL" for r in routes)
            return f"{len(routes)} rotas SEQUENTIAL. {summary}."

        @record("F16", "Funcional", "Rotas", "Geração de rotas na GPU (CUDA)",
                ["Em Rotas, escolher GPU (CUDA) e clicar em Gerar rotas"],
                "Rotas geradas pelo kernel CUDA com a mesma distância total do modo sequencial.", "f16_rotas_gpu.png")
        def _():
            if not capabilities.get("gpu_available"):
                raise RuntimeError(f"GPU indisponível nesta máquina: {capabilities.get('gpu_reason')}")
            admin.goto(APP + "/rotas")
            admin.get_by_role("radio", name="GPU (CUDA)").click()
            admin.get_by_role("button", name="Gerar rotas").click()
            expect(admin.get_by_text("GPU (CUDA)").first).to_be_visible(timeout=60000)
            admin.wait_for_timeout(1500)
            snap(admin, "f16_rotas_gpu.png")
            routes = api.call("GET", "/routes").json()["routes"]
            gpu_km = {r["courier"]["full_name"]: r["total_distance_km"] for r in routes}
            assert all(r["execution_mode"] == "GPU" for r in routes), [r["execution_mode"] for r in routes]
            assert gpu_km == state["sequential_km"], (gpu_km, state["sequential_km"])
            return f"{len(routes)} rotas GPU em {capabilities['gpu_name']}; distâncias iguais ao sequencial: {gpu_km}."

        @record("F17", "Funcional", "Entregas", "Entregador inicia a rota e confirma a entrega",
                ["Entrar como o entregador do pedido no celular", "Clicar em Iniciar rota", "Abrir o pedido e clicar em Confirmar entrega"],
                "Pedido passa a Entregue com autor e horário no histórico.", "f17_entrega_confirmada.png")
        def _():
            courier = logged(COURIERS[state["courier_name"]], mobile=True)
            courier.get_by_role("button", name="Iniciar rota").click()
            expect(courier.get_by_role("button", name="Iniciar rota")).to_have_count(0, timeout=20000)
            courier.goto(APP + f"/pedidos/{state['order']}")
            courier.get_by_role("button", name="Confirmar entrega").click()
            expect(courier.get_by_text("Entrega confirmada.").first).to_be_visible()
            snap(courier, "f17_entrega_confirmada.png")
            order = api.call("GET", f"/orders/{state['order']}").json()
            last = order["history"][-1]
            assert order["status"] == "DELIVERED" and last["changed_by"] == state["courier_name"], order
            state["courier_page"] = courier
            return f"Pedido #{state['order']} {order['status']}; último evento por {last['changed_by']} em {last['changed_at']}."

        @record("F18", "Funcional", "Pedidos", "Cancelamento com justificativa",
                ["Criar pedido pendente", "Abrir o pedido > Cancelar pedido", "Informar o motivo e Confirmar cancelamento"],
                "Pedido Cancelado e motivo gravado no histórico.", "f18_cancelamento.png")
        def _():
            created = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua do Apolo, 120 - Recife",
                "latitude": -8.0612, "longitude": -34.8721, "weight_kg": 2, "priority": 2}).json()
            admin.goto(APP + f"/pedidos/{created['id']}")
            admin.get_by_role("button", name="Cancelar pedido").click()
            admin.get_by_label("Motivo do cancelamento").fill("Cliente desistiu da compra")
            admin.get_by_role("button", name="Confirmar cancelamento").click()
            expect(admin.get_by_text("Cliente desistiu da compra").first).to_be_visible()
            snap(admin, "f18_cancelamento.png")
            order = api.call("GET", f"/orders/{created['id']}").json()
            assert order["status"] == "CANCELLED" and order["history"][-1]["note"] == "Cliente desistiu da compra"
            state["cancelled"] = created["id"]
            return f"Pedido #{created['id']} {order['status']}; motivo no histórico: '{order['history'][-1]['note']}'."

        @record("F19", "Funcional", "Painel", "Painel com indicadores atualizados",
                ["Abrir Visão geral depois dos fluxos anteriores"], "Indicadores calculados com os dados atuais do estabelecimento.",
                "f19_painel.png")
        def _():
            admin.goto(APP + "/painel")
            expect(admin.get_by_role("heading", name="Fluxo dos pedidos")).to_be_visible()
            expect(admin.locator(".dashboard-loading")).to_have_count(0, timeout=20000)
            snap(admin, "f19_painel.png")
            summary = api.call("GET", "/dashboard/summary").json()
            orders, routes = summary["orders"], summary["routes"]
            assert orders["delivered"] >= 1 and orders["cancelled"] >= 1, orders
            return (f"Pedidos: {orders['total']} no período, {orders['delivered']} entregue(s), {orders['cancelled']} cancelado(s), "
                    f"conclusão {orders['completion_rate']}%; rotas: {routes['planned']} planejada(s), {routes['in_progress']} em andamento.")

        @record("F20", "Funcional", "Relatórios", "Relatório filtrado e exportação CSV",
                ["Abrir Relatórios", "Buscar 'Helena' e Aplicar filtros", "Clicar em Exportar CSV"],
                "Somente pedidos da cliente; o CSV baixado contém as mesmas linhas.", "f20_relatorio.png")
        def _():
            admin.goto(APP + "/relatorios")
            admin.get_by_placeholder("Pedido, cliente, telefone, endereço ou entregador").fill("Helena")
            admin.get_by_role("button", name="Aplicar filtros").click()
            expect(admin.locator("tbody tr").first).to_contain_text("Helena")
            rows = admin.locator("tbody tr").all_inner_texts()
            snap(admin, "f20_relatorio.png")
            with admin.expect_download() as download:
                admin.get_by_role("button", name="Exportar CSV").click()
            csv = Path(download.value.path()).read_text(encoding="utf-8-sig")
            lines = [line for line in csv.splitlines()[1:] if line.strip()]
            assert all("Helena" in row for row in rows) and len(lines) == len(rows), (rows, lines)
            return f"{len(rows)} linha(s) na tela e {len(lines)} no CSV '{download.value.suggested_filename}', todas da cliente Helena."

        @record("F21", "Funcional", "Histórico", "Histórico operacional",
                ["Abrir Histórico", "Buscar o número do pedido do F07"], "Eventos do pedido listados com autor e horário.")
        def _():
            admin.goto(APP + "/historico")
            search = admin.get_by_role("searchbox").first
            search.fill(str(state["order"]))
            search.press("Enter")
            admin.wait_for_timeout(1200)
            events = admin.locator(".operation-event").filter(has_text=f"Pedido #{state['order']}")
            count = events.count()
            authors = set(events.locator(".operation-author").all_inner_texts())
            assert count >= 4, count
            return f"{count} eventos do pedido #{state['order']}; responsáveis: {sorted(authors)}."

        @record("F22", "Funcional", "Desempenho", "Comparação de desempenho sequencial, CPU e GPU",
                ["Chamar POST /optimizer/benchmark com 8 entregadores x 60 paradas, 1, 2 e 4 processos e GPU"],
                "Tempos, speedup e eficiência calculados; todos os modos produzem as mesmas rotas.")
        def _():
            response = api.call("POST", "/optimizer/benchmark", json={
                "source": "SYNTHETIC", "couriers": 8, "stops_per_courier": 60, "worker_counts": [1, 2, 4],
                "include_gpu": True, "repetitions": 1, "seed": 9})
            assert response.status_code == 200, response.text
            data = response.json()
            rows = data["rows"]
            assert rows and all(r["same_routes"] is not False for r in rows), "algum modo produziu rotas diferentes"
            modes = {r["execution_mode"] for r in rows}
            assert {"SEQUENTIAL", "PARALLEL"} <= modes, modes
            state["benchmark"] = rows
            parts = [f"{r['execution_mode']} {r['worker_count']}p: {r['execution_time_ms']:.1f} ms, speedup {r['speedup']}, "
                     f"eficiência {r['efficiency']}" for r in rows]
            return f"{data['order_count']} pedidos sintéticos; " + "; ".join(parts)

        # ------------------------------------------------------------------ Validação
        @record("V01", "Validação", "Autenticação", "Login com campos obrigatórios vazios",
                ["Abrir /login", "Clicar em Entrar sem preencher"], "Mensagens junto aos campos, sem chamada ao servidor.",
                "v01_login_vazio.png")
        def _():
            page = new_page()
            page.goto(APP + "/login")
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page.get_by_text("Informe o e-mail.")).to_be_visible()
            expect(page.get_by_text("Informe a senha.")).to_be_visible()
            snap(page, "v01_login_vazio.png")
            focused = page.evaluate("document.activeElement.name")
            return f"Mensagens 'Informe o e-mail.' e 'Informe a senha.'; foco no campo {focused}."

        @record("V02", "Validação", "Autenticação", "Login com senha incorreta",
                ["Informar e-mail válido e senha errada", "Clicar em Entrar"], "Mensagem genérica, sem revelar qual dado está errado.",
                "v02_senha_incorreta.png")
        def _():
            page = new_page()
            page.goto(APP + "/login")
            page.get_by_label("E-mail").fill(ADMIN)
            page.get_by_label("Senha", exact=True).fill("senhaerrada1")
            page.get_by_role("button", name="Entrar", exact=True).click()
            expect(page.get_by_text("E-mail ou senha inválidos.")).to_be_visible()
            snap(page, "v02_senha_incorreta.png")
            return f"Exibido 'E-mail ou senha inválidos.'; permaneceu em {path_of(page)}."

        @record("V03", "Validação", "Autenticação", "Cadastro de negócio com formatos inválidos",
                ["Em /cadastro, informar e-mail 'paula@', senha 'abc' e endereço curto", "Clicar em Criar conta"],
                "Cada campo inválido mostra a orientação de correção.", "v03_cadastro_invalido.png")
        def _():
            page = new_page()
            page.goto(APP + "/cadastro")
            page.get_by_label("Nome do negócio").fill("P")
            page.get_by_label("Endereço de saída das entregas").fill("Rua")
            page.get_by_label("Seu nome").fill("9")
            page.get_by_label("E-mail").fill("paula@")
            page.get_by_label("Senha", exact=True).fill("abc")
            page.get_by_role("button", name="Criar conta").click()
            messages = page.locator(".field-error").all_inner_texts()
            snap(page, "v03_cadastro_invalido.png")
            assert any("e-mail válido" in m for m in messages) and any("8 caracteres" in m for m in messages), messages
            return " | ".join(messages)

        @record("V04", "Validação", "Clientes", "Cliente com nome e telefone inválidos",
                ["Em Novo cliente, informar nome '123' e telefone '123'", "Clicar em Cadastrar cliente"],
                "Mensagens para nome sem letras e telefone sem DDD.", "v04_cliente_invalido.png")
        def _():
            admin.goto(APP + "/clientes/novo")
            admin.get_by_label("Nome").fill("123")
            admin.get_by_label("Telefone").fill("123")
            admin.get_by_role("button", name="Cadastrar cliente").click()
            expect(admin.get_by_text("Use pelo menos duas letras.")).to_be_visible()
            expect(admin.get_by_text("Informe o telefone com DDD, por exemplo (81) 98800-1001.")).to_be_visible()
            snap(admin, "v04_cliente_invalido.png")
            return "Exibidos 'Use pelo menos duas letras.' e 'Informe o telefone com DDD, por exemplo (81) 98800-1001.'"

        @record("V05", "Validação", "Clientes", "Cliente duplicado",
                ["Enviar POST /customers com o mesmo nome e telefone do cliente do F06"], "HTTP 409 com mensagem de duplicidade.")
        def _():
            response = api.call("POST", "/customers", json={"full_name": "helena sprint nove", "phone": "8133330909"})
            assert response.status_code == 409, response.text
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V06", "Validação", "Pedidos", "Pedido com campos obrigatórios vazios",
                ["Em Novo pedido, informar só espaços no endereço", "Clicar em Cadastrar pedido"],
                "Resumo de erros, mensagem por campo e foco no primeiro campo inválido.", "v06_pedido_vazio.png")
        def _():
            admin.goto(APP + "/pedidos/novo")
            admin.get_by_label("Endereço").fill("      ")
            admin.get_by_label("Peso (kg)").fill("")
            admin.get_by_role("button", name="Cadastrar pedido").click()
            expect(admin.get_by_text(re.compile(r"Corrija os \d+ campos destacados"))).to_be_visible()
            messages = admin.locator(".field-error").all_inner_texts()
            snap(admin, "v06_pedido_vazio.png")
            assert "Escolha o cliente do pedido." in messages and "Informe o endereço com rua, número e bairro." in messages, messages
            return " | ".join(messages)

        @record("V07", "Validação", "Pedidos", "Peso fora dos limites",
                ["Em Novo pedido, informar peso 0 e depois 600", "Clicar em Cadastrar pedido a cada valor"],
                "Mensagens 'maior que 0' e 'máximo 500'.")
        def _():
            obtained = []
            for value, message in (("0", "Informe um valor maior que 0."), ("600", "O valor máximo é 500.")):
                admin.goto(APP + "/pedidos/novo")
                admin.get_by_label("Peso (kg)").fill(value)
                admin.get_by_role("button", name="Cadastrar pedido").click()
                expect(admin.get_by_text(message)).to_be_visible()
                obtained.append(f"{value} kg: '{message}'")
            api_response = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua da Aurora, 400 - Recife",
                "latitude": -8.059, "longitude": -34.882, "weight_kg": 501})
            obtained.append(f"API com 501 kg: HTTP {api_response.status_code}")
            assert api_response.status_code == 422
            return "; ".join(obtained)

        @record("V08", "Validação", "Pedidos", "Janela de entrega invertida",
                ["Em Novo pedido, informar fim antes do início", "Clicar em Cadastrar pedido"], "Mensagem 'O fim precisa ser depois do início.'",
                "v08_janela_invertida.png")
        def _():
            admin.goto(APP + "/pedidos/novo")
            admin.get_by_label("Entregar a partir de").fill(local_input(future(6)))
            admin.get_by_label("Entregar até").fill(local_input(future(4)))
            admin.get_by_role("button", name="Cadastrar pedido").click()
            expect(admin.get_by_text("O fim precisa ser depois do início.")).to_be_visible()
            admin.get_by_label("Entregar até").scroll_into_view_if_needed()
            snap(admin, "v08_janela_invertida.png")
            return "Exibido 'O fim precisa ser depois do início.' junto ao campo Entregar até."

        @record("V09", "Validação", "Pedidos", "Janela de entrega no passado (API)",
                ["POST /orders com desired_end uma hora atrás"], "HTTP 422 com orientação para informar horário futuro.")
        def _():
            response = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua da Aurora, 400 - Recife",
                "latitude": -8.059, "longitude": -34.882, "desired_end": future(-1).isoformat()})
            assert response.status_code == 422 and "já passou" in detail(response)
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V10", "Validação", "Pedidos", "Entrega fora do raio de atendimento",
                ["POST /orders com coordenadas de São Paulo"], "HTTP 422 informando a distância e o limite de 30 km.")
        def _():
            response = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Av. Paulista, 1000 - São Paulo",
                "latitude": -23.561, "longitude": -46.656})
            assert response.status_code == 422 and "30 km" in detail(response)
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V11", "Validação", "Pedidos", "Cancelamento sem motivo suficiente",
                ["Abrir pedido > Cancelar pedido", "Informar 'abc'", "Clicar em Confirmar cancelamento"],
                "Mensagem pedindo ao menos 5 caracteres; pedido continua ativo.", "v11_motivo_curto.png")
        def _():
            created = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua do Imperador, 20 - Recife",
                "latitude": -8.0625, "longitude": -34.8771}).json()
            admin.goto(APP + f"/pedidos/{created['id']}")
            admin.get_by_role("button", name="Cancelar pedido").click()
            admin.get_by_label("Motivo do cancelamento").fill("abc")
            admin.get_by_role("button", name="Confirmar cancelamento").click()
            expect(admin.get_by_text(re.compile("pelo menos 5 caracteres"))).to_be_visible()
            snap(admin, "v11_motivo_curto.png")
            status = api.call("GET", f"/orders/{created['id']}").json()["status"]
            assert status == "PENDING"
            return f"Mensagem exibida; pedido #{created['id']} continua {status}."

        @record("V12", "Validação", "Usuários", "E-mail já cadastrado (sem diferenciar maiúsculas)",
                ["POST /users com ADMIN@ROTACERTA.COM.BR"], "HTTP 409 informando e-mail em uso.")
        def _():
            response = api.call("POST", "/users", json={
                "full_name": "Outra Pessoa", "email": ADMIN.upper(), "password": "outra12345", "role": "ATTENDANT"})
            assert response.status_code == 409
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V13", "Validação", "Usuários", "Entregador sem capacidade e senha fraca",
                ["POST /users perfil Entregador sem capacidade", "POST /users com senha 'abcdefgh'"],
                "HTTP 422 com as duas regras explicadas.")
        def _():
            no_capacity = api.call("POST", "/users", json={
                "full_name": "Novo Entregador", "email": f"novo.{STAMP}@rotacerta.com.br", "password": "novo12345", "role": "COURIER"})
            weak = api.call("POST", "/users", json={
                "full_name": "Novo Atendente", "email": f"fraco.{STAMP}@rotacerta.com.br", "password": "abcdefgh", "role": "ATTENDANT"})
            assert no_capacity.status_code == 422 and weak.status_code == 422
            return f"Sem capacidade: {detail(no_capacity)} | Senha fraca: {detail(weak)}"

        @record("V14", "Validação", "Pedidos", "Endereço só com espaços (BUG-01 corrigido)",
                ["POST /orders com delivery_address de 8 espaços"], "HTTP 422; nada é gravado.")
        def _():
            before = len(api.call("GET", "/orders").json())
            response = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "        ", "latitude": -8.059, "longitude": -34.882})
            after = len(api.call("GET", "/orders").json())
            assert response.status_code == 422 and before == after
            return f"HTTP {response.status_code}: {detail(response)}; total de pedidos {before} -> {after}."

        @record("V15", "Validação", "Pedidos", "Janela com e sem fuso horário (BUG-02 corrigido)",
                ["POST /orders com início sem fuso e fim com -03:00"], "Pedido aceito e datas normalizadas em UTC, sem erro 500.")
        def _():
            start = future(3).replace(microsecond=0)
            end = (start + timedelta(hours=2)).astimezone(RECIFE)
            response = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua da Aurora, 400 - Recife",
                "latitude": -8.059, "longitude": -34.882,
                "desired_start": start.replace(tzinfo=None).isoformat(), "desired_end": end.isoformat()})
            assert response.status_code == 201, response.text
            saved = response.json()
            return f"HTTP 201; início {saved['desired_start']}, fim {saved['desired_end']}."

        @record("V16", "Validação", "API", "Identificador acima do limite do banco (BUG-03 corrigido)",
                ["GET /orders/99999999999999999999", "PUT /customers/9223372036854775808"], "HTTP 422 com mensagem, sem erro 500.")
        def _():
            first = api.call("GET", "/orders/99999999999999999999")
            second = api.call("PUT", "/customers/9223372036854775808", json={"full_name": "Fulano de Tal"})
            assert first.status_code == second.status_code == 422
            return f"HTTP {first.status_code} e {second.status_code}: {detail(first)}"

        @record("V17", "Validação", "Clientes", "Caractere de controle no nome (BUG-04 corrigido)",
                ["POST /customers com nome contendo o byte nulo (\\u0000)"], "Cliente salvo sem o caractere inválido, sem erro 500.")
        def _():
            response = api.call("POST", "/customers", json={"full_name": f"Jo\u0000ana Controle {STAMP}"})
            assert response.status_code == 201, response.text
            return f"HTTP 201; nome salvo: '{response.json()['full_name']}'."

        @record("V18", "Validação", "Relatórios", "Período de relatório invertido",
                ["GET /dashboard/report com data final anterior à inicial"], "HTTP 422 com mensagem sobre o período.")
        def _():
            response = api.call("GET", "/dashboard/report", params={"start": "2026-11-10", "end": "2026-11-01"})
            assert response.status_code == 422
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V19", "Validação", "Usuários", "Capacidade abaixo da carga ativa",
                ["PUT /users do entregador Diego com capacidade 0,1 kg"], "HTTP 422 explicando a carga ativa.")
        def _():
            users = api.call("GET", "/users").json()
            diego = next(u for u in users if u["full_name"] == "Diego Entregador")
            response = api.call("PUT", f"/users/{diego['id']}", json={
                "full_name": diego["full_name"], "email": diego["email"], "role": "COURIER", "active": True,
                "load_capacity_kg": 0.1})
            assert response.status_code in (409, 422), response.text
            return f"HTTP {response.status_code}: {detail(response)}"

        @record("V20", "Validação", "Autenticação", "Requisição sem token e com token adulterado",
                ["GET /orders sem Authorization", "GET /orders com token alterado"], "HTTP 401 nos dois casos.")
        def _():
            anonymous = api.call("GET", "/orders", who=None)
            token = api.auth(ADMIN)["Authorization"]
            tampered = api.call("GET", "/orders", headers={"Authorization": token[:-3] + "abc"})
            assert anonymous.status_code == tampered.status_code == 401
            return f"Sem token: HTTP {anonymous.status_code} ({detail(anonymous)}); adulterado: HTTP {tampered.status_code}."

        # ------------------------------------------------------------------ Navegação
        @record("N01", "Navegação", "Acesso", "Página protegida sem login",
                ["Sem sessão, abrir /relatorios"], "Redirecionamento para /login guardando a página pedida.")
        def _():
            page = new_page()
            page.goto(APP + "/relatorios")
            page.wait_for_url("**/login")
            saved = page.evaluate("history.state && history.state.usr && history.state.usr.from")
            state["anon_page"] = page
            assert saved == "/relatorios"
            return f"Redirecionado para {path_of(page)}; destino guardado: {saved}."

        @record("N02", "Navegação", "Acesso", "Volta à página pedida depois do login (BUG-06 corrigido)",
                ["Na tela do N01, entrar como administrador"], "Usuário levado a /relatorios, não ao painel.", "n02_retorno_pagina.png")
        def _():
            page = state["anon_page"]
            ui_login(page, ADMIN)
            page.wait_for_url("**/relatorios")
            expect(page.get_by_role("heading", name="Relatórios")).to_be_visible()
            snap(page, "n02_retorno_pagina.png")
            return f"Após o login: {path_of(page)}."

        @record("N03", "Navegação", "Acesso", "Página pedida não permitida ao perfil que entrou",
                ["Sem sessão, abrir /relatorios", "Entrar como entregador"], "Entregador levado a Minhas entregas, sem tela de acesso negado.")
        def _():
            page = new_page()
            page.goto(APP + "/relatorios")
            page.wait_for_url("**/login")
            ui_login(page, COURIERS["Diego Entregador"])
            page.wait_for_url("**/entregas")
            expect(page.get_by_role("heading", name="Minhas entregas")).to_be_visible()
            return f"Após o login: {path_of(page)}."

        menus = {
            "Administrador": (ADMIN, ["Visão geral", "Pedidos", "Rotas", "Relatórios", "Histórico", "Clientes", "Desempenho", "Usuários"]),
            "Atendente": (ATTENDANT, ["Visão geral", "Pedidos", "Rotas", "Relatórios", "Histórico", "Clientes"]),
            "Entregador": (COURIERS["Carla Entregadora"], ["Minhas entregas"]),
        }
        headings = {"Visão geral": re.compile("^Olá,"), "Pedidos": "Pedidos", "Rotas": "Rotas", "Relatórios": "Relatórios",
                    "Histórico": "Histórico operacional", "Clientes": "Clientes", "Desempenho": "Desempenho do otimizador",
                    "Usuários": "Usuários", "Minhas entregas": "Minhas entregas"}
        for number, (profile, (email, expected_links)) in enumerate(menus.items(), start=4):
            @record(f"N0{number}", "Navegação", "Menu", f"Menu e navegação do perfil {profile}",
                    [f"Entrar como {profile}", "Clicar em cada item do menu"],
                    f"Menu com {len(expected_links)} itens ({', '.join(expected_links)}); cada um abre a tela correspondente e fica destacado.",
                    f"n0{number}_menu_{profile.lower()}.png")
            def _(email=email, expected_links=expected_links, number=number, profile=profile):
                page = logged(email)
                links = page.locator("#main-navigation a").all_inner_texts()
                assert links == expected_links, links
                visited = []
                for label in expected_links:
                    page.locator("#main-navigation").get_by_role("link", name=label, exact=True).click()
                    expect(page.get_by_role("heading", name=headings[label]).first).to_be_visible()
                    expect(page.locator("#main-navigation a.active")).to_have_text(label)
                    visited.append(f"{label}->{path_of(page)}")
                snap(page, f"n0{number}_menu_{profile.lower()}.png")
                return "; ".join(visited)

        @record("N07", "Navegação", "Permissões", "Atendente abre tela exclusiva do administrador",
                ["Entrar como atendente", "Abrir /usuarios pelo endereço", "Clicar em Voltar para o início"],
                "Tela de acesso negado explicando quem usa a página; botão leva ao painel; API responde 403.", "n07_acesso_negado.png")
        def _():
            page = logged(ATTENDANT)
            page.goto(APP + "/usuarios")
            expect(page.get_by_role("heading", name="Esta página não está disponível para o seu perfil")).to_be_visible()
            snap(page, "n07_acesso_negado.png")
            page.get_by_role("link", name="Voltar para o início").click()
            page.wait_for_url("**/painel")
            status = api.call("GET", "/users", who=ATTENDANT).status_code
            assert status == 403
            return f"Acesso negado exibido; botão levou a {path_of(page)}; GET /users como atendente: HTTP {status}."

        @record("N08", "Navegação", "Permissões", "Entregador abre cadastro de pedido",
                ["Como entregador, abrir /pedidos/novo"], "Acesso negado; API bloqueia criação com 403.")
        def _():
            page = state["courier_page"]
            page.goto(APP + "/pedidos/novo")
            expect(page.get_by_role("heading", name="Esta página não está disponível para o seu perfil")).to_be_visible()
            status = api.call("POST", "/orders", who=COURIERS[state["courier_name"]], json={}).status_code
            assert status == 403
            return f"Tela de acesso negado; POST /orders como entregador: HTTP {status}."

        @record("N09", "Navegação", "Permissões", "Entregador abre pedido de outro entregador",
                ["Como entregador, abrir o endereço de um pedido atribuído a outro entregador"],
                "Mensagem de pedido não encontrado; API responde 404 sem expor dados.")
        def _():
            other = next(name for name in COURIERS if name != state["courier_name"])
            order = next(o for o in api.call("GET", "/orders").json() if (o["assigned_courier"] or {}).get("full_name") == other)
            page = state["courier_page"]
            page.goto(APP + f"/pedidos/{order['id']}")
            expect(page.get_by_role("heading", name=f"O pedido #{order['id']} não foi encontrado")).to_be_visible()
            status = api.call("GET", f"/orders/{order['id']}", who=COURIERS[state["courier_name"]]).status_code
            assert status == 404
            return f"Pedido #{order['id']} de {other}: tela 'não foi encontrado'; API HTTP {status}."

        @record("N10", "Navegação", "Rotas da aplicação", "Endereço inexistente",
                ["Logado, abrir /pagina-que-nao-existe", "Clicar em Ir para o início"], "Página não encontrada dentro do layout; botão leva ao início.",
                "n10_pagina_inexistente.png")
        def _():
            admin.goto(APP + "/pagina-que-nao-existe")
            expect(admin.get_by_role("heading", name="Não existe nada em /pagina-que-nao-existe")).to_be_visible()
            snap(admin, "n10_pagina_inexistente.png")
            admin.get_by_role("link", name="Ir para o início").click()
            admin.wait_for_url("**/painel")
            return f"Página não encontrada exibida; botão levou a {path_of(admin)}."

        @record("N11", "Navegação", "Rotas da aplicação", "Identificador inválido no endereço (BUG-05 corrigido)",
                ["Abrir /pedidos/abc, /pedidos/abc/editar, /clientes/abc/editar e /usuarios/abc/editar"],
                "Mensagem de registro não encontrado, e não 'Corrija o campo destacado'.", "n11_id_invalido.png")
        def _():
            obtained = []
            for path, text in [("/pedidos/abc", "O pedido #abc não foi encontrado"), ("/pedidos/abc/editar", "O pedido #abc não foi encontrado."),
                               ("/clientes/abc/editar", "Cliente não encontrado."), ("/usuarios/abc/editar", "Usuário não encontrado.")]:
                admin.goto(APP + path)
                expect(admin.get_by_text(text, exact=True).first).to_be_visible()
                assert admin.get_by_text("Corrija o campo destacado.").count() == 0
                obtained.append(f"{path}: '{text}'")
                if path == "/pedidos/abc":
                    snap(admin, "n11_id_invalido.png")
            return "; ".join(obtained)

        @record("N12", "Navegação", "Acesso", "Usuário logado abre login ou cadastro",
                ["Logado como administrador, abrir /login e /cadastro"], "Redirecionado ao painel.")
        def _():
            visited = []
            for path in ("/login", "/cadastro"):
                admin.goto(APP + path)
                admin.wait_for_url("**/painel")
                visited.append(f"{path}->{path_of(admin)}")
            return "; ".join(visited)

        @record("N13", "Navegação", "Menu", "Menu no celular",
                ["Em 390 px de largura, clicar em Menu", "Escolher Clientes"], "Menu abre, navega e fecha sozinho após a escolha.",
                "n13_menu_celular.png")
        def _():
            page = logged(ADMIN, mobile=True)
            nav = page.locator("#main-navigation")
            hidden_before = not nav.is_visible()
            page.get_by_role("button", name=re.compile("Menu")).click()
            expect(nav).to_be_visible()
            snap(page, "n13_menu_celular.png")
            page.get_by_role("link", name="Clientes").click()
            page.wait_for_url("**/clientes")
            expect(nav).to_be_hidden()
            overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert hidden_before and overflow <= 0
            return f"Fechado no início; aberto após Menu; navegou para {path_of(page)} e fechou; rolagem horizontal {overflow}px."

        @record("N14", "Navegação", "Fluxos", "Continuidade entre lista, detalhe e edição",
                ["Abrir um pedido pela lista", "Ir para Editar pedido e clicar em Cancelar", "Clicar no item Pedidos da trilha"],
                "Cada ação leva à tela esperada sem perder o contexto.")
        def _():
            created = api.call("POST", "/orders", json={
                "customer_id": state["customer"]["id"], "delivery_address": "Rua da Guia, 30 - Recife",
                "latitude": -8.0617, "longitude": -34.8709}).json()
            admin.goto(APP + "/pedidos")
            admin.get_by_role("link", name=f"#{created['id']}", exact=False).first.click()
            admin.wait_for_url(f"**/pedidos/{created['id']}")
            steps = [path_of(admin)]
            admin.get_by_role("link", name="Editar pedido").click()
            admin.wait_for_url(f"**/pedidos/{created['id']}/editar")
            steps.append(path_of(admin))
            admin.get_by_role("link", name="Cancelar").click()
            admin.wait_for_url(f"**/pedidos/{created['id']}")
            steps.append(path_of(admin))
            admin.locator("nav[aria-label]").filter(has_text="Pedidos").get_by_role("link", name="Pedidos").first.click()
            admin.wait_for_url(re.compile(r"/pedidos$"))
            steps.append(path_of(admin))
            return " -> ".join(steps)

        @record("N15", "Navegação", "Acesso", "Sessão expirada no meio do uso",
                ["Logado em Clientes, invalidar o token salvo no navegador", "Recarregar a página", "Entrar novamente"],
                "Aviso de sessão expirada no login e retorno à mesma página após entrar.", "n15_sessao_expirada.png")
        def _():
            page = logged(ADMIN)
            page.goto(APP + "/clientes?busca=Helena")
            # Espera a confirmação inicial da sessão (/auth/me), que regrava o token salvo.
            page.wait_for_load_state("networkidle")
            page.evaluate("""() => { const s = JSON.parse(localStorage.getItem('rotacerta.session'));
                s.access_token = s.access_token.slice(0, -4) + 'xxxx'; localStorage.setItem('rotacerta.session', JSON.stringify(s)); }""")
            page.reload()
            page.wait_for_url("**/login")
            expect(page.get_by_text("Sua sessão expirou. Entre novamente para continuar.")).to_be_visible()
            snap(page, "n15_sessao_expirada.png")
            ui_login(page, ADMIN)
            page.wait_for_url(re.compile(r"/clientes"))
            return f"Aviso exibido no login; após entrar, voltou para {path_of(page)}."

        @record("N16", "Navegação", "Permissões", "Isolamento entre estabelecimentos",
                ["Como administrador da Padaria (F03), abrir um pedido da RotaCerta pelo endereço"],
                "Pedido de outro negócio não é exibido; API responde 404.")
        def _():
            page = new_page()
            page.goto(APP + "/login")
            ui_login(page, state["other_admin"], "padaria123")
            page.wait_for_url("**/painel")
            page.goto(APP + f"/pedidos/{state['order']}")
            expect(page.get_by_role("heading", name=f"O pedido #{state['order']} não foi encontrado")).to_be_visible()
            status = api.call("GET", f"/orders/{state['order']}", who=state["other_admin"]).status_code
            listed = len(api.call("GET", "/customers", who=state["other_admin"]).json())
            assert status == 404 and listed == 0
            return f"Tela 'não foi encontrado'; API HTTP {status}; clientes visíveis para a Padaria: {listed}."

        @record("N17", "Navegação", "Fluxos", "Cadastrar cliente a partir do pedido e voltar",
                ["Em Novo pedido, clicar em Cadastrar cliente", "Salvar o cliente"], "Retorno automático ao Novo pedido com o fluxo preservado.")
        def _():
            admin.goto(APP + "/pedidos/novo")
            admin.get_by_role("link", name="Cadastrar cliente").click()
            admin.wait_for_url(re.compile(r"/clientes/novo\?voltar="))
            first = path_of(admin)
            admin.get_by_label("Nome").fill(f"Cliente Do Pedido {STAMP}")
            admin.get_by_role("button", name="Cadastrar cliente").click()
            admin.wait_for_url(re.compile(r"/pedidos/novo"))
            return f"{first} -> {path_of(admin)}"

        @record("N18", "Navegação", "Acesso", "Voltar do navegador depois de sair",
                ["Logado no painel, clicar em Sair", "Usar o botão Voltar do navegador"], "A área protegida não é reaberta.")
        def _():
            page = logged(ADMIN)
            page.goto(APP + "/pedidos")
            page.get_by_role("button", name="Sair").click()
            page.wait_for_url("**/login")
            page.go_back()
            page.wait_for_timeout(800)
            assert "/login" in page.url
            return f"Após Voltar: {path_of(page)}."

        @record("N19", "Navegação", "Menu", "Menu completo visível no desktop (BUG-09 corrigido)",
                ["Entrar como administrador em telas de 1024, 1280, 1366 e 1920 px", "Medir a posição de cada item do menu"],
                "Os 8 itens ficam inteiros na tela, sem rolagem escondida.", "n19_menu_completo.png")
        def _():
            obtained = []
            for width in (1024, 1280, 1366, 1920):
                context = browser.new_context(viewport={"width": width, "height": 700}, locale="pt-BR")
                page = context.new_page()
                ui_login(page, ADMIN)
                page.wait_for_url("**/painel")
                expect(page.locator("#main-navigation a")).to_have_count(8)
                cut = page.evaluate("""() => { const nav = document.querySelector('#main-navigation');
                    const links = [...nav.querySelectorAll('a')];
                    return { total: links.length, hidden: links.filter(a => { const r = a.getBoundingClientRect();
                        return r.left < 0 || r.right > window.innerWidth || r.width === 0; }).map(a => a.textContent),
                        scroll: nav.scrollWidth - nav.clientWidth }; }""")
                assert cut["total"] == 8 and not cut["hidden"] and cut["scroll"] <= 0, (width, cut)
                if width == 1366:
                    page.screenshot(path=str(ASSETS / "n19_menu_completo.png"), clip={"x": 0, "y": 0, "width": width, "height": 260})
                obtained.append(f"{width}px: {cut['total']} itens visíveis")
                context.close()
            return "; ".join(obtained)

        browser.close()

    approved =sum(1 for r in results if r["situacao"] == "Aprovado")
    summary = {
        "executado_em": datetime.now(RECIFE).isoformat(timespec="seconds"),
        "api": API, "app": APP, "banco": health, "gpu": {k: capabilities.get(k) for k in ("gpu_available", "gpu_name", "gpu_reason")},
        "total": len(results), "aprovados": approved, "reprovados": len(results) - approved,
        "por_tipo": {kind: {"total": sum(1 for r in results if r["tipo"] == kind),
                            "aprovados": sum(1 for r in results if r["tipo"] == kind and r["situacao"] == "Aprovado")}
                     for kind in ("Funcional", "Validação", "Navegação")},
        "casos": results,
    }
    (EVIDENCE / "casos_de_teste.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{approved}/{len(results)} casos aprovados. Registro em docs/sprint-09/evidencias/casos_de_teste.json")


if __name__ == "__main__":
    main()
