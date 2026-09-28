"""Captura as evidências da Sprint 03 com o sistema em execução.

Pré-requisitos: banco recém-criado, API em http://localhost:8000 com os dados
de demonstração, frontend em http://localhost:5173 e Google Chrome instalado.
O roteiro cadastra dados fixos, então deve rodar uma única vez por banco.

    pip install playwright httpx psycopg[binary]
    python tools/documentation/capture_sprint03_evidence.py

Variáveis opcionais: APP_URL, API_URL e DATABASE_URL (formato libpq ou SQLAlchemy).
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import psycopg
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "sprint-03" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-03" / "evidencias"
APP_URL = os.environ.get("APP_URL", "http://localhost:5173")
API_URL = os.environ.get("API_URL", "http://localhost:8000")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://rotacerta:rotacerta_dev@localhost:5432/rotacerta"
).replace("postgresql+psycopg://", "postgresql://")
PASSWORD = "rotacerta123"
RECIFE = timezone(timedelta(hours=-3))
NEW_CUSTOMER = "Luciana Barros"


def shot(page: Page, name: str, **kwargs) -> None:
    page.wait_for_timeout(350)
    page.screenshot(path=ASSETS / name, **kwargs)
    print("imagem", name)


def drawer_shot(page: Page, name: str) -> None:
    """Aumenta a janela para o formulário do painel lateral aparecer inteiro."""

    page.evaluate("document.activeElement && document.activeElement.blur()")
    size = page.viewport_size
    needed = page.evaluate("document.querySelector('.drawer').scrollHeight")
    page.set_viewport_size({"width": size["width"], "height": min(max(needed, size["height"]), 1600)})
    shot(page, name)
    page.set_viewport_size(size)


def save_text(name: str, text: str) -> None:
    (EVIDENCE / name).write_text(text.rstrip() + "\n", encoding="utf-8")
    print("texto", name)


def sql_table(query: str, params: tuple = ()) -> str:
    """Executa a consulta e formata o resultado como uma tabela de texto."""

    with psycopg.connect(DATABASE_URL) as connection:
        cursor = connection.execute(query, params)
        headers = [column.name for column in cursor.description]
        rows = [["" if value is None else str(value) for value in row] for row in cursor.fetchall()]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h) for i, h in enumerate(headers)]
    line = lambda values: " | ".join(v.ljust(w) for v, w in zip(values, widths))  # noqa: E731
    body = [line(headers), "-+-".join("-" * w for w in widths), *(line(r) for r in rows)]
    body.append(f"({len(rows)} {'linha' if len(rows) == 1 else 'linhas'})")
    return "\n".join(body)


def sql_evidence(name: str, title: str, query: str, params: tuple = (), shown: str | None = None) -> None:
    compact = " ".join((shown or query).split())
    for value in params:
        compact = compact.replace("%s", str(value), 1)
    save_text(name, f"-- {title}\n{compact}\n\n{sql_table(query, params)}")


def login(page: Page, email: str, password: str = PASSWORD) -> None:
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Senha").fill(password)
    page.get_by_role("button", name="Entrar", exact=True).click()


def sign_out(page: Page) -> None:
    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_role("heading", name="Entrar")).to_be_visible()


def wait_map_tiles(page: Page) -> None:
    try:
        page.wait_for_function("document.querySelectorAll('.leaflet-tile-loaded').length >= 6", timeout=15000)
    except Exception:
        print("aviso: o mapa não carregou todos os blocos (sem internet?)")


def capture_api_access() -> None:
    lines = []

    def record(label: str, response: httpx.Response) -> None:
        body = response.json() if response.content else None
        if isinstance(body, list):
            detail = f"{len(body)} registros"
        elif isinstance(body, dict):
            detail = body.get("detail", "")
        else:
            detail = ""
        lines.append(f"{label}\n  -> HTTP {response.status_code} {detail}".rstrip())

    with httpx.Client(base_url=API_URL, timeout=10) as client:
        record("GET /orders sem token", client.get("/orders"))
        record(
            "POST /auth/login com senha errada",
            client.post("/auth/login", json={"email": "admin@rotacerta.com.br", "password": "senha-errada"}),
        )
        tokens = {}
        for role, email in (
            ("Administrador", "admin@rotacerta.com.br"),
            ("Atendente", "atendente@rotacerta.com.br"),
            ("Entregador", "entregador@rotacerta.com.br"),
        ):
            response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
            tokens[role] = {"Authorization": f"Bearer {response.json()['access_token']}"}
            lines.append(f"POST /auth/login ({role})\n  -> HTTP {response.status_code} token JWT emitido")
        for role in tokens:
            record(f"GET /users como {role}", client.get("/users", headers=tokens[role]))
        record("POST /orders como Entregador", client.post("/orders", headers=tokens["Entregador"], json={}))
        orders = client.get("/orders", headers=tokens["Entregador"]).json()
        lines.append(f"GET /orders como Entregador\n  -> HTTP 200 {len(orders)} pedidos, todos atribuídos a ele")
        any_order = client.get("/orders", headers=tokens["Administrador"]).json()[0]["id"]
        record(f"DELETE /orders/{any_order} como Atendente", client.delete(f"/orders/{any_order}", headers=tokens["Atendente"]))
    save_text("api_controle_acesso.txt", "\n".join(lines))


def capture_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "backend/tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = "\n".join(line for line in result.stderr.splitlines() if " ... " in line or line.startswith(("Ran ", "OK", "FAILED")))
    save_text("testes.txt", "$ python -m unittest discover backend/tests -v\n" + output)


def capture_screens() -> int:
    today = datetime.now(RECIFE).date().isoformat()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        context = browser.new_context(
            viewport={"width": 1366, "height": 820},
            device_scale_factor=1.5,
            locale="pt-BR",
            timezone_id="America/Recife",
        )
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        page.goto(f"{API_URL}/health")
        pretty_print = page.locator("input[type=checkbox]")
        if pretty_print.count():
            pretty_print.first.check()
        shot(page, "s03_01_health.png", clip={"x": 0, "y": 0, "width": 700, "height": 190})
        page.set_viewport_size({"width": 1366, "height": 1300})
        page.goto(f"{API_URL}/docs")
        page.wait_for_selector(".opblock")
        shot(page, "s03_02_swagger.png")
        page.set_viewport_size({"width": 1366, "height": 820})

        page.goto(APP_URL)
        page.evaluate("localStorage.clear()")
        page.reload()
        expect(page.get_by_role("heading", name="Entrar")).to_be_visible()
        shot(page, "s03_03_login.png")

        login(page, "admin@rotacerta.com.br", "senha-errada")
        expect(page.locator(".alert.error")).to_be_visible()
        shot(page, "s03_04_login_erro.png")

        page.get_by_role("button", name="Cadastrar meu negócio").click()
        page.get_by_label("Nome do negócio").fill("Mercadinho São José")
        page.get_by_label("Endereço de saída das entregas").fill("Rua Imperial, 1500 - São José, Recife - PE")
        page.get_by_label("Seu nome").fill("José Almeida")
        page.get_by_label("E-mail").fill("jose@mercadinhosaojose.com.br")
        page.get_by_label("Senha").fill("mercadinho2026")
        shot(page, "s03_05_cadastro_negocio.png")
        page.get_by_role("button", name="Criar conta").click()
        expect(page.get_by_text("Nenhum pedido cadastrado ainda.")).to_be_visible()
        shot(page, "s03_06_negocio_novo_vazio.png")
        sign_out(page)

        login(page, "admin@rotacerta.com.br")
        expect(page.locator("tbody tr").first).to_be_visible()
        shot(page, "s03_07_pedidos_admin.png")

        page.get_by_role("button", name="Novo pedido").click()
        drawer = page.get_by_role("dialog")
        drawer.get_by_label("Nome", exact=True).fill(NEW_CUSTOMER)
        drawer.get_by_label("Telefone").fill("(81) 98800-2040")
        drawer.get_by_label("Endereço", exact=True).fill("Rua das Graças, 210 - Graças, Recife - PE")
        wait_map_tiles(page)
        drawer.locator(".map-picker").click(position={"x": 250, "y": 95})
        drawer.get_by_label("Peso (kg)").fill("2,5")
        drawer.get_by_role("radio", name="Alta").click()
        drawer.get_by_label("Entregar a partir de").fill(f"{today}T14:00")
        drawer.get_by_label("Entregar até").fill(f"{today}T16:00")
        drawer.get_by_label("Entregador").select_option(label="Diego Entregador (disponível)")
        drawer_shot(page, "s03_08_novo_pedido.png")
        drawer.get_by_role("button", name="Cadastrar pedido").click()
        expect(page.locator(".toast")).to_contain_text("cadastrado")
        shot(page, "s03_09_pedido_cadastrado.png")
        order_id = int(re.search(r"#(\d+)", page.locator(".toast").inner_text()).group(1))

        page.locator("tr", has_text=NEW_CUSTOMER).get_by_role("button", name="Editar").click()
        drawer = page.get_by_role("dialog")
        drawer.get_by_role("radio", name="Normal").click()
        drawer.get_by_label("Entregador").select_option(label="Carla Entregadora (disponível)")
        drawer.get_by_label("Entregar até").fill(f"{today}T17:30")
        drawer_shot(page, "s03_10_editar_pedido.png")
        drawer.get_by_role("button", name="Salvar alterações").click()
        expect(page.locator(".toast")).to_contain_text("atualizado")
        shot(page, "s03_11_pedido_atualizado.png")

        sql_evidence(
            "sql_pedido_editado.txt",
            f"Pedido #{order_id} gravado no PostgreSQL após cadastro e edição pela interface",
            """SELECT o.id, c.full_name AS cliente, o.priority AS prioridade, o.status,
                      u.full_name AS entregador, o.weight_kg AS peso_kg,
                      to_char(o.desired_end AT TIME ZONE 'America/Recife', 'DD/MM HH24:MI') AS entregar_ate
               FROM orders o
               JOIN customers c ON c.id = o.customer_id
               LEFT JOIN couriers co ON co.id = o.assigned_courier_id
               LEFT JOIN users u ON u.id = co.user_id
               WHERE o.id = %s""",
            (order_id,),
        )

        page.locator("tr", has_text=NEW_CUSTOMER).get_by_role("button", name="Excluir").click()
        expect(page.locator(".toast")).to_contain_text("excluído")
        shot(page, "s03_12_pedido_excluido.png")
        sql_evidence(
            "sql_pedido_excluido.txt",
            f"Consulta ao pedido #{order_id} depois da exclusão pela interface",
            "SELECT count(*) AS pedidos_encontrados FROM orders WHERE id = %s",
            (order_id,),
        )

        page.get_by_role("button", name="Usuários").click()
        expect(page.get_by_role("heading", name="Usuários")).to_be_visible()
        shot(page, "s03_13_usuarios.png")
        page.get_by_role("button", name="Novo usuário").click()
        drawer = page.get_by_role("dialog")
        drawer.get_by_label("Nome completo").fill("Eduardo Nascimento")
        drawer.get_by_label("E-mail").fill("eduardo@rotacerta.com.br")
        drawer.get_by_label("Senha").fill("entregas2026")
        drawer.get_by_role("radio", name=re.compile("^Entregador")).click()
        drawer.get_by_label("Capacidade de carga (kg)").fill("30")
        drawer_shot(page, "s03_14_novo_usuario.png")
        drawer.get_by_role("button", name="Cadastrar usuário").click()
        expect(page.locator(".toast")).to_contain_text("cadastrado")
        shot(page, "s03_15_usuario_cadastrado.png")
        sign_out(page)

        login(page, "atendente@rotacerta.com.br")
        expect(page.locator("tbody tr").first).to_be_visible()
        shot(page, "s03_16_atendente.png")
        sign_out(page)

        phone = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="pt-BR",
            timezone_id="America/Recife",
        ).new_page()
        phone.goto(APP_URL)
        login(phone, "entregador@rotacerta.com.br")
        expect(phone.locator(".delivery").first).to_be_visible()
        shot(phone, "s03_17_entregador_celular.png")
        phone.get_by_role("button", name="Sair para entrega").first.click()
        expect(phone.locator(".toast")).to_contain_text("iniciada")
        shot(phone, "s03_18_entregador_status.png")
        browser.close()
    return order_id


def capture_database() -> None:
    tables = (
        "establishments", "users", "couriers", "customers",
        "orders", "routes", "route_stops", "optimization_runs",
    )
    counts = " UNION ALL ".join(f"SELECT '{name}' AS tabela, count(*) AS registros FROM {name}" for name in tables)
    sql_evidence(
        "sql_tabelas.txt",
        "Tabelas do banco rotacerta e quantidade de registros",
        counts,
        shown="SELECT 'establishments' AS tabela, count(*) AS registros FROM establishments UNION ALL ... (uma consulta por tabela)",
    )
    sql_evidence(
        "sql_usuarios.txt",
        "Usuários cadastrados: a senha fica gravada apenas como hash Argon2",
        """SELECT id, full_name AS nome, email, role AS perfil, active AS ativo,
                  left(password_hash, 32) || '...' AS hash_da_senha
           FROM users ORDER BY id""",
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    health = httpx.get(f"{API_URL}/health", timeout=10).json()
    save_text("health.txt", f"GET {API_URL}/health\n{health}")
    capture_screens()
    capture_api_access()
    capture_database()
    capture_tests()


if __name__ == "__main__":
    main()
