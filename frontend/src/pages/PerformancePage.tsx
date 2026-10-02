import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError, type BenchmarkInput, type Capabilities, type OptimizationRun } from "../api";
import Field from "../components/Field";
import { useToast } from "../components/Toast";
import { MODE_LABELS, formatDateTime, formatKm, formatMs, formatRatio } from "../labels";

const WORKER_CHOICES = [1, 2, 4, 8, 16, 32];
const DEFAULT_INPUT: BenchmarkInput = {
  source: "SYNTHETIC",
  couriers: 16,
  stops_per_courier: 200,
  worker_counts: [1, 2, 4, 8],
  include_gpu: true,
  repetitions: 3,
  seed: 42,
};

interface RunGroup {
  id: string;
  rows: OptimizationRun[];
}

function groupRuns(runs: OptimizationRun[]): RunGroup[] {
  const groups = new Map<string, OptimizationRun[]>();
  for (const run of runs) {
    if (run.purpose !== "BENCHMARK" || !run.run_group) continue;
    groups.set(run.run_group, [...(groups.get(run.run_group) ?? []), run]);
  }
  return [...groups].map(([id, rows]) => ({ id, rows: sortRows(rows) }));
}

const MODE_ORDER = { SEQUENTIAL: 0, PARALLEL: 1, GPU: 2 } as const;

function sortRows(rows: OptimizationRun[]): OptimizationRun[] {
  return [...rows].sort(
    (a, b) => MODE_ORDER[a.execution_mode] - MODE_ORDER[b.execution_mode] || a.worker_count - b.worker_count,
  );
}

function configLabel(run: OptimizationRun): string {
  if (run.execution_mode === "PARALLEL") return `CPU · ${run.worker_count} ${run.worker_count === 1 ? "processo" : "processos"}`;
  return MODE_LABELS[run.execution_mode];
}

