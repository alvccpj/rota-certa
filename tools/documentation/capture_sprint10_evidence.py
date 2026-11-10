"""Repete o roteiro anterior na RC e verifica a regressão visual no celular.

Requer tools/run_test_environment.py --schema sprint10_testes --api-port 8020 --web-port 5190.
"""

import json
import os
from pathlib import Path

os.environ.setdefault("API_URL", "http://127.0.0.1:8020")
os.environ.setdefault("APP_URL", "http://127.0.0.1:5190")
os.environ.setdefault("EVIDENCE_DIR", str(Path(__file__).resolve().parents[2] / "docs/sprint-10"))

import capture_sprint09_evidence as previous
from playwright.sync_api import expect, sync_playwright


def main():
    previous.main()
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for width in (320, 390, 768):
            context = browser.new_context(viewport={"width": width, "height": 844}, locale="pt-BR")
            page = context.new_page()
            page.goto(previous.APP + "/login")
            page.get_by_label("E-mail").fill(previous.ADMIN)
            page.get_by_label("Senha", exact=True).fill(previous.PASSWORD)
            page.get_by_role("button", name="Entrar", exact=True).click()
            page.wait_for_url("**/painel")
            page.goto(previous.APP + "/clientes")
            expect(page.locator("tbody tr").first).to_be_visible()
            measurements = page.evaluate("""() => {
                const table = document.querySelector('.table-wrap');
                return { viewport: innerWidth, document: document.documentElement.scrollWidth,
                    table_width: table.clientWidth, table_scroll: table.scrollWidth };
            }""")
            assert measurements["document"] == width, measurements
            assert measurements["table_scroll"] > measurements["table_width"], measurements
            page.locator(".table-wrap").evaluate("e => e.scrollLeft = e.scrollWidth")
            expect(page.get_by_role("button", name="Excluir", exact=True).first).to_be_in_viewport()
            if width == 390:
                page.screenshot(path=str(previous.ASSETS / "rc_clientes_celular.png"))
            checks.append({"largura_px": width, "situacao": "Aprovado", **measurements})
            context.close()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(previous.API + "/docs")
        expect(page.locator(".opblock").first).to_be_visible()
        page.screenshot(path=str(previous.ASSETS / "rc_swagger.png"))
        checks.append({"caso": "Swagger com endpoints carregados", "situacao": "Aprovado"})
        page.goto(previous.APP + "/login")
        page.get_by_label("E-mail").fill(previous.ADMIN)
        page.get_by_label("Senha", exact=True).fill(previous.PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.wait_for_url("**/painel")
        page.goto(previous.APP + "/rotas")
        expect(page.locator(".route-card").first).to_be_visible()
        page.locator(".routes-layout").evaluate("e => window.scrollTo(0, e.getBoundingClientRect().top + scrollY - 12)")
        page.wait_for_timeout(700)
        page.screenshot(path=str(previous.ASSETS / "rc_rotas_mapa.png"))
        browser.close()
    (previous.EVIDENCE / "interface_rc.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Regressão visual: 320, 390 e 768 px sem overflow; ações da tabela acessíveis por rolagem interna.")


if __name__ == "__main__":
    main()
