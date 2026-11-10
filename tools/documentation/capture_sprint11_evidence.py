"""Verifica os fluxos e captura as telas atuais usadas nos manuais da Sprint 11.

Use antes: tools/run_test_environment.py --schema sprint11_testes --api-port 8021 --web-port 5191
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("API_URL", "http://127.0.0.1:8021")
os.environ.setdefault("APP_URL", "http://127.0.0.1:5191")
os.environ.setdefault("EVIDENCE_DIR", str(ROOT / "docs/sprint-11"))

import capture_sprint10_evidence as previous
from playwright.sync_api import expect, sync_playwright


def capture_manual_screens():
    app, assets = previous.previous.APP, previous.previous.ASSETS
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1366, "height": 900}, locale="pt-BR", timezone_id="America/Recife")
        page.goto(app + "/login")
        expect(page.get_by_role("button", name="Entrar", exact=True)).to_be_visible()
        page.screenshot(path=str(assets / "manual_login.png"))
        page.get_by_label("E-mail").fill(previous.previous.ADMIN)
        page.get_by_label("Senha", exact=True).fill(previous.previous.PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.wait_for_url("**/painel")
        for path, heading, filename in [
            ("/clientes", "Clientes", "manual_clientes.png"),
            ("/usuarios", "Usuários", "manual_usuarios.png"),
            ("/pedidos/novo", "Novo pedido", "manual_novo_pedido.png"),
            ("/historico", "Histórico operacional", "manual_historico.png"),
            ("/desempenho", "Desempenho do otimizador", "manual_desempenho.png"),
        ]:
            page.goto(app + path)
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(assets / filename))
        browser.close()
    print("Capturas dos manuais gravadas com a aplicação real.")


def main():
    previous.main()
    capture_manual_screens()


if __name__ == "__main__":
    main()
