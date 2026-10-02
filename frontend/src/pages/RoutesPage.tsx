import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link } from "react-router";
import {
  api,
  ApiError,
  type Capabilities,
  type DeliveryRoute,
  type ExecutionMode,
  type GeocodeResult,
  type RouteGeneration,
  type RoutesOverview,
} from "../api";
import { StatusBadge } from "../components/Badges";
import Field from "../components/Field";
import MapPicker from "../components/MapPicker";
import RouteMap from "../components/RouteMap";
import { useToast } from "../components/Toast";
import {
  MODE_LABELS,
  ROUTE_STATUS_LABELS,
  formatDuration,
  formatKm,
  formatMs,
  formatTime,
  routeColor,
} from "../labels";
import { useUser } from "../session";

const MODES: ExecutionMode[] = ["SEQUENTIAL", "PARALLEL", "GPU"];

export default function RoutesPage() {
  const user = useUser();
  const notify = useToast();
  const [overview, setOverview] = useState<RoutesOverview | null>(null);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [mode, setMode] = useState<ExecutionMode>("SEQUENTIAL");
  const [workers, setWorkers] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<RouteGeneration | null>(null);
  const [focusId, setFocusId] = useState<number | null>(null);
  const [editingDepot, setEditingDepot] = useState(false);

  const load = useCallback(async () => {
    try {
      setOverview(await api<RoutesOverview>("/routes"));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
    api<Capabilities>("/optimizer/capabilities").then(setCapabilities, () => setCapabilities(null));
  }, [load]);

  // A cor de cada rota segue o entregador, não a posição na lista.
  const courierOrder = useMemo(
    () => [...new Set((overview?.routes ?? []).map((route) => route.courier.id))].sort((a, b) => a - b),
    [overview],
  );
  const colorIndex = useCallback((route: DeliveryRoute) => courierOrder.indexOf(route.courier.id), [courierOrder]);

  async function generate() {
    setBusy(true);
    try {
      const result = await api<RouteGeneration>("/routes/generate", {
        method: "POST",
        body: { mode, workers: mode === "PARALLEL" ? workers : null },
      });
      setOverview(result);
      setLastRun(result);
      setFocusId(null);
      notify(`${result.routes.filter((r) => r.status === "PLANNED").length} rota(s) gerada(s).`);
    } catch (err) {
      notify((err as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  const depot = overview?.depot;
  const depotMissing = depot != null && (depot.latitude == null || depot.longitude == null);
  const gpuUnavailable = capabilities != null && !capabilities.gpu_available;
  const workerOptions = capabilities
    ? [...new Set([2, 4, 8, capabilities.cpu_count])].filter((n) => n <= capabilities.cpu_count).sort((a, b) => a - b)
    : [2, 4];

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Rotas</h1>
          <p className="muted">
            O sistema ordena as entregas de cada entregador a partir dos pedidos atribuídos, saindo e voltando ao
            ponto de saída.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert error" role="alert">
          {error}{" "}
          <button type="button" className="link" onClick={load}>
            Tentar de novo
          </button>
        </div>
      )}

      {depot && (depotMissing || editingDepot) && (
        user.role === "ADMIN" ? (
          <DepotForm
            initialAddress={depot.address}
            initial={depotMissing ? null : { latitude: depot.latitude!, longitude: depot.longitude! }}
            missing={depotMissing}
            onCancel={depotMissing ? undefined : () => setEditingDepot(false)}
            onSaved={() => {
              setEditingDepot(false);
              load();
            }}
          />
        ) : (
          <p className="alert info">
            O ponto de saída das entregas ainda não foi marcado no mapa. Peça ao administrador para marcá-lo na página
            de rotas.
          </p>
        )
      )}

      <div className="route-controls">
        <div className="field">
          <span className="field-label">Modo de execução do otimizador</span>
          <div className="segmented three" role="radiogroup" aria-label="Modo de execução">
            {MODES.map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={mode === value}
                className={mode === value ? "active" : ""}
                disabled={value === "GPU" && gpuUnavailable}
                title={value === "GPU" && gpuUnavailable ? capabilities?.gpu_reason ?? undefined : undefined}
                onClick={() => setMode(value)}
              >
                {MODE_LABELS[value]}
              </button>
            ))}
          </div>
        </div>
        {mode === "PARALLEL" && (
          <div className="field workers-field">
            <label htmlFor="campo-workers">Processos</label>
            <select
              id="campo-workers"
              value={workers ?? ""}
              onChange={(event) => setWorkers(event.target.value ? Number(event.target.value) : null)}
            >
              <option value="">Automático (um por entregador)</option>
              {workerOptions.map((n) => (
                <option key={n} value={n}>
                  {n} processos
                </option>
              ))}
            </select>
          </div>
        )}
        <button type="button" className="button primary" onClick={generate} disabled={busy || depotMissing}>
          {busy ? "Gerando rotas…" : "Gerar rotas"}
        </button>
        {user.role === "ADMIN" && !depotMissing && !editingDepot && (
          <button type="button" className="button quiet" onClick={() => setEditingDepot(true)}>
            Alterar ponto de saída
          </button>
        )}
      </div>
      {mode === "GPU" && capabilities?.gpu_name && (
        <p className="inline-note">Cálculo na {capabilities.gpu_name}, com um bloco de threads CUDA por entregador.</p>
      )}

      {overview && (
        <p className="route-summary">
          <strong>{overview.waiting_orders}</strong>{" "}
          {overview.waiting_orders === 1 ? "pedido atribuído aguardando rota" : "pedidos atribuídos aguardando rota"}
          {overview.waiting_orders > 0 && overview.routes.length > 0 && " · gere as rotas de novo para incluí-los"}
        </p>
      )}

      {lastRun && (
        <div className="alert info run-result" role="status">
          <p>
            Rotas calculadas em <strong>{formatMs(lastRun.run.execution_time_ms)}</strong> no modo{" "}
            <strong>{MODE_LABELS[lastRun.run.execution_mode]}</strong>
            {lastRun.run.execution_mode === "PARALLEL" && ` com ${lastRun.run.worker_count} processo(s)`}:{" "}
            {lastRun.run.order_count} pedido(s), {formatKm(lastRun.run.total_distance_km)} no total.
          </p>
          {lastRun.skipped.map((item) => (
            <p key={item.courier.id}>
              <strong>{item.courier.full_name}:</strong> {item.reason}
            </p>
          ))}
        </div>
      )}

      {overview && depot && (
        overview.routes.length === 0 ? (
          <div className="empty">
            <p>Nenhuma rota para hoje. Atribua os pedidos aos entregadores e clique em Gerar rotas.</p>
            <Link className="button quiet" to="/pedidos">
              Ver pedidos
            </Link>
          </div>
        ) : (
          <div className="routes-layout">
            <RouteMap routes={overview.routes} depot={depot} focusId={focusId} colorIndex={colorIndex} />
            <ul className="route-list" aria-label="Rotas dos entregadores">
              {overview.routes.map((route) => (
                <RouteCard
                  key={route.id}
                  route={route}
                  color={routeColor(colorIndex(route))}
                  focused={focusId === route.id}
                  onFocus={() => setFocusId(focusId === route.id ? null : route.id)}
                />
              ))}
            </ul>
          </div>
        )
      )}
    </section>
  );
}

