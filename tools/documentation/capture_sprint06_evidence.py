"""Captura evidências do Painel operacional e relatórios da Sprint 06.

Pré-requisitos: API em http://127.0.0.1:8000, frontend em
http://127.0.0.1:5173 e dados de demonstração carregados.

Variáveis opcionais: APP_URL e API_URL.
"""

import json
import os
import re
from pathlib import Path

import httpx
from playwright.sync_api import Browser, Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "sprint-06" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-06" / "evidencias"
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5173")
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
PASSWORD = "rotacerta123"


def save_text(name: str, content: str) -> None:
    (EVIDENCE / name).write_text(content.rstrip() + "\n", encoding="utf-8")
    print("texto", name)


def login(page: Page) -> None:
    page.goto(f"{APP_URL}/login")
    page.get_by_label("E-mail").fill("admin@rotacerta.com.br")
    page.get_by_label("Senha").fill(PASSWORD)
    page.get_by_role("button", name="Entrar", exact=True).click()
    page.wait_for_url(re.compile(r"/painel"))
    expect(page.get_by_role("heading", name=re.compile("Olá,"))).to_be_visible()


def desktop(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1366, "height": 900},
        device_scale_factor=1.5,
        locale="pt-BR",
        timezone_id="America/Recife",
        accept_downloads=True,
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


def api_login(client: httpx.Client) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": "admin@rotacerta.com.br", "password": PASSWORD})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    client = httpx.Client(base_url=API_URL, timeout=120)
    headers = api_login(client)
    before = client.get("/dashboard/summary", headers=headers).json()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        login(page)
        page.screenshot(path=ASSETS / "s06_01_painel_operacional.png", full_page=True)
        print("imagem s06_01_painel_operacional.png")

        generated = client.post("/routes/generate", headers=headers, json={"mode": "SEQUENTIAL"})
        generated.raise_for_status()
        page.get_by_role("button", name="Atualizar painel").click()
        routes_tile = page.locator(".dashboard-stat").nth(2)
        expect(routes_tile).to_contain_text("2")
        page.locator(".dashboard-grid").screenshot(path=ASSETS / "s06_02_integracao_modulos.png")
        print("imagem s06_02_integracao_modulos.png")

        with page.expect_download() as download_info:
            page.get_by_role("button", name="Exportar relatório CSV").click()
        download = download_info.value
        download_path = download.path()
        expect(page.locator(".toast")).to_contain_text("Relatório exportado")
        page.screenshot(path=ASSETS / "s06_03_relatorio_exportado.png")
        print("imagem s06_03_relatorio_exportado.png")

        mobile = phone(browser)
        login(mobile)
        mobile.get_by_role("button", name="Menu").click()
        expect(mobile.get_by_role("navigation", name="Seções")).to_be_visible()
        mobile.screenshot(path=ASSETS / "s06_04_navegacao_mobile.png")
        print("imagem s06_04_navegacao_mobile.png")
        browser.close()

    after = client.get("/dashboard/summary", headers=headers).json()
    report = client.get("/dashboard/report", headers=headers).json()
    save_text(
        "integracao.txt",
        "GET /dashboard/summary antes da geração\n"
        + json.dumps(before, ensure_ascii=False, indent=2)
        + "\n\nPOST /routes/generate -> "
        + f"{len(generated.json()['routes'])} rotas gravadas\n\n"
        + "GET /dashboard/summary depois da geração\n"
        + json.dumps(after, ensure_ascii=False, indent=2)
        + "\n\nGET /dashboard/report\n"
        + f"{len(report)} registros integrados e disponíveis para exportação CSV\n"
        + f"Arquivo baixado pelo navegador: {'sim' if download_path else 'não'}",
    )


if __name__ == "__main__":
    main()
