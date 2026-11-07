"""Gera a arquitetura e o modelo de dados atualizados na Sprint 09.

Usa o mesmo estilo dos diagramas da Sprint 02 (generate_visuals.py). As tabelas
e colunas do MER correspondem a database/schema.sql na versão atual.

    backend\\.venv\\Scripts\\python.exe tools/documentation/generate_sprint09_diagrams.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

from generate_visuals import GREEN, LIGHT_BLUE, ORANGE, PALE, WHITE, arrow, box, title

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "sprint-09" / "assets"
PURPLE = "#6941C6"


def architecture() -> None:
    img = Image.new("RGB", (1900, 1060), WHITE)
    d = ImageDraw.Draw(img)
    title(d, "Arquitetura do RotaCerta - versão da Sprint 09",
          "API REST síncrona; otimização sequencial, paralela em CPU e em GPU; distâncias geográficas (Haversine)", 1900)
    box(d, (50, 200, 300, 470), "Usuários", ["Administrador", "Atendente", "Entregador (celular)"], fill=PALE, body_size=21)
    box(d, (365, 165, 735, 525), "Frontend", ["React 19 + TypeScript", "Vite", "Rotas protegidas por perfil",
                                                "Validação nos formulários", "Leaflet + OpenStreetMap"], fill=LIGHT_BLUE, body_size=21)
    box(d, (815, 150, 1225, 545), "API FastAPI", ["Autenticação JWT e senha Argon2", "Perfis e isolamento por estabelecimento",
                                                    "Validação Pydantic", "Erros 401, 403, 404 e 422 com mensagens", "OpenAPI em /docs"],
        fill="#EEF8F4", title_fill=GREEN, body_size=21)
    box(d, (1305, 150, 1850, 545), "Regras e serviços", ["Pedidos, clientes e usuários", "Carga, raio e janela de entrega",
                                                          "Atribuição automática", "Rotas, horários e esperas",
                                                          "Painel, relatórios, CSV e histórico"],
        fill="#FFF7ED", title_fill=ORANGE, body_size=21)
    box(d, (105, 700, 600, 990), "Localização", ["Busca de endereço (Nominatim)", "Distância Haversine, sem trânsito",
                                                  "Navegação externa por coordenadas"], fill=PALE, body_size=21)
    box(d, (705, 680, 1250, 1010), "Motor de otimização", ["Vizinho mais próximo + 2-opt", "Sequencial (linha de base)",
                                                            "Paralelo em CPU (processos)", "GPU com kernel CUDA próprio",
                                                            "Mesmas rotas em todos os modos"], fill="#F4F0FF", title_fill=PURPLE, body_size=21)
    box(d, (1355, 700, 1850, 990), "PostgreSQL", ["9 tabelas com integridade referencial", "Histórico de situação dos pedidos",
                                                  "Rotas, paradas e esperas", "Execuções e métricas do otimizador"], fill=PALE, body_size=21)
    arrow(d, (300, 335), (365, 335), "HTTPS")
    arrow(d, (735, 335), (815, 335), "JSON")
    arrow(d, (1225, 335), (1305, 335), "serviços")
    arrow(d, (1600, 545), (1600, 700), "SQL")
    arrow(d, (1380, 545), (1100, 680), "rotas")
    arrow(d, (1250, 850), (1355, 850), "métricas")
    arrow(d, (705, 850), (600, 850), "coordenadas")
    img.save(ASSETS / "arquitetura_v09.png", quality=95)


ENTITIES = {
    "establishments": ((60, 170, 560, 470), ["PK id", "name", "document", "depot_address",
                                             "depot_latitude / depot_longitude", "created_at"]),
    "users": ((760, 170, 1260, 470), ["PK id", "FK establishment_id", "full_name", "email (único)", "password_hash",
                                      "role (ADMIN, ATTENDANT, COURIER)", "active, created_at"]),
    "couriers": ((1460, 170, 1960, 470), ["PK id", "FK establishment_id", "FK user_id (único)", "load_capacity_kg",
                                          "availability", "created_at"]),
    "customers": ((60, 590, 560, 830), ["PK id", "FK establishment_id", "full_name", "phone", "created_at"]),
    "orders": ((760, 590, 1260, 1030), ["PK id", "FK establishment_id", "FK customer_id", "FK assigned_courier_id",
                                        "delivery_address", "latitude / longitude", "weight_kg (até 500)",
                                        "priority (1 a 3)", "desired_start / desired_end", "status", "created_at"]),
    "routes": ((1460, 590, 1960, 950), ["PK id", "FK establishment_id", "FK courier_id", "route_date", "status",
                                        "algorithm, execution_mode", "total_distance_km", "estimated_duration_min",
                                        "created_at"]),
    "order_status_history": ((60, 1150, 560, 1420), ["PK id", "FK order_id", "FK changed_by (users)", "status",
                                                     "note", "changed_at"]),
    "route_stops": ((760, 1150, 1260, 1470), ["PK id", "FK route_id", "FK order_id", "stop_sequence",
                                              "estimated_arrival", "waiting_minutes (Sprint 08)",
                                              "distance_from_previous_km", "status"]),
    "optimization_runs": ((1460, 1150, 1960, 1580), ["PK id", "FK establishment_id", "executed_at", "algorithm",
                                                     "execution_mode, worker_count", "order_count, courier_count",
                                                     "execution_time_ms", "total_distance_km",
                                                     "purpose, input_source, run_group", "speedup, efficiency",
                                                     "same_routes"]),
}


def er_diagram() -> None:
    img = Image.new("RGB", (2020, 1640), WHITE)
    d = ImageDraw.Draw(img)
    title(d, "Modelo de dados - versão da Sprint 09",
          "Tabelas de database/schema.sql. Todas as tabelas operacionais referenciam establishments (isolamento por negócio).", 2020)
    for name, (xy, items) in ENTITIES.items():
        box(d, xy, name, items, body_size=19, title_size=23, fill=PALE)
    arrow(d, (560, 300), (760, 300), "1:N")
    arrow(d, (1260, 300), (1460, 300), "1:0..1")
    arrow(d, (310, 470), (310, 590), "1:N")
    arrow(d, (560, 720), (760, 720), "1:N")
    arrow(d, (1520, 470), (1200, 590), "1:N")
    arrow(d, (1800, 470), (1800, 590), "1:N")
    arrow(d, (1010, 1030), (1010, 1150), "1:N")
    arrow(d, (760, 1000), (560, 1150), "1:N")
    arrow(d, (1560, 950), (1200, 1150), "1:N")
    img.save(ASSETS / "mer_v09.png", quality=95)


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    architecture()
    er_diagram()
    print(f"Diagramas gerados em {ASSETS}")
