"""Gera o PDF único das Sprints 01 a 11 com os dois manuais completos.

Requer requirements-docs.txt. Preserva as páginas 2 a 169 do documento anterior,
troca a capa e acrescenta o registro, manuais, consolidação e revisão da Sprint 11.
Execute na raiz: python tools/documentation/build_sprint11_document.py
"""

import json
import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer

from build_sprint10_document import BLUE, INK, STYLES, TEAM, WIDTH, image, para, table

ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / "tmp/sprint11/pdf"
PREVIOUS = ROOT / "output/pdf/Grupo_04_RotaCerta_Sprints_01_a_10.pdf"
TARGET = ROOT / "output/pdf/Grupo_04_RotaCerta_Sprints_01_a_11.pdf"
REPO = "https://github.com/alvccpj/rota-certa"
SECTIONS = [
    ("Registro da Sprint 11", ROOT / "docs/sprint-11/README.md"),
    ("Manual do Usuário", ROOT / "docs/manuais/MANUAL_DO_USUARIO.md"),
    ("Manual Técnico", ROOT / "docs/manuais/MANUAL_TECNICO.md"),
    ("Documentação final consolidada", ROOT / "docs/final/DOCUMENTACAO_FINAL.md"),
    ("Revisão de código", ROOT / "docs/sprint-11/REVISAO_CODIGO.md"),
]
STYLES.add(ParagraphStyle("H3S11", parent=STYLES["H2RC"], fontSize=11, leading=15, spaceBefore=10))
STYLES["BodyRC"].leading = 13.6
STYLES["BodyRC"].spaceAfter = 7
STYLES["BodyRC"].allowWidows = 0
STYLES["BodyRC"].allowOrphans = 0


class ReleaseDocument(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        self.section_pages = {}
        super().__init__(*args, **kwargs)

    def afterFlowable(self, flowable):
        if getattr(flowable, "section_key", None):
            self.section_pages[flowable.section_key] = 169 + self.page


def inline(text):
    value = escape(text)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.3">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(https?://[^\s<]+)", r'<link href="\1" color="#173B67">\1</link>', value)
    return value


def text(value, style="BodyRC"):
    return Paragraph(inline(value), STYLES[style])


