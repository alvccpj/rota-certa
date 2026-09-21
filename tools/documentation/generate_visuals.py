from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "sprint-02" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

NAVY = "#173B67"
BLUE = "#2563EB"
LIGHT_BLUE = "#EAF2FF"
PALE = "#F5F7FA"
GRAY = "#667085"
LIGHT_GRAY = "#D0D5DD"
DARK = "#172033"
WHITE = "#FFFFFF"
GREEN = "#17845A"
ORANGE = "#C96A16"


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size=size)


def wrapped_lines(draw, text, font_obj, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def box(draw, xy, title, items=(), fill=WHITE, outline=NAVY, title_fill=NAVY,
        title_size=28, body_size=23, radius=18):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=4)
    header_h = 58
    draw.rounded_rectangle((x1, y1, x2, y1 + header_h), radius=radius,
                           fill=title_fill, outline=title_fill)
    draw.rectangle((x1, y1 + header_h - radius, x2, y1 + header_h), fill=title_fill)
    draw.text((x1 + 18, y1 + 13), title, font=font(title_size, True), fill=WHITE)
    y = y1 + header_h + 15
    for item in items:
        lines = wrapped_lines(draw, item, font(body_size), x2 - x1 - 40)
        for i, line in enumerate(lines):
            prefix = "• " if i == 0 else "  "
            draw.text((x1 + 18, y), prefix + line, font=font(body_size), fill=DARK)
            y += body_size + 7
        y += 3


