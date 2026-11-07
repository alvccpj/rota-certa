"""Gera o PDF único das Sprints 01 a 09.

Mantém as páginas 2 a 112 do PDF 01 a 08 sem alteração, troca a capa e acrescenta
a Parte IX, montada a partir de docs/sprint-09/README.md e dos resultados em
docs/sprint-09/evidencias/casos_de_teste.json. O HTML é impresso pelo Chrome
(Playwright), como nas Sprints 01 a 07.

    backend\\.venv\\Scripts\\python.exe tools/documentation/build_sprint09_document.py
"""

import json
import re
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "sprint-09"
PREVIOUS = ROOT / "output" / "pdf" / "Grupo_04_RotaCerta_Sprints_01_a_08.pdf"
TARGET = ROOT / "output" / "pdf" / "Grupo_04_RotaCerta_Sprints_01_a_09.pdf"
TMP = ROOT / "tmp" / "sprint09"
TEAM = ["Álvaro Jordão - 01748200", "Arthur Sales - 01593811", "Vinícius Trigueiro - 01794959",
        "William Coelho de Morais - 01263977", "Guilherme de Luna Barros - 01615925"]

CSS = """
@page { size: A4; margin: 18mm 17mm 22mm 17mm; }
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; font-size: 10.2pt; line-height: 1.45; color: #1d2433; }
h1 { font-size: 20pt; color: #173B67; margin: 0 0 6px; }
h2 { font-size: 14pt; color: #173B67; margin: 20px 0 8px; padding-bottom: 4px; border-bottom: 2px solid #dce7f2;
     break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 6px; break-after: avoid; }
p { margin: 0 0 8px; }
ul { margin: 0 0 8px 18px; padding: 0; }
li { margin-bottom: 4px; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f2f4f7; padding: 0 3px; border-radius: 3px; }
pre { background: #f2f4f7; padding: 8px 10px; border-radius: 6px; font-size: 8.6pt; white-space: pre-wrap; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 12px; font-size: 8.4pt; line-height: 1.35; }
th { background: #dce7f2; text-align: left; }
th, td { border: 1px solid #d0d5dd; padding: 4px 6px; vertical-align: top; overflow-wrap: break-word; }
td code { word-break: break-all; }
tr { break-inside: avoid; }
.cases td:first-child, .cases td:last-child { white-space: nowrap; font-weight: bold; }
.ok { color: #17845A; font-weight: bold; }
.fail { color: #B42318; font-weight: bold; }
.ident { border: 1px solid #d0d5dd; border-radius: 8px; padding: 10px 14px; margin: 10px 0 14px; background: #f5f7fa; }
figure { margin: 0 0 14px; break-inside: avoid; }
figure img { width: 100%; border: 1px solid #d0d5dd; border-radius: 4px; }
figure.half img { width: 62%; display: block; margin: 0 auto; }
figcaption { font-size: 8.8pt; color: #475467; margin-top: 4px; }
figcaption strong { color: #1d2433; }
.part { break-before: page; }
"""


def inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(https://\S+)", r'<a href="\1">\1</a>', text)


def markdown(lines: list[str]) -> str:
    """Conversor mínimo para o README: títulos, parágrafos, listas, tabelas e código."""

    out, i = [], 0
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            block = []
            i += 1
            while not lines[i].startswith("```"):
                block.append(escape(lines[i].rstrip()))
                i += 1
            out.append("<pre>" + "\n".join(block) + "</pre>")
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", c) for c in cells):
                    rows.append(cells)
                i += 1
            head = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>" for row in rows[1:])
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:].strip())}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line:
            out.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(out)


def sections() -> dict[str, list[str]]:
    lines = (SOURCE / "README.md").read_text(encoding="utf-8").splitlines()
    result, current = {"_intro": []}, "_intro"
    for line in lines[1:]:
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        result[current].append(line)
    return result


