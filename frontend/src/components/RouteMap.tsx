import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import type { Depot, DeliveryRoute } from "../api";
import { routeColor } from "../labels";

const RECIFE: [number, number] = [-8.0476, -34.877];

interface Props {
  routes: DeliveryRoute[];
  depot: Depot;
  /** Rota em destaque; as demais ficam esmaecidas. */
  focusId?: number | null;
  /** Índice de cor de cada rota, para manter a mesma cor da lista ao lado. */
  colorIndex?: (route: DeliveryRoute) => number;
  label?: string;
}

const escape = (text: string) =>
  text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);

/** Mapa com o ponto de saída e, para cada rota, a linha do trajeto e as paradas numeradas. */
export default function RouteMap({ routes, depot, focusId = null, colorIndex, label = "Mapa das rotas" }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const fittedRef = useRef<string>("");
  const boundsRef = useRef<L.LatLngBounds | null>(null);

  useEffect(() => {
    const map = L.map(containerRef.current!, { scrollWheelZoom: false }).setView(RECIFE, 12);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap",
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    // O contêiner só tem o tamanho final depois do layout; reenquadra quando ele chega.
    const timer = window.setTimeout(() => {
      map.invalidateSize();
      if (boundsRef.current) map.fitBounds(boundsRef.current, { padding: [32, 32], maxZoom: 15 });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const bounds: L.LatLngExpression[] = [];
    const hasDepot = depot.latitude != null && depot.longitude != null;
    const depotPoint: [number, number] | null = hasDepot ? [depot.latitude!, depot.longitude!] : null;

    routes.forEach((route, index) => {
      const color = routeColor(colorIndex ? colorIndex(route) : index);
      const dimmed = focusId != null && focusId !== route.id;
      const points: [number, number][] = route.stops.map((stop) => [stop.latitude, stop.longitude]);
      const path = depotPoint ? [depotPoint, ...points, depotPoint] : points;
      // Contorno branco por baixo para a linha aparecer sobre qualquer fundo do mapa.
      L.polyline(path, { color: "#fff", weight: 7, opacity: dimmed ? 0.3 : 0.9 }).addTo(layer);
      L.polyline(path, { color, weight: 4, opacity: dimmed ? 0.25 : 1 })
        .bindTooltip(escape(route.courier.full_name), { sticky: true })
        .addTo(layer);
      route.stops.forEach((stop) => {
        const done = stop.status === "COMPLETED" || stop.status === "FAILED";
        const icon = L.divIcon({
          className: "",
          html: `<span class="stop-pin${done ? " done" : ""}" style="--pin:${color}">${stop.sequence}</span>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        });
        L.marker([stop.latitude, stop.longitude], { icon, opacity: dimmed ? 0.35 : 1, keyboard: false })
          .bindTooltip(
            `<strong>${stop.sequence}. ${escape(stop.customer_name)}</strong><br>${escape(stop.delivery_address)}<br><span>${escape(route.courier.full_name)}</span>`,
          )
          .addTo(layer);
        bounds.push([stop.latitude, stop.longitude]);
      });
    });

    if (depotPoint) {
      L.marker(depotPoint, {
        icon: L.divIcon({ className: "", html: '<span class="depot-pin">S</span>', iconSize: [30, 30], iconAnchor: [15, 15] }),
        zIndexOffset: 1000,
        keyboard: false,
      })
        .bindTooltip(`<strong>Ponto de saída</strong><br>${escape(depot.address)}`)
        .addTo(layer);
      bounds.push(depotPoint);
    }

    // Reenquadra só quando o conjunto de pontos muda, não ao destacar uma rota.
    const signature = JSON.stringify(bounds);
    if (bounds.length && signature !== fittedRef.current) {
      fittedRef.current = signature;
      boundsRef.current = L.latLngBounds(bounds);
      map.fitBounds(boundsRef.current, { padding: [32, 32], maxZoom: 15 });
    }
  }, [routes, depot, focusId, colorIndex]);

  return (
    <div className="route-map">
      <div ref={containerRef} className="map-canvas" role="img" aria-label={label} />
    </div>
  );
}
