"""Exporta o contrato e o catálogo a partir da aplicação, sem conectar ao banco.

    backend/.venv/bin/python tools/documentation/export_api_docs.py
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.routing import APIRoute
from app.main import app


def roles_for(dependant):
    roles = set()
    for child in dependant.dependencies:
        call = child.call
        if getattr(call, "__name__", "") == "dependency":
            roles.update(inspect.getclosurevars(call).nonlocals.get("roles", ()))
        roles.update(roles_for(child))
    return roles


def schema_name(schema):
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if schema.get("type") == "array":
        return f"lista de {schema_name(schema['items'])}"
    if "anyOf" in schema:
        return " ou ".join(schema_name(item) for item in schema["anyOf"])
    return schema.get("type", "objeto")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, help="Destino opcional do catálogo JSON desta execução.")
    args = parser.parse_args()
    target = ROOT / "docs" / "api"
    target.mkdir(parents=True, exist_ok=True)
    contract = app.openapi()
    routes = {(method.lower(), route.path): route for route in app.routes
              if isinstance(route, APIRoute) for method in route.methods}
    lines = ["# Catálogo dos endpoints", "",
             f"Contrato da versão `{app.version}`, gerado por `tools/documentation/export_api_docs.py`.", "",
             "Consulte [o guia e exemplos](README.md) e [o contrato OpenAPI completo](openapi.json). "
             "Os modelos do contrato detalham todos os campos, tipos, limites, valores padrão e obrigatoriedade.", "",
             "ADMIN = administrador; ATTENDANT = atendente; COURIER = entregador. "
             "O perfil não substitui as regras sobre estabelecimento e propriedade do registro.", ""]
    catalog = []
    for path, methods in contract["paths"].items():
        for method, operation in methods.items():
            route = routes[(method, path)]
            roles = sorted(roles_for(route.dependant))
            access = ", ".join(roles) if roles else ("Usuário autenticado" if operation.get("security") else "Público")
            catalog.append({"metodo": method.upper(), "rota": path, "acesso": access,
                            "entrada": schema_name(operation.get("requestBody", {}).get("content", {})
                                                   .get("application/json", {}).get("schema", {}))
                            if operation.get("requestBody") else None})
            lines += [f"## {method.upper()} {path}", "", f"**Acesso:** {access}.", ""]
            if operation.get("description"):
                lines += [operation["description"], ""]
            params = operation.get("parameters", [])
            if params:
                lines += ["| Parâmetro | Local | Obrigatório | Tipo e limites |",
                          "| --- | --- | --- | --- |"]
                for param in params:
                    schema = param["schema"]
                    details = {k: v for k, v in schema.items() if k not in ("title", "description")}
                    lines.append(f"| `{param['name']}` | {param['in']} | {'Sim' if param.get('required') else 'Não'} | "
                                 f"`{json.dumps(details, ensure_ascii=False)}` |")
                lines.append("")
            if operation.get("requestBody"):
                lines += [f"**Corpo JSON:** `{catalog[-1]['entrada']}` "
                          "(veja a definição completa em `components.schemas` no contrato).", ""]
            lines += ["| HTTP | Resposta |", "| --- | --- |"]
            for code, response in operation["responses"].items():
                schema = response.get("content", {}).get("application/json", {}).get("schema")
                label = schema_name(schema) if schema else "Sem corpo" if code == "204" else response["description"]
                lines.append(f"| {code} | {label} |")
            if operation.get("security"):
                lines.append("| 401 | Sessão ausente, inválida, expirada ou usuário desativado |")
            if roles:
                lines.append("| 403 | Perfil sem permissão |")
            lines += ["", "Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) "
                      "dependem da operação; veja o guia de erros e as regras de negócio.", ""]
    (target / "openapi.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "ENDPOINTS.md").write_text("\n".join(lines), encoding="utf-8")
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / "catalogo_api.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(catalog)} operações HTTP documentadas; versão {app.version}.")


if __name__ == "__main__":
    main()
