// Run from frontend: node --test src/sprint09.test.mjs
// Regressões da Sprint 09: destino após o login (BUG-06), ID inválido no endereço (BUG-05)
// e validações dos formulários usadas pelos testes de validação.
import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const compiled = await build({
  stdin: {
    contents: `export { canAccess, homePath, landingPath } from "./access";
      export { api, ApiError } from "./api";
      export { check, parseDecimal, formatPhone } from "./validation";`,
    resolveDir: fileURLToPath(new URL(".", import.meta.url)),
    loader: "ts",
  },
  bundle: true,
  platform: "node",
  format: "cjs",
  write: false,
  define: { "import.meta.env": JSON.stringify({ VITE_API_URL: "http://api.test" }) },
});
const module = { exports: {} };
new Function("module", "exports", compiled.outputFiles[0].text)(module, module.exports);
const { canAccess, homePath, landingPath, api, check, parseDecimal, formatPhone } = module.exports;

test("Cada perfil tem a sua página inicial", () => {
  assert.equal(homePath("ADMIN"), "/painel");
  assert.equal(homePath("ATTENDANT"), "/painel");
  assert.equal(homePath("COURIER"), "/entregas");
});

for (const [role, path, expected] of [
  ["ADMIN", "/relatorios", "/relatorios"],
  ["ADMIN", "/clientes?busca=Ana", "/clientes?busca=Ana"],
  ["ADMIN", "/usuarios/3/editar", "/usuarios/3/editar"],
  ["ATTENDANT", "/pedidos/2", "/pedidos/2"],
  ["ATTENDANT", "/usuarios", "/painel"],
  ["ATTENDANT", "/desempenho", "/painel"],
  ["ADMIN", "/entregas", "/painel"],
  ["COURIER", "/pedidos/2", "/pedidos/2"],
  ["COURIER", "/relatorios", "/entregas"],
  ["COURIER", "/pedidos/2/editar", "/entregas"],
  ["COURIER", "/pedidos/novo", "/entregas"],
  ["ADMIN", "/login", "/painel"],
  ["ADMIN", "/cadastro", "/painel"],
  ["ADMIN", "//site-externo.com/painel", "/painel"],
  ["ADMIN", "https://site-externo.com", "/painel"],
  ["ADMIN", undefined, "/painel"],
]) {
  test(`Depois do login, ${role} pedindo ${path} vai para ${expected}`, () => {
    assert.equal(landingPath(role, path), expected);
  });
}

test("A regra de acesso ignora barra final, busca e âncora", () => {
  assert.equal(canAccess("COURIER", "/pedidos/7/"), true);
  assert.equal(canAccess("ATTENDANT", "/usuarios/?x=1"), false);
  assert.equal(canAccess("ADMIN", "/desempenho#medicoes"), true);
});

async function apiErrorFor(status, body) {
  globalThis.fetch = async () => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  try {
    await api("/orders/abc");
  } catch (error) {
    return error;
  }
  assert.fail("A chamada deveria falhar");
}

test("ID inválido no endereço é tratado como registro não encontrado", async () => {
  const error = await apiErrorFor(422, {
    detail: [{ type: "int_parsing", loc: ["path", "order_id"], msg: "Input should be a valid integer" }],
  });
  assert.equal(error.status, 404);
  assert.match(error.message, /Registro não encontrado/);
  assert.deepEqual(error.fields, {});
});

test("Erros de formulário continuam destacando o campo", async () => {
  const error = await apiErrorFor(422, {
    detail: [{ type: "greater_than", loc: ["body", "weight_kg"], msg: "", ctx: { gt: 0 } }],
  });
  assert.equal(error.status, 422);
  assert.equal(error.fields.weight_kg, "Informe um valor maior que 0.");
  assert.equal(error.message, "Corrija o campo destacado.");
});

test("Mensagem de regra de negócio da API é exibida como veio", async () => {
  const error = await apiErrorFor(422, { detail: "O horário final da entrega já passou. Informe um horário futuro." });
  assert.equal(error.message, "O horário final da entrega já passou. Informe um horário futuro.");
});

test("Falha de rede mostra orientação ao usuário", async () => {
  globalThis.fetch = async () => {
    throw new TypeError("fetch failed");
  };
  await assert.rejects(api("/orders"), (error) => error.status === 0 && /Não foi possível falar com o servidor/.test(error.message));
});

for (const [label, actual, expected] of [
  ["e-mail sem domínio", () => check.email("ana@empresa"), "Informe um e-mail válido, como nome@empresa.com.br."],
  ["e-mail vazio", () => check.email("  "), "Informe o e-mail."],
  ["telefone sem DDD", () => check.phone("98800-1001"), "Informe o telefone com DDD, por exemplo (81) 98800-1001."],
  ["telefone começando com zero", () => check.phone("(01) 98800-1001"), "Informe o telefone com DDD, por exemplo (81) 98800-1001."],
  ["senha curta", () => check.password("abc1"), "Use pelo menos 8 caracteres."],
  ["senha sem número", () => check.password("abcdefgh"), "A senha precisa ter letras e números."],
  ["nome só com números", () => check.personName("12345"), "Use pelo menos duas letras."],
  ["peso zero", () => check.number("0", { label: "o peso", min: 0 }), "Informe um valor maior que 0."],
  ["peso acima do limite", () => check.number("501", { label: "o peso", min: 0, max: 500 }), "O valor máximo é 500."],
  ["peso com texto", () => check.number("dois", { label: "o peso", min: 0 }), "Informe um número."],
  ["telefone válido", () => check.phone("+55 81 98800-1001"), null],
  ["senha válida", () => check.password("rotacerta123"), null],
]) {
  test(`Validação do formulário: ${label}`, () => {
    assert.equal(actual(), expected);
  });
}

test("Números aceitam vírgula decimal e telefones são formatados", () => {
  assert.equal(parseDecimal("2,5"), 2.5);
  assert.equal(parseDecimal("abc"), null);
  assert.equal(formatPhone("81988001001"), "(81) 98800-1001");
  assert.equal(formatPhone("8133331001"), "(81) 3333-1001");
});
