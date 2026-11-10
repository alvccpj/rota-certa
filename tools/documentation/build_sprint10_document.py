"""Consolida Sprints 01 a 10 preservando as páginas históricas 2 a 150.

Dependências: reportlab, pypdf, Pillow. Na raiz:
    python tools/documentation/build_sprint10_document.py

A Parte X segue a tipografia, as cores e as tabelas do PDF anterior.
O relatório é construído com os registros reais da Sprint 10 e seu README.
"""

import json
import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/sprint-10"
TMP = ROOT / "tmp/sprint10/pdf"
PREVIOUS = ROOT / "output/pdf/Grupo_04_RotaCerta_Sprints_01_a_09.pdf"
TARGET = ROOT / "output/pdf/Grupo_04_RotaCerta_Sprints_01_a_10.pdf"
REPO = "https://github.com/alvccpj/rota-certa"
TEAM = ["Álvaro Jordão - 01748200", "Arthur Sales - 01593811", "Vinícius Trigueiro - 01794959",
        "William Coelho de Morais - 01263977", "Guilherme de Luna Barros - 01615925"]
BLUE, INK = colors.HexColor("#173B67"), colors.HexColor("#1d2433")
WIDTH = A4[0] - 34 * mm
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("BodyRC", fontName="Helvetica", fontSize=10, leading=14.3,
                          textColor=INK, spaceAfter=8))
STYLES.add(ParagraphStyle("H1RC", parent=STYLES["BodyRC"], fontName="Helvetica-Bold", fontSize=19,
                          leading=23, textColor=BLUE, spaceAfter=13, keepWithNext=True))
STYLES.add(ParagraphStyle("H2RC", parent=STYLES["BodyRC"], fontName="Helvetica-Bold", fontSize=13.2,
                          leading=17, textColor=BLUE, spaceBefore=13, spaceAfter=8, keepWithNext=True))
STYLES.add(ParagraphStyle("CellRC", parent=STYLES["BodyRC"], fontSize=8.4, leading=11.1, spaceAfter=0))
STYLES.add(ParagraphStyle("CaptionRC", parent=STYLES["BodyRC"], fontSize=9.2, leading=13,
                          textColor=colors.HexColor("#475467"), spaceAfter=10))
STYLES.add(ParagraphStyle("CodeRC", fontName="Courier", fontSize=7.4, leading=10.2,
                          backColor=colors.HexColor("#f2f4f7"), borderPadding=8, spaceBefore=4, spaceAfter=12))


def inline(value):
    value = escape(str(value))
    value = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.3">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(https://[^\s<]+)", r'<link href="\1" color="#173B67">\1</link>', value)
    return value


def para(value, style="BodyRC"):
    return Paragraph(inline(value), STYLES[style])


def table(rows, widths=None, size=8.4):
    style = ParagraphStyle("CellLocal", parent=STYLES["CellRC"], fontSize=size, leading=size * 1.32)
    content = [[Paragraph(("<b>" if row == 0 else "") + inline(cell) + ("</b>" if row == 0 else ""), style)
                for cell in record] for row, record in enumerate(rows)]
    result = Table(content, colWidths=widths or [WIDTH / len(rows[0])] * len(rows[0]), repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce7f2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#d0d5dd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [result, Spacer(1, 8)]


def markdown(source):
    lines = source.splitlines()
    flow, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.extend(textwrap.wrap(lines[i], width=105, replace_whitespace=False,
                                          drop_whitespace=False) or [""])
                i += 1
            flow.append(Preformatted("\n".join(code), STYLES["CodeRC"]))
        elif line.startswith("# "):
            flow.append(para("Parte X - Sprint 10", "H1RC"))
            flow.append(para("Versão Release Candidate", "H1RC"))
        elif line.startswith("## "):
            flow.append(para(line[3:], "H2RC"))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            # Colunas numéricas compactas; textos e caminhos recebem mais espaço.
            if rows[0][0] == "Tabela":
                widths = [100, 52, WIDTH - 152]
            elif rows[0][0] == "Integrante":
                widths = [135, 65, WIDTH - 200]
            elif rows[0][0] == "Rodada":
                widths = [46, 70, 68, 85, 105, WIDTH - 374]
            elif len(rows[0]) == 2:
                widths = [70, WIDTH - 70]
            else:
                widths = [WIDTH * .25, WIDTH * .43, WIDTH * .32] if len(rows[0]) == 3 else None
            flow.extend(table(rows, widths))
            continue
        elif line.startswith("- "):
            flow.append(para("• " + line[2:]))
        else:
            parts = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "- ")):
                parts.append(lines[i].strip())
                i += 1
            flow.append(para(" ".join(parts)))
            continue
        i += 1
    return flow


