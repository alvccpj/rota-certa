"""Renderiza o HTML cumulativo existente como PDF usando o Chrome."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
NAME = "Grupo_04_RotaCerta_Sprints_01_a_07"


def main() -> None:
    html_path = (ROOT / "output" / "html" / f"{NAME}.html").resolve()
    pdf_path = (ROOT / "output" / "pdf" / f"{NAME}.pdf").resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    footer = (
        "<div style='width:100%;font-family:Arial;font-size:8px;color:#58606e;text-align:center'>"
        "RotaCerta  |  Grupo 04  |  Sprints 01 a 07  |  Página "
        "<span class='pageNumber'></span></div>"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=footer,
            margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"},
        )
        browser.close()
    print(pdf_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
