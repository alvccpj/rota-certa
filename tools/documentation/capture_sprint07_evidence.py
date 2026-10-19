"""Captura evidências funcionais da Sprint 07.

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
ASSETS = ROOT / "docs" / "sprint-07" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-07" / "evidencias"
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
        viewport={"width": 1440, "height": 960},
        device_scale_factor=1.25,
        locale="pt-BR",
        timezone_id="America/Recife",
        accept_downloads=True,
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
    generation = client.post("/routes/generate", headers=headers, json={"mode": "SEQUENTIAL"})
    generation.raise_for_status()

    summary = client.get("/dashboard/summary", headers=headers)
    summary.raise_for_status()
    report = client.get("/dashboard/report", headers=headers)
    report.raise_for_status()
    filtered_report = client.get(
        "/dashboard/report",
        headers=headers,
        params={"q": "Boa Viagem", "status": "ASSIGNED", "priority": 1},
    )
    filtered_report.raise_for_status()
    history = client.get("/dashboard/history", headers=headers)
    history.raise_for_status()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        login(page)
        page.screenshot(path=ASSETS / "s07_01_dashboard.png", full_page=True)
        print("imagem s07_01_dashboard.png")

        page.get_by_role("link", name="Relatórios", exact=True).click()
        page.wait_for_url(re.compile(r"/relatorios"))
        expect(page.get_by_role("heading", name="Relatórios")).to_be_visible()
        expect(page.locator("tbody tr").first).to_be_visible()
        page.screenshot(path=ASSETS / "s07_02_relatorios.png", full_page=True)
        print("imagem s07_02_relatorios.png")

        page.get_by_label("Pesquisa").fill("Boa Viagem")
        page.get_by_label("Situação").select_option("ASSIGNED")
        page.get_by_label("Prioridade").select_option("1")
        page.get_by_role("button", name="Aplicar filtros").click()
        expect(page.get_by_text("Maria Silva", exact=True)).to_be_visible()
        expect(page.get_by_text("Pedidos encontrados").locator("..")).to_contain_text("1")
        page.screenshot(path=ASSETS / "s07_03_pesquisa_filtros.png", full_page=True)
        print("imagem s07_03_pesquisa_filtros.png")

        with page.expect_download() as download_info:
            page.get_by_role("button", name="Exportar CSV").click()
        download = download_info.value
        csv_downloaded = download.path() is not None
        expect(page.locator(".toast")).to_contain_text("Relatório exportado com 1 pedido")
        page.screenshot(path=ASSETS / "s07_04_exportacao_csv.png", full_page=True)
        print("imagem s07_04_exportacao_csv.png")
        expect(page.locator(".toast")).to_be_hidden(timeout=10_000)

        page.get_by_role("link", name="Histórico", exact=True).click()
        page.wait_for_url(re.compile(r"/historico"))
        expect(page.get_by_role("heading", name="Histórico operacional")).to_be_visible()
        expect(page.get_by_text("Execução do otimizador", exact=True).first).to_be_visible()
        page.screenshot(path=ASSETS / "s07_05_historico_operacional.png", full_page=True)
        print("imagem s07_05_historico_operacional.png")

        page.get_by_label("Tipo de operação").select_option("OPTIMIZATION")
        page.get_by_role("button", name="Aplicar filtros").click()
        expect(page.locator(".operation-event").first).to_be_visible()
        page.screenshot(path=ASSETS / "s07_06_historico_filtrado.png", full_page=True)
        print("imagem s07_06_historico_filtrado.png")
        browser.close()

    history_payload = history.json()
    event_counts = {
        "ORDER_STATUS": sum(item["event_type"] == "ORDER_STATUS" for item in history_payload),
        "OPTIMIZATION": sum(item["event_type"] == "OPTIMIZATION" for item in history_payload),
    }
    save_text(
        "consultas_e_integracao.txt",
        "GET /dashboard/summary\n"
        + json.dumps(summary.json(), ensure_ascii=False, indent=2)
        + "\n\nGET /dashboard/report\n"
        + f"{len(report.json())} pedidos integrados.\n\n"
        + "GET /dashboard/report?q=Boa Viagem&status=ASSIGNED&priority=1\n"
        + json.dumps(filtered_report.json(), ensure_ascii=False, indent=2)
        + "\n\nGET /dashboard/history\n"
        + json.dumps(event_counts, ensure_ascii=False, indent=2)
        + "\n\nPOST /routes/generate\n"
        + f"{len(generation.json()['routes'])} rotas geradas e execução registrada.\n"
        + f"Arquivo CSV baixado pelo navegador: {'sim' if csv_downloaded else 'não'}",
    )


if __name__ == "__main__":
    main()