def markdown(path, section):
    lines = path.read_text(encoding="utf-8").splitlines()
    output, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        picture = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", line)
        if picture:
            caption, target = picture.groups()
            destination = (path.parent / target).resolve()
            assert destination.is_file(), destination
            output.append(KeepTogether([Spacer(1, 6), image(destination, max_height=355),
                                       Spacer(1, 7), text(caption, "CaptionRC")]))
        elif line.startswith("# "):
            heading = text("Parte XI - Sprint 11" if section == "Registro da Sprint 11" else line[2:], "H1RC")
            heading.section_key = section
            output.append(heading)
            if section == "Registro da Sprint 11":
                output.append(text("Preparação para entrega", "H1RC"))
        elif line.startswith("### "):
            output.append(text(line[4:], "H3S11"))
        elif line.startswith("## "):
            output.append(text(line[3:], "H2RC"))
        elif line.startswith("```"):
            language = line[3:]
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                parts = textwrap.wrap(lines[i], width=104, break_long_words=False, break_on_hyphens=False,
                                      replace_whitespace=False, drop_whitespace=True) or [""]
                for j, part in enumerate(parts):
                    # Quebra de comandos Bash mantém a continuação válida ao copiar do PDF.
                    continuation = " " + chr(92) if language == "bash" and j < len(parts)-1 else ""
                    block.append(("  " if j else "") + part + continuation)
                i += 1
            output.append(Preformatted("\n".join(block), STYLES["CodeRC"]))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", c) for c in cells):
                    rows.append(cells)
                i += 1
            count = len(rows[0])
            if count == 2:
                widths = [WIDTH * .31, WIDTH * .69]
            elif count == 4:
                widths = [WIDTH * .14, WIDTH * .25, WIDTH * .34, WIDTH * .27]
            elif rows[0][0] == "Integrante":
                widths = [135, 65, WIDTH-200]
            else:
                widths = [WIDTH * .27, WIDTH * .43, WIDTH * .30]
            assert all(len(row) == count for row in rows), (path, rows)
            output.extend(table(rows, widths, 8.2))
            continue
        elif re.match(r"^(?:\d+\. |- )", line):
            items = []
            while i < len(lines) and re.match(r"^(?:\d+\. |- )", lines[i].strip()):
                item = lines[i].strip()
                items.append(text("• " + item[2:] if item.startswith("- ") else item))
                i += 1
            output.append(KeepTogether(items))
            continue
        else:
            parts = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^(?:#|\||```|!\[|\d+\. |- )", lines[i]):
                parts.append(lines[i].strip())
                i += 1
            output.append(text(" ".join(parts)))
            continue
        i += 1
    return output


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#58606e"))
    canvas.drawCentredString(A4[0]/2, 9*mm, f"RotaCerta | Grupo 04 | Sprint 11 | Página {169 + doc.page}")
    canvas.restoreState()


def cover(pages):
    title = ParagraphStyle("Cover11", fontName="Helvetica-Bold", fontSize=25, leading=31,
                           alignment=TA_CENTER, textColor=INK, spaceAfter=9)
    center = ParagraphStyle("Center11", parent=STYLES["BodyRC"], alignment=TA_CENTER, fontSize=11, leading=15)
    result = [Spacer(1, 13*mm), Paragraph("UNINASSAU", title),
              Paragraph("Ciência da Computação | Turma 8NA | 2026.2", center), Spacer(1, 17*mm),
              Paragraph("RotaCerta", title), Paragraph("Documento técnico cumulativo", title),
              Paragraph("Sprints 01 a 11 | Grupo 04", title), Spacer(1, 7*mm)]
    result += [Paragraph(escape(member), center) for member in TEAM]
    result += [Spacer(1, 4*mm), Paragraph(REPO, center), Spacer(1, 7*mm),
               para("Consolidação em 10/11/2026. O conteúdo das Sprints 01 a 10 permanece nas páginas "
                    "2 a 169. A Sprint 11 começa na página 170, com os manuais completos, a documentação "
                    "final e a revisão de código. Onde houver diferença, prevalece a parte mais recente."),
               para("Guia de leitura da Parte XI", "H2RC")]
    result += table([["Conteúdo", "Página inicial"]] + [[name, str(number)] for name, number in pages.items()], [WIDTH-95, 95])
    result += [para("Versão 0.11.0-rc.1. Prazo: 21/11/2026 às 23h59, horário de Recife. "
                    "Envio único no Teams pelo Scrum Master Álvaro Jordão, após revisão da equipe.")]
    SimpleDocTemplate(str(TMP / "capa.pdf"), pagesize=A4, leftMargin=17*mm, rightMargin=17*mm,
                      topMargin=12*mm, bottomMargin=15*mm).build(result)
    assert len(PdfReader(TMP / "capa.pdf").pages) == 1


def main():
    evidence = ROOT / "docs/sprint-11/evidencias"
    cases = json.loads((evidence / "casos_de_teste.json").read_text())
    assert cases["reprovados"] == 0 and cases["aprovados"] == 60 and cases["nao_executados"] == 1
    for name in ("testes_backend_sqlite.txt", "testes_backend_postgresql.txt"):
        result = (evidence / name).read_text()
        assert "Ran 159 tests" in result and "\nOK (skipped=" in result and "FAILED" not in result
    assert re.search(r"\bfail 0\b", (evidence / "testes_frontend.txt").read_text())
    assert json.loads((evidence / "banco_e_contrato.json").read_text())["situacao"] == "Aprovado"
    assert json.loads((evidence / "backup_restauracao.json").read_text())["situacao"] == "Aprovado"
    assert len(PdfReader(PREVIOUS).pages) == 169
    TMP.mkdir(parents=True, exist_ok=True)
    story = []
    for name, path in SECTIONS:
        if story:
            story.append(PageBreak())
        story.extend(markdown(path, name))
    doc = ReleaseDocument(str(TMP / "parte11.pdf"), pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                          topMargin=18*mm, bottomMargin=20*mm, title="Sprint 11 Preparação para entrega RotaCerta",
                          author="Equipe RotaCerta Grupo 04")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    cover(doc.section_pages)
    writer = PdfWriter()
    writer.append(str(TMP / "capa.pdf"))
    writer.append(str(PREVIOUS), pages=(1,169))
    writer.append(str(TMP / "parte11.pdf"))
    for label, page in doc.section_pages.items():
        writer.add_outline_item(label, page-1)
    writer.add_metadata({"/Title":"Grupo 04 RotaCerta Sprints 01 a 11", "/Author":"Equipe RotaCerta Grupo 04",
                         "/Subject":"Preparação para entrega Manuais e revisão de código"})
    with TARGET.open("wb") as stream:
        writer.write(stream)
    (evidence / "paginacao.json").write_text(json.dumps({"paginas":len(writer.pages),
            "secoes":doc.section_pages}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"{TARGET.relative_to(ROOT)} | {len(writer.pages)} páginas | {doc.section_pages}")


if __name__ == "__main__":
    main()