export default function PerformancePage() {
  const notify = useToast();
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [input, setInput] = useState<BenchmarkInput>(DEFAULT_INPUT);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<OptimizationRun[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const loadRuns = useCallback(async () => {
    try {
      setRuns(await api<OptimizationRun[]>("/optimizer/runs?limit=300"));
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }, [notify]);

  useEffect(() => {
    loadRuns();
    api<Capabilities>("/optimizer/capabilities").then((caps) => {
      setCapabilities(caps);
      setInput((current) => ({
        ...current,
        include_gpu: caps.gpu_available,
        worker_counts: current.worker_counts.filter((n) => n <= caps.cpu_count),
      }));
    });
  }, [loadRuns]);

  const groups = useMemo(() => groupRuns(runs), [runs]);
  const generations = useMemo(() => runs.filter((run) => run.purpose === "ROUTE_GENERATION").slice(0, 10), [runs]);
  const current = groups.find((group) => group.id === selected) ?? groups[0] ?? null;
  const workerChoices = WORKER_CHOICES.filter((n) => !capabilities || n <= capabilities.cpu_count);

  function update<K extends keyof BenchmarkInput>(key: K, value: BenchmarkInput[K]) {
    setInput((previous) => ({ ...previous, [key]: value }));
    setErrors((previous) => ({ ...previous, [key]: "" }));
  }

  function toggleWorkers(value: number) {
    const next = input.worker_counts.includes(value)
      ? input.worker_counts.filter((n) => n !== value)
      : [...input.worker_counts, value].sort((a, b) => a - b);
    update("worker_counts", next);
  }

  async function run() {
    if (input.worker_counts.length === 0) {
      setErrors({ worker_counts: "Escolha pelo menos uma quantidade de processos." });
      return;
    }
    setRunning(true);
    try {
      const result = await api<{ run_group: string }>("/optimizer/benchmark", { method: "POST", body: input });
      await loadRuns();
      setSelected(result.run_group);
      notify("Comparação concluída e registrada.");
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.fields);
      notify((err as Error).message, "error");
    } finally {
      setRunning(false);
    }
  }

  const synthetic = input.source === "SYNTHETIC";

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Desempenho do otimizador</h1>
          <p className="muted">
            Executa o mesmo algoritmo (vizinho mais próximo + 2-opt) em modo sequencial, paralelo em CPU e na GPU, sobre
            a mesma entrada, e registra no banco o tempo, o speedup e a eficiência.
          </p>
        </div>
      </div>

      {capabilities && (
        <p className="machine">
          <span>
            <strong>{capabilities.cpu_count}</strong> núcleos lógicos de CPU
          </span>
          <span>
            {capabilities.gpu_available ? (
              <>
                GPU <strong>{capabilities.gpu_name}</strong> disponível
              </>
            ) : (
              <>GPU indisponível: {capabilities.gpu_reason}</>
            )}
          </span>
        </p>
      )}

      <div className="form-card bench-form">
        <div className="field">
          <span className="field-label">Entrada</span>
          <div className="segmented two" role="radiogroup" aria-label="Entrada da comparação">
            {(["SYNTHETIC", "REAL"] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={input.source === value}
                className={input.source === value ? "active" : ""}
                onClick={() => update("source", value)}
              >
                {value === "SYNTHETIC" ? "Instância sintética" : "Pedidos atribuídos"}
              </button>
            ))}
          </div>
          <small>
            {synthetic
              ? "Paradas sorteadas num raio de 8 km do ponto de saída, sempre as mesmas para a mesma semente."
              : "Usa os pedidos atribuídos hoje, agrupados por entregador. Com poucos pedidos o tempo é muito pequeno para medir ganho."}
          </small>
        </div>

        {synthetic && (
          <div className="grid-3">
            <Field label="Entregadores (rotas)" name="couriers" error={errors.couriers}>
              {(props) => (
                <input
                  {...props}
                  type="number"
                  min={1}
                  max={64}
                  value={input.couriers}
                  onChange={(event) => update("couriers", Number(event.target.value))}
                />
              )}
            </Field>
            <Field label="Paradas por entregador" name="stops_per_courier" error={errors.stops_per_courier}>
              {(props) => (
                <input
                  {...props}
                  type="number"
                  min={2}
                  max={500}
                  value={input.stops_per_courier}
                  onChange={(event) => update("stops_per_courier", Number(event.target.value))}
                />
              )}
            </Field>
            <Field label="Semente" name="seed" error={errors.seed}>
              {(props) => (
                <input
                  {...props}
                  type="number"
                  min={0}
                  value={input.seed}
                  onChange={(event) => update("seed", Number(event.target.value))}
                />
              )}
            </Field>
          </div>
        )}

        <div className="field">
          <span className="field-label">Processos na CPU</span>
          <div className="filters" role="group" aria-label="Quantidades de processos">
            {workerChoices.map((n) => (
              <button
                key={n}
                type="button"
                className={input.worker_counts.includes(n) ? "chip active" : "chip"}
                aria-pressed={input.worker_counts.includes(n)}
                onClick={() => toggleWorkers(n)}
              >
                {n}
              </button>
            ))}
          </div>
          {errors.worker_counts && <p className="field-error">{errors.worker_counts}</p>}
        </div>

        <div className="grid-2">
          <Field label="Repetições por modo" name="repetitions" hint="Vale a mediana dos tempos." error={errors.repetitions}>
            {(props) => (
              <select {...props} value={input.repetitions} onChange={(event) => update("repetitions", Number(event.target.value))}>
                {[1, 3, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            )}
          </Field>
          <label className="check">
            <input
              type="checkbox"
              checked={input.include_gpu}
              disabled={!capabilities?.gpu_available}
              onChange={(event) => update("include_gpu", event.target.checked)}
            />
            Incluir a GPU (CUDA)
          </label>
        </div>

        {errors.body && <p className="alert error">{errors.body}</p>}
        <div className="form-actions">
          <button type="button" className="button primary" onClick={run} disabled={running}>
            {running ? "Executando a comparação…" : "Executar comparação"}
          </button>
        </div>
      </div>

      {current ? <Results group={current} /> : <div className="empty"><p>Nenhuma comparação registrada ainda.</p></div>}

      {groups.length > 0 && (
        <div className="history">
          <h2>Comparações registradas</h2>
          <div className="table-wrap">
            <table className="clickable">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Entrada</th>
                  <th>Rotas × paradas</th>
                  <th>Sequencial</th>
                  <th>Melhor CPU</th>
                  <th>GPU</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => {
                  const base = group.rows[0];
                  const cpu = bestCpu(group.rows);
                  const gpu = group.rows.find((row) => row.execution_mode === "GPU");
                  return (
                    <tr
                      key={group.id}
                      className={group.id === current?.id ? "selected" : undefined}
                      onClick={() => setSelected(group.id)}
                    >
                      <td className="nowrap">{formatDateTime(base.executed_at)}</td>
                      <td>{base.input_source === "SYNTHETIC" ? "Sintética" : "Pedidos reais"}</td>
                      <td className="nowrap">
                        {base.courier_count} × {Math.round(base.order_count / Math.max(base.courier_count, 1))}
                      </td>
                      <td className="nowrap">{formatMs(base.execution_time_ms)}</td>
                      <td className="nowrap">{cpu ? `${formatRatio(cpu.speedup)}× com ${cpu.worker_count}` : "—"}</td>
                      <td className="nowrap">{gpu ? `${formatRatio(gpu.speedup)}×` : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {generations.length > 0 && (
        <div className="history">
          <h2>Últimas gerações de rotas</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Modo</th>
                  <th>Pedidos</th>
                  <th>Rotas</th>
                  <th>Tempo</th>
                  <th>Distância total</th>
                </tr>
              </thead>
              <tbody>
                {generations.map((run) => (
                  <tr key={run.id}>
                    <td className="nowrap">{formatDateTime(run.executed_at)}</td>
                    <td>{configLabel(run)}</td>
                    <td>{run.order_count}</td>
                    <td>{run.courier_count}</td>
                    <td className="nowrap">{formatMs(run.execution_time_ms)}</td>
                    <td className="nowrap">{formatKm(run.total_distance_km)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

function bestCpu(rows: OptimizationRun[]): OptimizationRun | null {
  const parallel = rows.filter((row) => row.execution_mode === "PARALLEL" && row.speedup != null);
  return parallel.reduce<OptimizationRun | null>((best, row) => (!best || row.speedup! > best.speedup! ? row : best), null);
}

function Results({ group }: { group: RunGroup }) {
  const base = group.rows.find((row) => row.execution_mode === "SEQUENTIAL") ?? group.rows[0];
  const cpu = bestCpu(group.rows);
  const gpu = group.rows.find((row) => row.execution_mode === "GPU");
  const parallel = group.rows.filter((row) => row.execution_mode === "PARALLEL");
  const allSame = group.rows.every((row) => row.same_routes !== false);

  return (
    <div className="results">
      <div className="results-head">
        <h2>Resultado</h2>
        <p className="muted">
          {formatDateTime(base.executed_at)} · {base.input_source === "SYNTHETIC" ? "instância sintética" : "pedidos reais"} ·{" "}
          {base.courier_count} rotas, {base.order_count} paradas
        </p>
      </div>

      <div className="stat-tiles">
        <div className="stat-tile">
          <span>Sequencial (linha de base)</span>
          <strong>{formatMs(base.execution_time_ms)}</strong>
        </div>
        <div className="stat-tile">
          <span>Melhor resultado em CPU</span>
          <strong>{cpu ? `${formatRatio(cpu.speedup)}×` : "—"}</strong>
          {cpu && (
            <small>
              com {cpu.worker_count} processos · eficiência {formatRatio((cpu.efficiency ?? 0) * 100, 0)}%
            </small>
          )}
        </div>
        <div className="stat-tile">
          <span>GPU (CUDA)</span>
          <strong>{gpu ? `${formatRatio(gpu.speedup)}×` : "—"}</strong>
          {gpu && <small>{formatMs(gpu.execution_time_ms)} · {gpu.worker_count.toLocaleString("pt-BR")} threads</small>}
        </div>
        <div className={allSame ? "stat-tile" : "stat-tile warn"}>
          <span>Qualidade das rotas</span>
          <strong>{allSame ? "Idênticas" : "Diferentes"}</strong>
          <small>{formatKm(base.total_distance_km)} no total em todos os modos</small>
        </div>
      </div>

      {parallel.length > 0 && <SpeedupChart rows={parallel} />}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Configuração</th>
              <th>Tempo (mediana)</th>
              <th>Speedup</th>
              <th>Eficiência</th>
              <th>Distância total</th>
              <th>Mesmas rotas do sequencial</th>
            </tr>
          </thead>
          <tbody>
            {group.rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <strong>{configLabel(row)}</strong>
                </td>
                <td className="num">{formatMs(row.execution_time_ms)}</td>
                <td className="num">{row.speedup != null ? `${formatRatio(row.speedup)}×` : "—"}</td>
                <td className="num">{row.efficiency != null ? `${formatRatio(row.efficiency * 100, 0)}%` : "—"}</td>
                <td className="nowrap">{formatKm(row.total_distance_km)}</td>
                <td>{row.same_routes ? "Sim" : "Não"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="inline-note">
        Speedup = tempo sequencial ÷ tempo do modo. Eficiência = speedup ÷ número de processos (100% seria o ganho
        ideal). Na GPU a eficiência não se aplica: o paralelismo é de milhares de threads, não de processos.
      </p>
    </div>
  );
}

/** Barras horizontais com o speedup de cada quantidade de processos e a marca do speedup ideal. */
function SpeedupChart({ rows }: { rows: OptimizationRun[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(...rows.map((row) => Math.max(row.speedup ?? 0, row.worker_count)), 1);
  const ticks = niceTicks(max);
  const scale = (value: number) => (value / ticks[ticks.length - 1]) * 100;

  return (
    <figure className="speedup-chart">
      <figcaption>
        <strong>Speedup da CPU por número de processos</strong>
        <span className="legend">
          <span className="legend-bar" aria-hidden="true" /> Speedup medido
          <span className="legend-ideal" aria-hidden="true" /> Ideal (igual ao número de processos)
        </span>
      </figcaption>
      <div className="chart-rows" role="list">
        {rows.map((row) => (
          <div
            key={row.id}
            className="chart-row"
            role="listitem"
            onMouseEnter={() => setHover(row.id)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(row.id)}
            onBlur={() => setHover(null)}
            tabIndex={0}
            aria-label={`${row.worker_count} processos: speedup ${formatRatio(row.speedup)}, ideal ${row.worker_count}`}
          >
            <span className="chart-label">{row.worker_count}</span>
            <div className="chart-track">
              {ticks.map((tick) => (
                <span key={tick} className="chart-grid" style={{ left: `${scale(tick)}%` }} />
              ))}
              <span className="chart-bar" style={{ width: `${scale(row.speedup ?? 0)}%` }} />
              <span className="chart-ideal" style={{ left: `${scale(row.worker_count)}%` }} />
              <span className="chart-value" style={{ left: `${scale(row.speedup ?? 0)}%` }}>
                {formatRatio(row.speedup)}×
              </span>
              {hover === row.id && (
                <span className="chart-tooltip" role="tooltip" style={{ left: `${scale(row.speedup ?? 0)}%` }}>
                  <strong>{row.worker_count} {row.worker_count === 1 ? "processo" : "processos"}</strong>
                  <span>Tempo {formatMs(row.execution_time_ms)}</span>
                  <span>Speedup {formatRatio(row.speedup)}× (ideal {row.worker_count}×)</span>
                  <span>Eficiência {formatRatio((row.efficiency ?? 0) * 100, 0)}%</span>
                </span>
              )}
            </div>
          </div>
        ))}
        <div className="chart-row axis" aria-hidden="true">
          <span className="chart-label">Processos</span>
          <div className="chart-track">
            {ticks.map((tick) => (
              <span key={tick} className="chart-tick" style={{ left: `${scale(tick)}%` }}>
                {tick}×
              </span>
            ))}
          </div>
        </div>
      </div>
    </figure>
  );
}

function niceTicks(max: number): number[] {
  const step = max <= 4 ? 1 : max <= 10 ? 2 : max <= 20 ? 5 : 10;
  const top = Math.ceil(max / step) * step;
  return Array.from({ length: top / step + 1 }, (_, index) => index * step);
}