def image(path, max_height=420, max_width=WIDTH):
    with PILImage.open(path) as source:
        w, h = source.size
    scale = min(max_width / w, max_height / h)
    return Image(str(path), width=w * scale, height=h * scale)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#58606e"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0] / 2, 9 * mm, f"RotaCerta | Grupo 04 | Sprint 10 | Página {150 + doc.page}")
    canvas.restoreState()


def evidence_pages(summary):
    items = []
    cases = {case["id"]: case for case in summary["casos"]}
    for cid, heading in (("F01", "Acesso e painel operacional"), ("F07", "Cadastro de pedido integrado ao banco"),
                         ("F14", "Resultado da atribuição automática"), ("F20", "Relatório e exportação")):
        case = cases[cid]
        items += [PageBreak(), para(heading, "H1RC"), para(f"Evidência {cid} - {case['titulo']}.")]
        items.append(image(SOURCE / case["evidencia"], max_height=420))
        items += [Spacer(1, 12), para("Procedimento: " + "; ".join(case["procedimento"]) + ".", "CaptionRC"),
                  para("Resultado observado: " + case["obtido"], "CaptionRC"),
                  para("Captura realizada no sistema executado com PostgreSQL em 10/11/2026. "
                       "O resultado completo e as verificações da API estão no registro dos casos.", "CaptionRC")]
    items += [PageBreak(), para("Rotas integradas ao mapa e às paradas", "H1RC"),
              para("Consulta da candidata após o roteiro funcional, com trajetos e paradas persistidos."),
              image(SOURCE / "assets/rc_rotas_mapa.png", max_height=440), Spacer(1, 10),
              para("Os trajetos ligam as coordenadas e mostram a sequência de atendimento. "
                   "São distâncias geográficas; não representam navegação por ruas ou trânsito em tempo real.", "CaptionRC"),
              para("Resultado de F15: " + cases["F15"]["obtido"], "CaptionRC")]
    items += [PageBreak(), para("Entrega e navegação no celular", "H1RC"),
              para("À esquerda, confirmação de entrega pelo responsável. À direita, tabela de clientes "
                   "rolada internamente até as ações, após a correção do BUG-10.")]
    panels = Table([[image(SOURCE / cases["F17"]["evidencia"], 415, 200),
                     image(SOURCE / "assets/rc_clientes_celular.png", 415, 200)]], colWidths=[WIDTH / 2] * 2)
    panels.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    items += [panels, Spacer(1, 12), para("F17: " + cases["F17"]["obtido"], "CaptionRC"),
              para("A regressão adicional mediu documento e viewport iguais em 320, 390 e 768 px; "
                   "a tabela de 981 px permaneceu dentro do contêiner, com botões acessíveis por rolagem.", "CaptionRC")]
    items += [PageBreak(), para("Documentação interativa da API", "H1RC"),
              para("Swagger carregado a partir da aplicação candidata, versão 0.10.0-rc.1."),
              image(SOURCE / "assets/rc_swagger.png", max_height=420), Spacer(1, 12),
              para("O guia no repositório inclui autenticação Bearer, exemplos, perfis e erros. "
                   "O catálogo e o contrato versionado documentam as 37 operações, seus parâmetros "
                   "e modelos. A inspeção automática confirmou igualdade entre o JSON exportado e o servido.", "CaptionRC")]
    return items