function RouteCard({
  route,
  color,
  focused,
  onFocus,
}: {
  route: DeliveryRoute;
  color: string;
  focused: boolean;
  onFocus: () => void;
}) {
  return (
    <li className={focused ? "route-card focused" : "route-card"} style={{ "--route": color } as CSSProperties}>
      <button type="button" className="route-card-head" onClick={onFocus} aria-pressed={focused}>
        <span className="route-swatch" aria-hidden="true" />
        <span className="route-courier">{route.courier.full_name}</span>
        <span className={`route-status route-${route.status.toLowerCase()}`}>{ROUTE_STATUS_LABELS[route.status]}</span>
      </button>
      <dl className="facts">
        <div>
          <dt>Paradas</dt>
          <dd>{route.stops.length}</dd>
        </div>
        <div>
          <dt>Distância</dt>
          <dd>{formatKm(route.total_distance_km)}</dd>
        </div>
        <div>
          <dt>Duração estimada</dt>
          <dd>{formatDuration(route.estimated_duration_min)}</dd>
        </div>
        <div>
          <dt>Calculada em</dt>
          <dd>{MODE_LABELS[route.execution_mode]}</dd>
        </div>
      </dl>
      <ol className="stop-list">
        {route.stops.map((stop) => (
          <li key={stop.order_id} className={stop.status === "COMPLETED" ? "done" : undefined}>
            <span className="stop-number">{stop.sequence}</span>
            <div>
              <Link to={`/pedidos/${stop.order_id}`}>{stop.customer_name}</Link>
              <span className="sub">{stop.delivery_address}</span>
            </div>
            <div className="stop-meta">
              <span>{formatTime(stop.estimated_arrival)}</span>
              <StatusBadge status={stop.order_status} />
            </div>
          </li>
        ))}
      </ol>
    </li>
  );
}