def case_table(cases: list[dict], kind: str) -> str:
    rows = []
    for case in (c for c in cases if c["tipo"] == kind):
        steps = "<br>".join(f"{n}. {inline(step)}" for n, step in enumerate(case["procedimento"], 1))
        status = "ok" if case["situacao"] == "Aprovado" else "fail"
        rows.append(f"<tr><td>{case['id']}</td><td><strong>{inline(case['titulo'])}</strong><br>{inline(case['modulo'])}</td>"
                    f"<td>{steps}</td><td>{inline(case['esperado'])}</td><td>{inline(case['obtido'])}</td>"
                    f"<td class='{status}'>{case['situacao']}</td></tr>")
    return ("<table class='cases'><colgroup><col style='width:5%'><col style='width:15%'><col style='width:23%'>"
            "<col style='width:19%'><col style='width:27%'><col style='width:11%'></colgroup><thead><tr><th>ID</th><th>Caso</th>"
            "<th>Procedimento</th><th>Resultado esperado</th><th>Resultado obtido</th><th>Situação</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def figures(cases: list[dict]) -> str:
    out = []
    for case in cases:
        if not case.get("evidencia"):
            continue
        image = (SOURCE / case["evidencia"]).as_uri()
        mobile = case["id"] in ("F17", "N13")
        out.append(f"<figure class='{'half' if mobile else ''}'><img src='{image}'><figcaption><strong>{case['id']} - "
                   f"{inline(case['titulo'])}.</strong> Procedimento: {inline('; '.join(case['procedimento']))}. "
                   f"Obtido: {inline(case['obtido'])}</figcaption></figure>")
    return "\n".join(out)


def build_html(summary: dict) -> str:
    parts = sections()
    cases = summary["casos"]
    team = "<br>".join(TEAM)
    html = [f"<h1>Parte IX - Sprint 09: Testes, correções e documentação</h1>",
            f"<div class='ident'><strong>Grupo 04 - RotaCerta</strong> | UNINASSAU, Ciência da Computação, turma 8NA, 2026.2<br>"
            f"{team}<br>Repositório: <a href='https://github.com/alvccpj/rota-certa'>https://github.com/alvccpj/rota-certa</a> "
            f"| branch <code>sprint/09-testes-validacao</code></div>",
            ]  # a identificação acima substitui as linhas iniciais do README
    for title, body in parts.items():
        if title == "_intro":
            continue
        html.append(markdown(body))
        kind = {"Testes funcionais": "Funcional", "Testes de validação": "Validação", "Testes de navegação": "Navegação"}.get(title)
        if kind:
            approved = sum(1 for c in cases if c["tipo"] == kind and c["situacao"] == "Aprovado")
            total = sum(1 for c in cases if c["tipo"] == kind)
            html.append(f"<p><strong>Casos de teste ({approved} de {total} aprovados na execução de "
                        f"{summary['executado_em'][:16].replace('T', ' ')}):</strong></p>" + case_table(cases, kind))
        if title == "Atualização da documentação":
            for image, caption in (("arquitetura_v09.png", "Arquitetura atualizada na Sprint 09."),
                                   ("mer_v09.png", "Modelo de dados atualizado na Sprint 09, conforme database/schema.sql.")):
                html.append(f"<figure><img src='{(SOURCE / 'assets' / image).as_uri()}'><figcaption><strong>{caption}</strong>"
                            "</figcaption></figure>")
    html.append("<h2 class='part'>Evidências da execução dos testes</h2><p>Capturas de tela salvas pelo roteiro durante a "
                "execução oficial, na aplicação real ligada ao PostgreSQL. Cada legenda informa o caso, o procedimento e o "
                "resultado obtido. As capturas de computador usam 1366 px de largura e as de celular, 390 px.</p>")
    html.append(figures(cases))
    return f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(html)}</body></html>"