def main():
    summary = json.loads((SOURCE / "evidencias/casos_de_teste.json").read_text(encoding="utf-8"))
    database = json.loads((SOURCE / "evidencias/banco_e_contrato.json").read_text(encoding="utf-8"))
    assert summary["reprovados"] == 0 and summary["aprovados"] == 60 and summary["nao_executados"] == 1
    assert database["situacao"] == "Aprovado"
    for name in ("testes_backend_sqlite.txt", "testes_backend_postgresql.txt"):
        result = (SOURCE / "evidencias" / name).read_text(encoding="utf-8")
        assert "Ran 152 tests" in result and "\nOK (skipped=" in result and "FAILED" not in result
    assert len(PdfReader(PREVIOUS).pages) == 150
    TMP.mkdir(parents=True, exist_ok=True)
    story = markdown((SOURCE / "README.md").read_text(encoding="utf-8"))
    story += [PageBreak(), para("Catálogo resumido das APIs", "H1RC"),
              para("A = ADMIN; T = ATTENDANT; E = COURIER. Autenticado: qualquer perfil, respeitando "
                   "propriedade e estabelecimento. As entradas são modelos JSON; IDs e filtros são "
                   "detalhados no catálogo completo. As saídas indicam o modelo da resposta de sucesso.")]
    contract = json.loads((ROOT / "docs/api/openapi.json").read_text(encoding="utf-8"))
    catalog = json.loads((SOURCE / "evidencias/catalogo_api.json").read_text(encoding="utf-8"))
    rows = [["Método", "Rota", "Acesso", "Entrada", "Resposta"]]
    for endpoint in catalog:
        operation = contract["paths"][endpoint["rota"]][endpoint["metodo"].lower()]
        code = next(c for c in operation["responses"] if c.startswith("2"))
        schema = operation["responses"][code].get("content", {}).get("application/json", {}).get("schema", {})
        if schema.get("type") == "array":
            output = "Lista " + schema.get("items", {}).get("$ref", "objeto").split("/")[-1]
        else:
            output = schema.get("$ref", "Sem corpo" if code == "204" else "Objeto").split("/")[-1]
        access = endpoint["acesso"].replace("ATTENDANT", "T").replace("COURIER", "E").replace("ADMIN", "A").replace("Usuário autenticado", "Autenticado")
        rows.append([endpoint["metodo"], endpoint["rota"], access, endpoint["entrada"] or "-", code + " " + output])
    story += table(rows, [42, 151, 65, 101, WIDTH - 359], 7.7)
    story += [PageBreak(), para("Modelo de dados vigente na candidata", "H1RC"),
              para("O diagrama atualizado na Sprint 09 permanece coerente com o DDL final inspecionado "
                   "na Sprint 10. Não houve alteração de tabelas ou colunas nesta candidata."),
              image(ROOT / "docs/sprint-09/assets/mer_v09.png", max_height=490), Spacer(1, 10),
              para("Fonte técnica: database/schema.sql e modelos de backend/app/models.py. Inspeção atual: "
                   "docs/sprint-10/evidencias/banco_e_contrato.json, com nove tabelas, 14 referências "
                   "sem órfãos e nenhuma inconsistência nas quatro consultas de isolamento.", "CaptionRC")]
    story += evidence_pages(summary)
    doc = SimpleDocTemplate(str(TMP / "parte10.pdf"), pagesize=A4, rightMargin=17 * mm,
                            leftMargin=17 * mm, topMargin=18 * mm, bottomMargin=20 * mm,
                            title="Sprint 10 Release Candidate RotaCerta", author="Equipe RotaCerta Grupo 04")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

    # Capa mantém o padrão e informa a paginação preservada.
    cover_style = ParagraphStyle("Cover", fontName="Helvetica-Bold", fontSize=26, leading=32,
                                 textColor=INK, alignment=TA_CENTER, spaceAfter=10)
    center = ParagraphStyle("Center", parent=STYLES["BodyRC"], alignment=TA_CENTER, fontSize=11, leading=16)
    cover = [Spacer(1, 25 * mm), Paragraph("UNINASSAU", cover_style),
             Paragraph("Ciência da Computação | Turma 8NA | 2026.2", center), Spacer(1, 27 * mm),
             Paragraph("RotaCerta", cover_style), Paragraph("Documento técnico cumulativo", cover_style),
             Paragraph("Sprints 01 a 10 | Grupo 04", cover_style), Spacer(1, 12 * mm)]
    cover += [Paragraph(escape(person), center) for person in TEAM]
    cover += [Spacer(1, 5 * mm), Paragraph(REPO, center), Spacer(1, 12 * mm),
              para("Consolidação em 10/11/2026. As Sprints 01 a 07 estão preservadas nas páginas "
                   "2 a 100, a Sprint 08 nas páginas 101 a 112 e a Sprint 09 nas páginas 113 a 150. "
                   "A Sprint 10 começa na página 151 e apresenta a versão Release Candidate 0.10.0-rc.1. "
                   "As partes anteriores mantêm seus registros históricos; onde houver diferença, prevalece a mais recente."),
              para("Prazo de entrega: 14/11/2026 às 23h59, horário de Recife. Envio único no Teams "
                   "pelo Scrum Master Álvaro Jordão, após revisão da equipe.")]
    SimpleDocTemplate(str(TMP / "capa.pdf"), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=12 * mm, bottomMargin=15 * mm).build(cover)
    assert len(PdfReader(TMP / "capa.pdf").pages) == 1
    writer = PdfWriter()
    writer.append(str(TMP / "capa.pdf"))
    writer.append(str(PREVIOUS), pages=(1, 150))
    writer.append(str(TMP / "parte10.pdf"))
    writer.add_outline_item("Sprint 10 Versão Release Candidate", 150)
    writer.add_metadata({"/Title": "Grupo 04 RotaCerta Sprints 01 a 10",
                         "/Author": "Equipe RotaCerta Grupo 04", "/Subject": "Versão Release Candidate 0.10.0-rc.1"})
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with TARGET.open("wb") as stream:
        writer.write(stream)
    print(f"{TARGET.relative_to(ROOT)} | {len(writer.pages)} páginas | Sprint 10 a partir da página 151")


if __name__ == "__main__":
    main()
