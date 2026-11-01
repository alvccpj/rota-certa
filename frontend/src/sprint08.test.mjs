// Run from frontend: node --test src/sprint08.test.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

// Compile the actual frontend modules in memory using the existing build tool.
const compiled = await build({
  stdin: {
    contents: `export { csvCell } from "./reporting";
      export { default as StopTiming } from "./components/StopTiming";
      export { default as NavigationLink } from "./components/NavigationLink";`,
    resolveDir: fileURLToPath(new URL(".", import.meta.url)),
    loader: "tsx",
  },
  bundle: true,
  platform: "node",
  packages: "external",
  format: "cjs",
  jsx: "automatic",
  write: false,
});
const module = { exports: {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(createRequire(import.meta.url), module, module.exports);
const { csvCell, StopTiming, NavigationLink } = module.exports;
const render = (Component, props) => renderToStaticMarkup(createElement(Component, props));

for (const [input, expected] of [
  ["=1+1", `"'=1+1"`],
  ["+1+1", `"'+1+1"`],
  ["-1+1", `"'-1+1"`],
  ["@SUM(A1)", `"'@SUM(A1)"`],
  ["\t=1+1", `"'\t=1+1"`],
  ["\r=1+1", `"'\r=1+1"`],
  ["\n=1+1", `"'\n=1+1"`],
]) {
  test(`CSV neutralizes formula prefix ${JSON.stringify(input[0])}`, () => {
    assert.equal(csvCell(input), expected);
  });
}

test("CSV preserves text, accents, separators, quotes, nulls and numeric IDs", () => {
  assert.equal(csvCell('João; "Centro"'), '"João; ""Centro"""');
  assert.equal(csvCell("Rua A\r\nBloco 2"), '"Rua A\r\nBloco 2"');
  assert.equal(csvCell("cliente@exemplo.com"), '"cliente@exemplo.com"');
  assert.equal(csvCell("2026-11-01"), '"2026-11-01"');
  assert.equal(csvCell(null), '""');
  assert.equal(csvCell(42), '"42"');
  assert.equal(csvCell(0), '"0"');
});

test("CSV escapes embedded quotes even in formula payloads", () => {
  assert.equal(csvCell('=HYPERLINK("https://example.com";"Abrir")'), `"'=HYPERLINK(""https://example.com"";""Abrir"")"`);
});

const stop = {
  desired_start: "2026-11-01T10:00:00-03:00",
  desired_end: "2026-11-01T11:00:00-03:00",
  estimated_arrival: "2026-11-01T10:00:00-03:00",
  timing_status: "ON_TIME",
  waiting_minutes: 30,
  delay_minutes: 0,
};

test("Stop timing shows window, dated ETA and waiting separately", () => {
  const html = render(StopTiming, { stop });
  assert.match(html, /Janela de entrega/);
  assert.match(html, /Chegada estimada/);
  assert.match(html, /dateTime="2026-11-01T10:00:00-03:00"/);
  assert.match(html, /Previsão dentro da janela/);
  assert.match(html, /Espera prevista: 30 min até a janela/);
  assert.doesNotMatch(html, /Atraso previsto/);
});

test("Late stop displays the specific delay without an on-time label", () => {
  const html = render(StopTiming, { stop: { ...stop, timing_status: "LATE", waiting_minutes: 0, delay_minutes: 17 } });
  assert.match(html, /Atraso previsto: 17 min/);
  assert.doesNotMatch(html, /Previsão dentro da janela|Espera prevista/);
});

test("No-window and missing-ETA stops do not claim an on-time estimate", () => {
  const html = render(StopTiming, { stop: { ...stop, desired_start: null, desired_end: null, estimated_arrival: null, timing_status: "NO_WINDOW", waiting_minutes: 0 } });
  assert.match(html, /Sem janela definida/);
  assert.match(html, /Ainda não calculada/);
  assert.doesNotMatch(html, /Previsão dentro da janela|Atraso previsto|Espera prevista/);
});

test("Open-ended delivery windows are supported", () => {
  assert.match(render(StopTiming, { stop: { ...stop, desired_end: null } }), /A partir de/);
  assert.match(render(StopTiming, { stop: { ...stop, desired_start: null } }), /Até/);
});

test("Navigation uses encoded coordinates, a fixed HTTPS host and safe new-tab attributes", () => {
  const html = render(NavigationLink, { latitude: -8.0476, longitude: -34.877, orderId: 42 });
  assert.match(html, /https:\/\/www.google.com\/maps\/dir\/\?api=1/);
  assert.match(html, /destination=-8.0476%2C-34.877/);
  assert.match(html, /target="_blank"/);
  assert.match(html, /rel="noopener noreferrer"/);
  assert.match(html, /aria-label="Navegar até o pedido #42.*abre em nova aba/);
});

test("Navigation rejects invalid coordinates and accepts the equator and meridian", () => {
  for (const [latitude, longitude] of [[NaN, 0], [0, Infinity], [91, 0], [0, -181], [null, 0], ["-8", 0]]) {
    assert.equal(render(NavigationLink, { latitude, longitude, orderId: 1 }), "");
  }
  assert.match(render(NavigationLink, { latitude: 0, longitude: 0, orderId: 1 }), /destination=0%2C0/);
});
