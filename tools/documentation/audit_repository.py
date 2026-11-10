"""Confere organização, links locais Markdown e padrões de segredo sem imprimir valores."""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/sprint-11/evidencias/organizacao_github.json"
SECRET_PATTERNS = {
    "chave_privada": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "token_github": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "chave_openai": re.compile(r"\bsk-proj-[A-Za-z0-9_-]{30,}\b"),
    "chave_aws": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=OUT.parent)
    args = parser.parse_args()
    destination = args.evidence_dir / OUT.name
    paths = sorted(set(subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()))
    unwanted, secrets, bad_links = [], [], []
    scanned, checked = 0, 0
    for name in paths:
        path = Path(name)
        if (path.name == ".env" or set(path.parts) & {"node_modules", ".venv", "__pycache__", "dist", "tmp"}
                or path.suffix in {".pyc", ".db", ".sqlite", ".sqlite3"}):
            unwanted.append(name)
        if path.suffix.lower() not in {".py", ".md", ".ts", ".tsx", ".mjs", ".json", ".yaml", ".yml", ".txt", ".sql", ".example"}:
            continue
        text = (ROOT / path).read_text(encoding="utf-8")
        scanned += 1
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                secrets.append({"arquivo": name, "linha": text.count("\n", 0, match.start()) + 1, "tipo": label})
        if path.suffix.lower() != ".md":
            continue
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or re.match(r"[a-zA-Z]+:", target):
                continue
            checked += 1
            if not (ROOT / path.parent / target).resolve().exists():
                bad_links.append({"arquivo": name, "destino": target})
    ignore_targets = [".env", "backend/.env", "frontend/.env", "backend/rotacerta-demo.db", "tmp/verificacao.txt"]
    ignored = {name: subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT).returncode == 0
               for name in ignore_targets}
    result = {"executado_em": datetime.now(ZoneInfo("America/Recife")).isoformat(timespec="seconds"),
              "arquivos_versionados_ou_preparados": len(paths), "arquivos_texto_inspecionados": scanned,
              "links_locais_conferidos": checked, "artefatos_locais_indevidos": unwanted,
              "padroes_de_segredo_encontrados": secrets, "links_quebrados": bad_links,
              "protecao_gitignore": ignored,
              "limites": "Verifica arquivos atuais de texto e padrões explícitos, não todo o histórico Git nem segredos em serviços externos. Exemplos públicos de demonstração permanecem identificados.",
              "situacao": "Aprovado" if not (unwanted or secrets or bad_links) and all(ignored.values()) else "Reprovado"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["situacao"] != "Aprovado":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