function DepotForm({
  initialAddress,
  initial,
  missing,
  onCancel,
  onSaved,
}: {
  initialAddress: string;
  initial: { latitude: number; longitude: number } | null;
  missing: boolean;
  onCancel?: () => void;
  onSaved: () => void;
}) {
  const notify = useToast();
  const [address, setAddress] = useState(initialAddress);
  const [point, setPoint] = useState(initial);
  const [results, setResults] = useState<GeocodeResult[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  async function search() {
    setMessage(null);
    try {
      const found = await api<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(address.trim())}`);
      setResults(found);
      if (found.length === 0) setMessage("Nenhum endereço encontrado. Marque o ponto direto no mapa.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function save() {
    if (!point) {
      setErrors({ map: "Marque no mapa de onde saem as entregas." });
      return;
    }
    setSaving(true);
    try {
      await api("/establishment/depot", {
        method: "PUT",
        body: { depot_address: address, latitude: point.latitude, longitude: point.longitude },
      });
      notify("Ponto de saída salvo.");
      onSaved();
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.fields);
      notify((err as Error).message, "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="form-card depot-card">
      <div>
        <h2>Ponto de saída das entregas</h2>
        <p className="muted">
          {missing
            ? "Antes de gerar as rotas, marque no mapa de onde os entregadores saem. Todas as rotas começam e terminam nele."
            : "Todas as rotas começam e terminam neste ponto."}
        </p>
      </div>
      <Field label="Endereço" name="depot_address" error={errors.depot_address}>
        {(props) => (
          <div className="input-with-action">
            <input {...props} value={address} onChange={(event) => setAddress(event.target.value)} />
            <button type="button" className="button quiet" onClick={search} disabled={address.trim().length < 5}>
              Buscar endereço
            </button>
          </div>
        )}
      </Field>
      {message && <p className="alert info">{message}</p>}
      {results && results.length > 0 && (
        <ul className="lookup-results" aria-label="Endereços encontrados">
          {results.map((result) => (
            <li key={`${result.latitude},${result.longitude}`}>
              <button
                type="button"
                onClick={() => {
                  setPoint({ latitude: result.latitude, longitude: result.longitude });
                  setResults(null);
                  setErrors({});
                }}
              >
                {result.label}
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="map-field">
        <span className="field-label">Local no mapa (clique para marcar)</span>
        <MapPicker
          latitude={point?.latitude ?? null}
          longitude={point?.longitude ?? null}
          onPick={(latitude, longitude) => {
            setPoint({ latitude, longitude });
            setErrors({});
          }}
          invalid={Boolean(errors.map)}
        />
        {errors.map && <p className="field-error">{errors.map}</p>}
      </div>
      <div className="form-actions">
        {onCancel && (
          <button type="button" className="button quiet" onClick={onCancel}>
            Cancelar
          </button>
        )}
        <button type="button" className="button primary" onClick={save} disabled={saving}>
          {saving ? "Salvando…" : "Salvar ponto de saída"}
        </button>
      </div>
    </div>
  );
}
