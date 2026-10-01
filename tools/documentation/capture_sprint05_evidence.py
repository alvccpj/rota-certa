"""Captura as evidências da Sprint 05 com o sistema em execução.

Pré-requisitos: banco recém-criado (com os dados de demonstração da Sprint 05),
API em http://localhost:8000, frontend em http://localhost:5173, Google Chrome e
acesso à internet para os mapas. Para as medições do modo CUDA, a API precisa
rodar numa máquina com GPU NVIDIA e o CuPy instalado (backend/requirements-gpu.txt).

    python tools/documentation/capture_sprint05_evidence.py fluxo     # sistema no ar
    python tools/documentation/capture_sprint05_evidence.py reinicio  # depois de reiniciar a API
    python tools/documentation/capture_sprint05_evidence.py experimentos  # só as medições, com a máquina livre

Variáveis opcionais: APP_URL, API_URL e DATABASE_URL.
"""

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
ASSETS = ROOT / "docs" / "sprint-05" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-05" / "evidencias"
APP_URL = os.environ.get("APP_URL", "http://localhost:5173")
API_URL = os.environ.get("API_URL", "http://localhost:8000")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://rotacerta:rotacerta_dev@localhost:5432/rotacerta"
).replace("postgresql+psycopg://", "postgresql://")
PASSWORD = "rotacerta123"
RECIFE = timezone(timedelta(hours=-3))
MODES = {"SEQUENTIAL": "Sequencial", "PARALLEL": "CPU", "GPU": "GPU (CUDA)"}


def now_text() -> str:
    return datetime.now(RECIFE).strftime("%d/%m/%Y %H:%M:%S")