def cover_html(first_page: int) -> str:
    team = "".join(f"<p>{name}</p>" for name in TEAM)
    return f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>
    @page {{ size: A4; margin: 0; }} body {{ font-family: Arial, sans-serif; text-align: center; color: #1d2433; margin: 0; padding: 70px 60px; }}
    .big {{ font-size: 30pt; font-weight: bold; margin: 0 0 14px; }} p {{ font-size: 12pt; margin: 6px 0; }}
    .note {{ font-size: 10.5pt; text-align: left; margin-top: 40px; line-height: 1.5; }}</style></head><body>
    <p class='big' style='margin-top:40px'>UNINASSAU</p><p>Ciência da Computação | Turma 8NA | 2026.2</p>
    <div style='height:90px'></div><p class='big'>RotaCerta</p><p class='big'>Documento técnico cumulativo</p>
    <p class='big'>Sprints 01 a 09 | Grupo 04</p><div style='height:40px'></div>{team}
    <p style='margin-top:18px'>Repositório: https://github.com/alvccpj/rota-certa</p>
    <p class='note'>Consolidação em 07/11/2026. As Sprints 01 a 07 estão preservadas nas páginas 2 a 100 e a Sprint 08 nas
    páginas 101 a 112, com seus registros históricos. A Sprint 09 começa na página {first_page} e registra os testes funcionais,
    de validação e de navegação, os bugs encontrados e corrigidos e a documentação atualizada. Onde houver diferença, prevalece
    a parte mais recente.</p><p class='note' style='margin-top:10px'>Envio no Teams pelo Scrum Master após revisão da equipe.</p>
    </body></html>"""


def footer_html(count: int, first_page: int) -> str:
    pages = "".join(f"<div class='page'><span>RotaCerta | Grupo 04 | Sprint 09 | Página {first_page + n}</span></div>"
                    for n in range(count))
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>@page {{ size: A4; margin: 0; }} body {{ margin: 0; }}
    .page {{ width: 210mm; height: 297mm; position: relative; break-after: page; }}
    .page span {{ position: absolute; bottom: 9mm; width: 100%; text-align: center; font: 8pt Arial, sans-serif; color: #58606e; }}
    </style></head><body>{pages}</body></html>"""


def main() -> None:
    summary = json.loads((SOURCE / "evidencias" / "casos_de_teste.json").read_text(encoding="utf-8"))
    assert summary["reprovados"] == 0, "Há casos reprovados: conclua as correções antes de gerar o PDF."
    for name, marker in (("testes_backend_sqlite.txt", "OK"), ("testes_backend_postgresql.txt", "OK")):
        text = (SOURCE / "evidencias" / name).read_text(encoding="utf-8")
        assert text.rstrip().endswith(marker) and "FAILED" not in text, name
    assert re.search(r"\bfail 0\b", (SOURCE / "evidencias" / "testes_frontend.txt").read_text(encoding="utf-8"))
    TMP.mkdir(parents=True, exist_ok=True)
    previous = PdfReader(PREVIOUS)
    first_page = len(previous.pages) + 1
    (TMP / "parte9.html").write_text(build_html(summary), encoding="utf-8")
    (TMP / "capa.html").write_text(cover_html(first_page), encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        for name in ("parte9", "capa"):
            page.goto((TMP / f"{name}.html").as_uri(), wait_until="networkidle")
            page.pdf(path=str(TMP / f"{name}.pdf"), format="A4", print_background=True, prefer_css_page_size=True)
        count = len(PdfReader(TMP / "parte9.pdf").pages)
        (TMP / "rodape.html").write_text(footer_html(count, first_page), encoding="utf-8")
        page.goto((TMP / "rodape.html").as_uri())
        page.pdf(path=str(TMP / "rodape.pdf"), format="A4", prefer_css_page_size=True)
        browser.close()
    part, footers = PdfReader(TMP / "parte9.pdf"), PdfReader(TMP / "rodape.pdf")
    writer = PdfWriter()
    writer.append(str(TMP / "capa.pdf"))
    writer.append(previous, pages=(1, len(previous.pages)))
    for content, footer in zip(part.pages, footers.pages):
        content.merge_page(footer)
        writer.add_page(content)
    writer.add_metadata({"/Title": "Grupo 04 RotaCerta Sprints 01 a 09", "/Author": "Equipe RotaCerta Grupo 04"})
    with TARGET.open("wb") as handle:
        writer.write(handle)
    print(f"{TARGET.relative_to(ROOT)} | {len(writer.pages)} páginas | Sprint 09 nas páginas {first_page} a {first_page + count - 1}")


if __name__ == "__main__":
    main()