def arrow(draw, start, end, label=None, color=GRAY, width=5):
    draw.line((start, end), fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        pts = [(x2, y2), (x2 - direction * 18, y2 - 11), (x2 - direction * 18, y2 + 11)]
    else:
        direction = 1 if y2 > y1 else -1
        pts = [(x2, y2), (x2 - 11, y2 - direction * 18), (x2 + 11, y2 - direction * 18)]
    draw.polygon(pts, fill=color)
    if label:
        lx = (x1 + x2) // 2
        ly = (y1 + y2) // 2 - 28
        bbox = draw.textbbox((0, 0), label, font=font(19, True))
        w = bbox[2] - bbox[0]
        draw.rounded_rectangle((lx - w // 2 - 9, ly - 4, lx + w // 2 + 9, ly + 24),
                               radius=8, fill=WHITE)
        draw.text((lx - w // 2, ly), label, font=font(19, True), fill=color)


def title(draw, text, subtitle=None, width=1800):
    draw.text((60, 45), text, font=font(38, True), fill=DARK)
    if subtitle:
        draw.text((60, 94), subtitle, font=font(22), fill=GRAY)
    draw.line((60, 132, width - 60, 132), fill=LIGHT_GRAY, width=3)


def architecture():
    img = Image.new("RGB", (1800, 1000), WHITE)
    d = ImageDraw.Draw(img)
    title(d, "Arquitetura do RotaCerta", "Comunicação síncrona por API REST e processamento isolado de otimização")

    box(d, (55, 205, 295, 430), "Usuários", ["Administrador", "Atendente", "Entregador"], fill=PALE)
    box(d, (360, 170, 670, 470), "Frontend", ["React + TypeScript", "Vite", "Interface responsiva", "Leaflet + OpenStreetMap"], fill=LIGHT_BLUE)
    box(d, (755, 155, 1085, 485), "API", ["FastAPI", "Autenticação JWT", "Controle por perfil", "OpenAPI", "Validação de dados"], fill="#EEF8F4", title_fill=GREEN)
    box(d, (1170, 145, 1515, 495), "Aplicação", ["Serviços de domínio", "Pedidos e entregadores", "Geração de rotas", "Relatórios e métricas"], fill="#FFF7ED", title_fill=ORANGE)
    box(d, (1240, 650, 1605, 890), "PostgreSQL", ["Dados operacionais", "Rotas e paradas", "Execuções de otimização", "Índices e integridade"], fill=PALE)
    box(d, (720, 650, 1100, 900), "Motor de otimização", ["Vizinho mais próximo", "Refinamento 2-opt", "Modo sequencial", "Modo paralelo", "Coleta de métricas"], fill="#F4F0FF", title_fill="#6941C6")
    box(d, (185, 650, 570, 870), "Serviço cartográfico", ["Adaptador OSRM", "Matriz de distâncias", "Geocodificação", "Sem acoplamento ao provedor"], fill=PALE)

    arrow(d, (295, 315), (360, 315), "HTTPS")
    arrow(d, (670, 315), (755, 315), "JSON")
    arrow(d, (1085, 315), (1170, 315), "serviços")
    arrow(d, (1360, 495), (1430, 650), "SQL")
    arrow(d, (1235, 495), (1030, 650), "tarefas")
    arrow(d, (720, 770), (570, 770), "distâncias")
    arrow(d, (1100, 785), (1240, 785), "métricas")

    img.save(ASSETS / "arquitetura.png", quality=95)


def class_diagram():
    img = Image.new("RGB", (1900, 1350), WHITE)
    d = ImageDraw.Draw(img)
    title(d, "Diagrama de classes", "Classes de domínio e serviço previstas para as próximas Sprints", 1900)

    classes = {
        "Estabelecimento": ((70, 175, 500, 500), ["id: int", "nome: string", "enderecoBase: string", "latitudeBase: decimal", "longitudeBase: decimal", "adicionarUsuario()", "listarPedidosPendentes()"]),
        "Usuario": ((735, 165, 1165, 510), ["id: int", "nome: string", "email: string", "senhaHash: string", "perfil: Perfil", "ativo: bool", "autenticar()", "temPermissao()"]),
        "Entregador": ((1385, 175, 1815, 500), ["id: int", "capacidadeKg: decimal", "disponibilidade: Status", "aceitarRota()", "atualizarStatusParada()"]),
        "Cliente": ((70, 585, 500, 900), ["id: int", "nome: string", "telefone: string", "cadastrarEndereco()", "consultarHistorico()"]),
        "Pedido": ((735, 555, 1165, 950), ["id: int", "enderecoEntrega: string", "latitude: decimal", "longitude: decimal", "pesoKg: decimal", "prioridade: int", "status: StatusPedido", "atribuirEntregador()", "alterarStatus()"]),
        "Rota": ((1385, 570, 1815, 950), ["id: int", "data: date", "algoritmo: string", "modo: ModoExecucao", "distanciaTotalKm: decimal", "status: StatusRota", "adicionarParada()", "calcularTotais()"]),
        "ExecucaoOtimizacao": ((85, 1040, 575, 1325), ["modo: ModoExecucao", "workers: int", "tempoMs: decimal", "distanciaTotalKm: decimal", "pedidos: int", "entregadores: int"]),
        "OtimizadorRotas": ((725, 1035, 1175, 1325), ["gerarSequencial()", "gerarParalelo()", "vizinhoMaisProximo()", "aplicar2Opt()", "registrarMetricas()"]),
        "ParadaRota": ((1335, 1040, 1825, 1325), ["sequencia: int", "previsaoChegada: datetime", "distanciaAnteriorKm: decimal", "status: StatusParada"]),
    }
    for name, (xy, items) in classes.items():
        box(d, xy, name, items, body_size=19, title_size=24, fill=PALE)

    arrow(d, (500, 310), (735, 310), "1 para N")
    arrow(d, (1165, 315), (1385, 315), "1 para 0..1")
    arrow(d, (500, 735), (735, 735), "1 para N")
    arrow(d, (1165, 735), (1385, 735), "N para 0..1")
    arrow(d, (1600, 950), (1600, 1040), "1 contém N")
    arrow(d, (950, 950), (950, 1035), "entrada")
    arrow(d, (725, 1175), (575, 1175), "registra")
    arrow(d, (1175, 1085), (1385, 900), "gera")

    img.save(ASSETS / "diagrama_classes.png", quality=95)


def er_diagram():
    img = Image.new("RGB", (1900, 1500), WHITE)
    d = ImageDraw.Draw(img)
    title(d, "Modelo Entidade Relacionamento", "Entidades, chaves e cardinalidades da estrutura inicial", 1900)

    entities = {
        "ESTABELECIMENTO": ((60, 170, 470, 455), ["PK id", "nome", "documento", "endereco_base", "latitude_base", "longitude_base"]),
        "USUARIO": ((745, 155, 1155, 475), ["PK id", "FK estabelecimento_id", "nome", "email", "senha_hash", "perfil", "ativo"]),
        "ENTREGADOR": ((1430, 170, 1840, 470), ["PK id", "FK estabelecimento_id", "FK usuario_id", "capacidade_kg", "disponibilidade"]),
        "CLIENTE": ((60, 610, 470, 880), ["PK id", "FK estabelecimento_id", "nome", "telefone"]),
        "PEDIDO": ((745, 545, 1155, 980), ["PK id", "FK estabelecimento_id", "FK cliente_id", "FK entregador_id", "endereco", "latitude / longitude", "peso_kg", "prioridade", "janela_horario", "status"]),
        "ROTA": ((1430, 555, 1840, 970), ["PK id", "FK estabelecimento_id", "FK entregador_id", "data", "status", "algoritmo", "modo_execucao", "distancia_total", "duracao_estimada"]),
        "PARADA_ROTA": ((140, 1130, 650, 1450), ["PK id", "FK rota_id", "FK pedido_id", "sequencia", "previsao_chegada", "distancia_anterior", "status"]),
        "EXECUCAO_OTIMIZACAO": ((1130, 1105, 1760, 1460), ["PK id", "FK estabelecimento_id", "algoritmo", "modo_execucao", "workers", "pedidos", "entregadores", "tempo_ms", "distancia_total"]),
    }
    for name, (xy, items) in entities.items():
        box(d, xy, name, items, body_size=19, title_size=22, fill=PALE)

    arrow(d, (470, 290), (745, 290), "1:N")
    arrow(d, (1155, 290), (1430, 290), "1:0..1")
    arrow(d, (470, 730), (745, 730), "1:N")
    arrow(d, (1155, 700), (1430, 700), "N:0..1")
    arrow(d, (1630, 970), (650, 1250), "1:N")
    arrow(d, (940, 980), (650, 1130), "1:0..1")

    img.save(ASSETS / "modelo_entidade_relacionamento.png", quality=95)


def frame(draw, xy, screen_title):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=24, fill=WHITE, outline=LIGHT_GRAY, width=4)
    draw.rectangle((x1, y1, x2, y1 + 70), fill=NAVY)
    draw.text((x1 + 25, y1 + 20), "RotaCerta", font=font(25, True), fill=WHITE)
    draw.text((x1 + 25, y1 + 90), screen_title, font=font(28, True), fill=DARK)
    return x1, y1, x2, y2


def field(draw, x, y, w, label, value=""):
    draw.text((x, y), label, font=font(18, True), fill=DARK)
    draw.rounded_rectangle((x, y + 28, x + w, y + 78), radius=8, fill=PALE, outline=LIGHT_GRAY, width=2)
    if value:
        draw.text((x + 12, y + 43), value, font=font(18), fill=GRAY)


def button(draw, x, y, w, label, fill=BLUE):
    draw.rounded_rectangle((x, y, x + w, y + 55), radius=10, fill=fill)
    bbox = draw.textbbox((0, 0), label, font=font(19, True))
    tx = x + (w - (bbox[2] - bbox[0])) / 2
    draw.text((tx, y + 16), label, font=font(19, True), fill=WHITE)


def prototypes_admin():
    img = Image.new("RGB", (2000, 1180), "#EEF2F6")
    d = ImageDraw.Draw(img)
    title(d, "Protótipos principais", "Fluxo administrativo em baixa fidelidade", 2000)

    x1, y1, x2, y2 = frame(d, (40, 160, 620, 1110), "Acesso")
    d.text((x1 + 70, y1 + 210), "Entrar no sistema", font=font(30, True), fill=DARK)
    field(d, x1 + 70, y1 + 300, 440, "E-mail", "usuario@empresa.com")
    field(d, x1 + 70, y1 + 410, 440, "Senha", "••••••••")
    button(d, x1 + 70, y1 + 540, 440, "Entrar")
    d.text((x1 + 70, y1 + 625), "Perfis: administrador, atendente e entregador", font=font(17), fill=GRAY)

    x1, y1, x2, y2 = frame(d, (710, 160, 1290, 1110), "Painel do dia")
    for i, (label, value) in enumerate([("Pedidos", "38"), ("Em rota", "16"), ("Entregues", "19")]):
        x = x1 + 25 + i * 178
        d.rounded_rectangle((x, y1 + 160, x + 160, y1 + 270), radius=12, fill=LIGHT_BLUE)
        d.text((x + 15, y1 + 180), label, font=font(18, True), fill=NAVY)
        d.text((x + 15, y1 + 215), value, font=font(34, True), fill=DARK)
    d.text((x1 + 25, y1 + 320), "Operação", font=font(23, True), fill=DARK)
    for i, row in enumerate(["#1038  Ana Souza  Pendente", "#1037  João Lima  Em rota", "#1036  Carla Melo  Entregue"]):
        y = y1 + 370 + i * 70
        d.rounded_rectangle((x1 + 25, y, x2 - 25, y + 55), radius=8, fill=PALE, outline=LIGHT_GRAY)
        d.text((x1 + 40, y + 17), row, font=font(18), fill=DARK)
    button(d, x1 + 25, y1 + 640, 250, "Novo pedido")
    button(d, x1 + 295, y1 + 640, 250, "Gerar rotas", fill=GREEN)

    x1, y1, x2, y2 = frame(d, (1380, 160, 1960, 1110), "Novo pedido")
    field(d, x1 + 30, y1 + 145, 520, "Cliente", "Nome do cliente")
    field(d, x1 + 30, y1 + 250, 520, "Endereço", "Rua, número e bairro")
    field(d, x1 + 30, y1 + 355, 245, "Peso em kg", "2,50")
    field(d, x1 + 305, y1 + 355, 245, "Prioridade", "Normal")
    field(d, x1 + 30, y1 + 460, 520, "Horário desejado", "14:00 às 16:00")
    button(d, x1 + 30, y1 + 590, 250, "Cancelar", fill=GRAY)
    button(d, x1 + 300, y1 + 590, 250, "Salvar pedido")

    img.save(ASSETS / "prototipos_administracao.png", quality=95)


def prototypes_routes():
    img = Image.new("RGB", (2000, 1180), "#EEF2F6")
    d = ImageDraw.Draw(img)
    title(d, "Protótipos principais", "Geração de rotas e operação móvel do entregador", 2000)

    x1, y1, x2, y2 = frame(d, (40, 160, 1050, 1110), "Planejamento de rotas")
    d.rounded_rectangle((x1 + 25, y1 + 145, x1 + 650, y1 + 665), radius=12, fill="#E7EEF5", outline=LIGHT_GRAY)
    for px, py, n in [(180, 260, 1), (350, 360, 2), (560, 250, 3), (730, 470, 4), (900, 330, 5)]:
        cx, cy = x1 + px, y1 + py
        d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=BLUE)
        d.text((cx - 6, cy - 12), str(n), font=font(18, True), fill=WHITE)
    for a, b in [((180, 260), (350, 360)), ((350, 360), (560, 250)), ((560, 250), (730, 470)), ((730, 470), (900, 330))]:
        d.line((x1 + a[0], y1 + a[1], x1 + b[0], y1 + b[1]), fill=BLUE, width=5)
    d.text((x1 + 700, y1 + 160), "Resumo", font=font(23, True), fill=DARK)
    for i, t in enumerate(["4 entregadores", "38 pedidos", "62,4 km", "1 h 48 min estimados"]):
        d.text((x1 + 700, y1 + 220 + i * 55), t, font=font(20), fill=DARK)
    button(d, x1 + 700, y1 + 500, 260, "Otimizar rotas", fill=GREEN)
    d.text((x1 + 25, y1 + 720), "Entregador 1", font=font(22, True), fill=DARK)
    for i, t in enumerate(["1. Farmácia Central", "2. Rua das Flores, 82", "3. Av. Norte, 410"]):
        d.text((x1 + 45, y1 + 770 + i * 48), t, font=font(19), fill=DARK)

    x1, y1, x2, y2 = frame(d, (1160, 160, 1550, 1110), "Minha rota")
    d.text((x1 + 25, y1 + 150), "3 de 7 entregas", font=font(22, True), fill=DARK)
    d.rounded_rectangle((x1 + 25, y1 + 210, x2 - 25, y1 + 500), radius=12, fill="#E7EEF5")
    d.line((x1 + 95, y1 + 430, x1 + 285, y1 + 270), fill=BLUE, width=6)
    for cx, cy in [(x1 + 95, y1 + 430), (x1 + 190, y1 + 350), (x1 + 285, y1 + 270)]:
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=BLUE)
    d.text((x1 + 25, y1 + 540), "Próxima parada", font=font(19, True), fill=GRAY)
    d.text((x1 + 25, y1 + 580), "Rua das Flores, 82", font=font(23, True), fill=DARK)
    d.text((x1 + 25, y1 + 625), "Previsão 14:35", font=font(19), fill=GRAY)
    button(d, x1 + 25, y1 + 710, 340, "Iniciar navegação")

    x1, y1, x2, y2 = frame(d, (1600, 160, 1960, 1110), "Atualizar entrega")
    d.text((x1 + 25, y1 + 150), "Pedido #1037", font=font(25, True), fill=DARK)
    d.text((x1 + 25, y1 + 200), "João Lima", font=font(20), fill=GRAY)
    d.text((x1 + 25, y1 + 245), "Rua das Flores, 82", font=font(19), fill=DARK)
    for i, t in enumerate(["Em rota", "Entregue", "Não entregue"]):
        y = y1 + 330 + i * 80
        d.rounded_rectangle((x1 + 25, y, x2 - 25, y + 58), radius=8, fill=PALE, outline=LIGHT_GRAY)
        d.ellipse((x1 + 45, y + 18, x1 + 67, y + 40), outline=BLUE, width=3)
        d.text((x1 + 85, y + 17), t, font=font(19), fill=DARK)
    field(d, x1 + 25, y1 + 585, 310, "Observação", "Opcional")
    button(d, x1 + 25, y1 + 710, 310, "Confirmar status", fill=GREEN)

    img.save(ASSETS / "prototipos_rotas.png", quality=95)


if __name__ == "__main__":
    architecture()
    class_diagram()
    er_diagram()
    prototypes_admin()
    prototypes_routes()
    print(f"Visuals generated in {ASSETS}")