def shot(page: Page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(500)
    page.screenshot(path=ASSETS / name, full_page=full)
    print("imagem", name)


def tall_shot(page: Page, name: str) -> None:
    """Aumenta a janela até caber a página inteira, sem cortar mapas."""

    page.evaluate("document.activeElement && document.activeElement.blur()")
    size = page.viewport_size
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": size["width"], "height": min(max(height, size["height"]), 2600)})
    page.wait_for_timeout(900)
    shot(page, name)
    page.set_viewport_size(size)


def save_text(name: str, text: str, append: bool = False) -> None:
    with (EVIDENCE / name).open("a" if append else "w", encoding="utf-8") as file:
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


ROUTES_SQL = """SELECT r.id AS rota, u.full_name AS entregador, r.status, r.execution_mode AS modo,
                       r.total_distance_km AS km, r.estimated_duration_min AS minutos,
                       count(s.id) AS paradas
                FROM routes r
                JOIN couriers c ON c.id = r.courier_id
                JOIN users u ON u.id = c.user_id
                LEFT JOIN route_stops s ON s.route_id = r.id
                GROUP BY r.id, u.full_name ORDER BY r.id"""

STOPS_SQL = """SELECT s.route_id AS rota, s.stop_sequence AS ordem, s.order_id AS pedido, cu.full_name AS cliente,
                      s.distance_from_previous_km AS km_trecho,
                      to_char(s.estimated_arrival AT TIME ZONE 'America/Recife', 'HH24:MI') AS chegada,
                      s.status AS parada, o.status AS pedido_status
               FROM route_stops s
               JOIN orders o ON o.id = s.order_id
               JOIN customers cu ON cu.id = o.customer_id
               WHERE s.route_id = %s ORDER BY s.stop_sequence"""

RUNS_SQL = """SELECT id, purpose AS finalidade, input_source AS entrada, execution_mode AS modo,
                     worker_count AS workers, courier_count AS rotas, order_count AS paradas,
                     execution_time_ms AS tempo_ms, speedup, efficiency AS eficiencia, same_routes AS mesmas_rotas
              FROM optimization_runs ORDER BY id"""


def login(page: Page, email: str) -> None:
    page.goto(f"{APP_URL}/login")
    page.get_by_label("E-mail").fill(email)
    page.get_by_label("Senha").fill(PASSWORD)
    page.get_by_role("button", name="Entrar", exact=True).click()
    page.wait_for_url(re.compile(r"/(pedidos|entregas)"))


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


def api_login(client: httpx.Client, email: str) -> dict[str, str]:
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def generate(page: Page, mode: str) -> None:
    page.get_by_role("radio", name=mode).click()
    page.get_by_role("button", name="Gerar rotas").click()
    expect(page.locator(".run-result")).to_contain_text(mode)
    wait_tiles(page)


def benchmark_table(result: dict) -> str:
    lines = [
        f"Entrada: {'instância sintética' if result['source'] == 'SYNTHETIC' else 'pedidos atribuídos'} | "
        f"{result['courier_count']} rotas | {result['order_count']} paradas | mediana de {result['repetitions']} execuções",
        f"{'Configuração':<18} {'Tempo (ms)':>11} {'Speedup':>8} {'Eficiência':>11} {'Distância (km)':>15} {'Mesmas rotas':>13}",
    ]
    for row in result["rows"]:
        label = MODES[row["execution_mode"]]
        if row["execution_mode"] == "PARALLEL":
            label = f"CPU {row['worker_count']} processo(s)"
        efficiency = f"{row['efficiency'] * 100:.0f}%" if row["efficiency"] is not None else "-"
        lines.append(
            f"{label:<18} {row['execution_time_ms']:>11.2f} {row['speedup']:>7.2f}x {efficiency:>11} "
            f"{row['total_distance_km']:>15.3f} {'sim' if row['same_routes'] else 'não':>13}"
        )
    return "\n".join(lines)


def phase_flow() -> None:
    save_text("persistencia.txt", f"[{now_text()}] Fase 1: fluxo completo executado com o sistema no ar.")
    client = httpx.Client(base_url=API_URL, timeout=900)
    admin = api_login(client, "admin@rotacerta.com.br")
    attendant = api_login(client, "atendente@rotacerta.com.br")
    carla = api_login(client, "entregador@rotacerta.com.br")
    diego = api_login(client, "entregador2@rotacerta.com.br")
    capabilities = client.get("/optimizer/capabilities", headers=admin).json()
    save_text(
        "maquina.txt",
        f"GET /optimizer/capabilities\n{capabilities}\n\n"
        f"CPU: {capabilities['cpu_count']} núcleos lógicos | GPU: {capabilities['gpu_name'] or capabilities['gpu_reason']}",
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)

        # Rotas: antes e depois da geração, nos modos sequencial e GPU
        login(page, "admin@rotacerta.com.br")
        page.goto(f"{APP_URL}/rotas")
        expect(page.locator(".route-summary")).to_contain_text("aguardando rota")
        shot(page, "s05_01_rotas_antes.png")
        generate(page, "Sequencial")
        tall_shot(page, "s05_02_rotas_sequencial.png")
        generate(page, "GPU (CUDA)" if capabilities["gpu_available"] else "Paralelo em CPU")
        tall_shot(page, "s05_03_rotas_gpu.png")
        page.locator(".route-card-head", has_text="Carla Entregadora").click()
        page.wait_for_timeout(600)
        shot(page, "s05_04_rota_destacada.png")
        page.get_by_role("button", name="Alterar ponto de saída").click()
        wait_tiles(page)
        shot(page, "s05_05_ponto_saida.png")
        page.get_by_role("button", name="Cancelar").click()

        overview = client.get("/routes", headers=admin).json()
        routes = {route["courier"]["full_name"]: route for route in overview["routes"]}
        carla_route = routes["Carla Entregadora"]["id"]
        diego_route = routes["Diego Entregador"]["id"]
        save_text(
            "sql_rotas_geradas.txt",
            f"-- Rotas gravadas na tabela routes\n{sql_table(ROUTES_SQL)}\n\n"
            f"-- Paradas da rota {carla_route} na tabela route_stops\n{sql_table(STOPS_SQL, (carla_route,))}\n\n"
            f"-- Execuções registradas na tabela optimization_runs\n{sql_table(RUNS_SQL)}",
        )

        # Entregadora no celular: vê, inicia e executa a rota
        mobile = phone(browser)
        login(mobile, "entregador@rotacerta.com.br")
        expect(mobile.get_by_role("heading", name="Sua rota")).to_be_visible()
        wait_tiles(mobile)
        tall_shot(mobile, "s05_06_rota_entregador.png")
        mobile.get_by_role("button", name="Iniciar rota").click()
        expect(mobile.locator(".my-route")).to_contain_text("Em andamento")
        stops = client.get("/routes/me", headers=carla).json()["route"]["stops"]
        for stop in stops[:2]:
            client.patch(f"/orders/{stop['order_id']}/status", headers=carla, json={"status": "DELIVERED"})
        mobile.reload()
        expect(mobile.locator(".stop-list li.next")).to_be_visible()
        wait_tiles(mobile)
        tall_shot(mobile, "s05_07_rota_em_andamento.png")
        for stop in stops[2:]:
            client.patch(f"/orders/{stop['order_id']}/status", headers=carla, json={"status": "DELIVERED"})
        # Pedido que a demonstração já deixa em rota, fora da rota calculada.
        for order in client.get("/orders", headers=carla, params={"status": "IN_ROUTE"}).json():
            client.patch(f"/orders/{order['id']}/status", headers=carla, json={"status": "DELIVERED"})

        page.goto(f"{APP_URL}/rotas")
        expect(page.locator(".route-card", has_text="Carla Entregadora")).to_contain_text("Concluída")
        wait_tiles(page)
        tall_shot(page, "s05_08_rota_concluida.png")
        first_order = stops[0]["order_id"]
        save_text(
            "sql_rota_concluida.txt",
            f"-- Situação das rotas depois das entregas\n{sql_table(ROUTES_SQL)}\n\n"
            f"-- Paradas da rota {carla_route}\n{sql_table(STOPS_SQL, (carla_route,))}\n\n"
            f"-- Histórico do pedido #{first_order}\n"
            + sql_table(
                """SELECT h.status, h.note AS observacao, u.full_name AS autor,
                          to_char(h.changed_at AT TIME ZONE 'America/Recife', 'DD/MM HH24:MI:SS') AS horario
                   FROM order_status_history h LEFT JOIN users u ON u.id = h.changed_by
                   WHERE h.order_id = %s ORDER BY h.changed_at, h.id""",
                (first_order,),
            ),
        )

        # Regras de negócio chamando a API diretamente
        lines: list[str] = []

        def record(title: str, response: httpx.Response, summary=None) -> dict:
            body = response.json() if response.content else {}
            shown = summary(body) if summary and response.is_success else body.get("detail", body)
            lines.append(f"{title}\n  -> {response.status_code} {shown}\n")
            return body

        def new_order(courier_id: int, name: str, lat: float, lon: float) -> int:
            customer = client.post("/customers", headers=admin, json={"full_name": name, "phone": "(81) 98877-0000"}).json()
            payload = {
                "customer_id": customer["id"], "delivery_address": f"Endereço de {name}, Recife - PE",
                "latitude": lat, "longitude": lon, "weight_kg": 1, "priority": 2, "assigned_courier_id": courier_id,
            }
            return record(f"POST /orders atribuído ({name})", client.post("/orders", headers=admin, json=payload),
                          lambda b: f"pedido #{b['id']} {b['status']}")["id"]

        def routes_summary(body: dict) -> str:
            planned = [f"{r['courier']['full_name']} ({r['status']}, {len(r['stops'])} parada{'s' if len(r['stops']) != 1 else ''})" for r in body["routes"]]
            skipped = [f"{s['courier']['full_name']}: {s['reason']}" for s in body.get("skipped", [])]
            return f"rotas: {planned}; aguardando: {body['waiting_orders']}" + (f"; fora: {skipped}" if skipped else "")

        couriers = {c["full_name"]: c["id"] for c in client.get("/couriers", headers=admin).json()}
        record("POST /routes/generate pelo entregador", client.post("/routes/generate", headers=carla, json={}))
        record("PATCH /routes/{id}/start em rota já concluída", client.patch(f"/routes/{carla_route}/start", headers=carla))
        record("PATCH /routes/{id}/start da rota de outro entregador", client.patch(f"/routes/{diego_route}/start", headers=carla))
        record("PATCH /routes/{id}/start pelo próprio entregador", client.patch(f"/routes/{diego_route}/start", headers=diego),
               lambda b: f"rota {b['id']} {b['status']}, pedidos: {sorted({s['order_status'] for s in b['stops']})}")
        new_order(couriers["Diego Entregador"], "Rafaela Moura", -8.0420, -34.9050)
        carla_order = new_order(couriers["Carla Entregadora"], "Sérgio Lins", -8.0630, -34.8990)
        record("POST /routes/generate com rota em andamento", client.post("/routes/generate", headers=admin, json={"mode": "PARALLEL"}), routes_summary)
        diego_stop = client.get("/routes/me", headers=diego).json()["route"]["stops"][0]["order_id"]
        record("DELETE /orders de pedido em rota iniciada", client.delete(f"/orders/{diego_stop}", headers=admin))
        order = client.get(f"/orders/{carla_order}", headers=admin).json()
        move = {
            "customer_id": order["customer"]["id"], "delivery_address": order["delivery_address"],
            "latitude": order["latitude"], "longitude": order["longitude"], "weight_kg": order["weight_kg"],
            "priority": order["priority"], "assigned_courier_id": couriers["Diego Entregador"],
        }
        record("PUT /orders trocando o entregador de pedido em rota planejada", client.put(f"/orders/{carla_order}", headers=admin, json=move),
               lambda b: f"pedido #{b['id']} agora com {b['assigned_courier']['full_name']}")
        record("GET /routes depois da troca", client.get("/routes", headers=admin), routes_summary)
        new_order(couriers["Carla Entregadora"], "Tânia Prado", -8.0510, -34.8880)
        record("PATCH /couriers/me/availability OFFLINE (Carla)", client.patch("/couriers/me/availability", headers=carla, json={"availability": "OFFLINE"}),
               lambda b: b["availability"])
        record("POST /routes/generate com entregadora fora de serviço", client.post("/routes/generate", headers=admin, json={}))

        # A mesma recusa vista na interface
        page.goto(f"{APP_URL}/rotas")
        page.get_by_role("button", name="Gerar rotas").click()
        expect(page.locator(".toast")).to_contain_text("Nenhuma rota foi gerada")
        shot(page, "s05_09_regra_recusada.png")
        client.patch("/couriers/me/availability", headers=carla, json={"availability": "AVAILABLE"})

        record("POST /optimizer/benchmark pela atendente", client.post("/optimizer/benchmark", headers=attendant, json={}))
        record("POST /optimizer/benchmark com 64 x 500 paradas", client.post("/optimizer/benchmark", headers=admin,
               json={"couriers": 64, "stops_per_courier": 500}))
        record("PUT /establishment/depot pela atendente", client.put("/establishment/depot", headers=attendant,
               json={"depot_address": "Rua da Aurora, 325 - Recife", "latitude": -8.0593, "longitude": -34.8816}))
        save_text("regras.txt", "\n".join(lines))

        # Comparação de desempenho pela interface
        page.goto(f"{APP_URL}/desempenho")
        expect(page.locator(".machine")).to_be_visible()
        page.get_by_label("Entregadores (rotas)").fill("16")
        page.get_by_label("Paradas por entregador").fill("200")
        if capabilities["cpu_count"] >= 16:
            page.get_by_role("button", name="16", exact=True).click()
        page.get_by_role("button", name="Executar comparação").click()
        expect(page.locator(".toast")).to_contain_text("Comparação concluída", timeout=900000)
        page.mouse.move(0, 0)
        tall_shot(page, "s05_10_desempenho.png")
        page.locator(".chart-row").nth(2).hover()
        page.locator(".speedup-chart").screenshot(path=ASSETS / "s05_11_grafico_tooltip.png")
        print("imagem s05_11_grafico_tooltip.png")
        browser.close()

    run_experiments(client, admin, capabilities)
    capture_tests()
    capture_commits()


def run_experiments(client: httpx.Client, admin: dict[str, str], capabilities: dict) -> None:
    """Comparações com tamanhos crescentes e a mesma semente (pode ser repetida à parte)."""

    workers = [n for n in (1, 2, 4, 8, 16) if n <= capabilities["cpu_count"]]
    experiments = [f"[{now_text()}] Máquina: {capabilities['cpu_count']} núcleos lógicos, GPU {capabilities['gpu_name'] or 'indisponível'}\n"]
    real = client.post("/optimizer/benchmark", headers=admin, json={
        "source": "REAL", "worker_counts": [1, 2], "include_gpu": capabilities["gpu_available"], "repetitions": 5,
    })
    if real.is_success:
        experiments.append(benchmark_table(real.json()) + "\n")
    for couriers_count, stops_count in ((8, 50), (16, 100), (16, 200), (32, 300)):
        result = client.post("/optimizer/benchmark", headers=admin, json={
            "source": "SYNTHETIC", "couriers": couriers_count, "stops_per_courier": stops_count,
            "worker_counts": workers, "include_gpu": capabilities["gpu_available"], "repetitions": 3, "seed": 42,
        }).json()
        experiments.append(benchmark_table(result) + "\n")
    save_text("experimentos.txt", "\n".join(experiments))
    save_text("sql_execucoes.txt", "-- Execuções registradas na tabela optimization_runs\n" + sql_table(RUNS_SQL))


def phase_experiments() -> None:
    client = httpx.Client(base_url=API_URL, timeout=900)
    admin = api_login(client, "admin@rotacerta.com.br")
    run_experiments(client, admin, client.get("/optimizer/capabilities", headers=admin).json())
    capture_tests()
    capture_commits()


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


def phase_after_restart() -> None:
    save_text("persistencia.txt", f"[{now_text()}] Fase 2: API reiniciada; rotas e execuções consultadas de novo.", append=True)
    health = httpx.get(f"{API_URL}/health", timeout=10).json()
    save_text("persistencia.txt", f"GET /health -> {health}", append=True)
    counts = sql_table(
        """SELECT (SELECT count(*) FROM routes) AS rotas, (SELECT count(*) FROM route_stops) AS paradas,
                  (SELECT count(*) FROM optimization_runs) AS execucoes"""
    )
    save_text("persistencia.txt", f"-- Registros no banco depois do reinício\n{counts}", append=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = desktop(browser)
        login(page, "admin@rotacerta.com.br")
        page.goto(f"{APP_URL}/rotas")
        expect(page.locator(".route-card").first).to_be_visible()
        wait_tiles(page)
        tall_shot(page, "s05_12_rotas_apos_reinicio.png")
        browser.close()


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    phases = {"fluxo": phase_flow, "reinicio": phase_after_restart, "experimentos": phase_experiments}
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase not in phases:
        raise SystemExit(f"Informe a fase: {', '.join(phases)}")
    phases[phase]()


if __name__ == "__main__":
    main()
