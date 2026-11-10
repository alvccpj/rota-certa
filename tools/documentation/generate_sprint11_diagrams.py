"""Gera os diagramas finais com Pillow; fontes Arial ou DejaVu Sans."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/final/assets"
BLUE, PALE, INK = "#173B67", "#f1f5f9", "#1d2433"


def font(size, bold=False):
    candidates = (["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
                  if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    candidates.append(str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf")))
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Instale Arial ou DejaVu Sans para renderizar os diagramas.")


def box(draw, xy, name, lines, body=24):
    x, y, right, bottom = xy
    draw.rounded_rectangle(xy, radius=14, fill=PALE, outline=BLUE, width=3)
    draw.rounded_rectangle((x, y, right, y + 55), radius=14, fill=BLUE)
    draw.rectangle((x, y + 30, right, y + 55), fill=BLUE)
    draw.text((x + 17, y + 13), name, font=font(27, True), fill="white")
    for i, line in enumerate(lines):
        draw.text((x + 17, y + 74 + i * (body + 12)), line, font=font(body), fill=INK)


def arrow(draw, start, end, label=""):
    draw.line((start, end), fill="#64748b", width=3)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    draw.polygon([end, (end[0]-15*math.cos(angle-.45), end[1]-15*math.sin(angle-.45)),
                  (end[0]-15*math.cos(angle+.45), end[1]-15*math.sin(angle+.45))], fill="#64748b")
    if label:
        center = ((start[0]+end[0])/2, (start[1]+end[1])/2)
        draw.text((center[0]+4, center[1]-30), label, font=font(21), fill=INK)


def heading(draw, title, subtitle):
    draw.text((50, 35), title, font=font(40, True), fill=BLUE)
    draw.text((50, 93), subtitle, font=font(23), fill="#475467")


def architecture():
    image = Image.new("RGB", (1900, 1050), "white")
    draw = ImageDraw.Draw(image)
    heading(draw, "Arquitetura final do RotaCerta", "Sprint 11 | 0.11.0-rc.1 | Componentes implementados e integrações efetivas")
    box(draw, (50, 180, 410, 490), "Pessoas e perfis", ["Administrador", "Atendente", "Entregador", "Navegador / celular"])
    box(draw, (500, 180, 900, 490), "Frontend React", ["TypeScript, Router, Vite", "Formulários e sessão local", "Leaflet e exportação CSV", "HTTP/JSON para a API"])
    box(draw, (1000, 180, 1400, 490), "API FastAPI", ["JWT e Argon2", "Pydantic e permissões", "Isolamento por negócio", "Rotas OpenAPI"])
    box(draw, (1500, 180, 1850, 490), "PostgreSQL", ["9 tabelas / 14 FKs", "Pedidos, rotas e eventos", "Sessões SQLAlchemy", "DDL e checks"] ,body=22)
    box(draw, (70, 680, 570, 980), "Serviços externos", ["OpenStreetMap: tiles no navegador", "Nominatim: busca feita pela API", "Google Maps: nova aba", "Sem OSRM ou trânsito ao vivo"],body=23)
    box(draw, (670, 680, 1220, 980), "Regras e serviços", ["Carga, raio, situação e horários", "Atribuição automática com transação", "Planejamento e execução das rotas", "Painel, relatórios e histórico"],body=23)
    box(draw, (1320, 680, 1850, 980), "Otimização", ["Vizinho mais próximo e 2-opt", "Haversine, sem treinamento de IA", "Sequencial / processos de CPU", "GPU CUDA opcional com CuPy"],body=23)
    arrow(draw,(410,330),(500,330));arrow(draw,(900,330),(1000,330),"HTTP")
    arrow(draw,(1400,330),(1500,330),"SQL")
    arrow(draw,(700,490),(350,680));arrow(draw,(1200,490),(970,680))
    arrow(draw,(1220,820),(1320,820),"cálculo")
    arrow(draw,(1040,490),(550,680))
    image.save(OUT / "arquitetura_v11.png")


def classes():
    image = Image.new("RGB", (2020, 1490), "white")
    draw = ImageDraw.Draw(image)
    heading(draw, "Classes de domínio implementadas", "Associações centrais de models.py; atributos selecionados. FKs completas e restrições estão no MER e no DDL.")
    positions = {
        "Establishment": (50,180,560,470), "User": (755,180,1265,470), "Courier":(1460,180,1970,470),
        "Customer": (50,615,560,870), "Order":(755,615,1265,940), "Route":(1460,615,1970,940),
        "OrderStatusEvent":(50,1130,560,1425), "RouteStop":(755,1130,1265,1425), "OptimizationRun":(1460,1130,1970,1425),
    }
    fields = {
        "Establishment":["id, name, document", "depot_address", "depot_latitude, depot_longitude", "created_at"],
        "User":["id, establishment_id", "full_name, email, password_hash", "role, active", "courier: Courier | None"],
        "Courier":["id, establishment_id, user_id", "load_capacity_kg, availability", "user: User"],
        "Customer":["id, establishment_id", "full_name, phone", "created_at"],
        "Order":["id, establishment_id, customer_id", "assigned_courier_id, status", "latitude, longitude, weight_kg", "priority, desired_start, desired_end", "history: list[OrderStatusEvent]"],
        "Route":["id, establishment_id, courier_id", "route_date, status, algorithm", "execution_mode, total_distance_km", "estimated_duration_min", "stops: list[RouteStop]"],
        "OrderStatusEvent":["id, order_id, changed_by", "status, note, changed_at", "order: Order", "author: User | None"],
        "RouteStop":["id, route_id, order_id", "stop_sequence, estimated_arrival", "waiting_minutes, status", "route: Route; order: Order"],
        "OptimizationRun":["id, establishment_id, run_group", "purpose, input_source", "execution_mode, worker_count", "execution_time_ms, total_distance_km", "speedup, efficiency, same_routes"],
    }
    for name, xy in positions.items(): box(draw,xy,name,fields[name],body=23)
    for start,end,label in [((560,320),(755,320),"1:N"),((1265,320),(1460,320),"1:0..1"),
        ((305,470),(305,615),"1:N"),((560,750),(755,750),"1:N"),
        ((1530,470),(1220,615),"1:N"),((1715,470),(1715,615),"1:N"),
        ((770,940),(550,1130),"1:N"),((1010,940),(1010,1130),"1:0..1"),
        ((1520,940),(1240,1130),"1:N")]: arrow(draw,start,end,label)
    image.save(OUT / "classes_v11.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture()
    classes()
    print(f"Diagramas finais em {OUT}")
