import type { RouteStop } from "../api";
import { formatDateTime, formatWindow } from "../labels";

const minutes = (value: number) => value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });

/** Exibe a previsão calculada pelo servidor, sem confundi-la com rastreamento ao vivo. */
export default function StopTiming({ stop }: { stop: RouteStop }) {
  return (
    <div className="stop-timing">
      <span><strong>Janela de entrega:</strong> {formatWindow(stop.desired_start, stop.desired_end)}</span>
      <span>
        <strong>Chegada estimada:</strong>{" "}
        {stop.estimated_arrival
          ? <time dateTime={stop.estimated_arrival}>{formatDateTime(stop.estimated_arrival)}</time>
          : "Ainda não calculada"}
        {stop.estimated_arrival && stop.waiting_minutes > 0 && " (inclui espera)"}
      </span>
      <div className="timing-indicators">
        {stop.timing_status === "LATE" && (
          <span className="timing-badge timing-late">Atraso previsto: {minutes(stop.delay_minutes)} min</span>
        )}
        {stop.timing_status === "ON_TIME" && stop.estimated_arrival && (
          <span className="timing-badge timing-on-time">Previsão dentro da janela</span>
        )}
        {stop.timing_status === "NO_WINDOW" && <span className="timing-badge">Sem janela definida</span>}
        {stop.waiting_minutes > 0 && (
          <span className="timing-badge timing-waiting">Espera prevista: {minutes(stop.waiting_minutes)} min até a janela</span>
        )}
      </div>
    </div>
  );
}
