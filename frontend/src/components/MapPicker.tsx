import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";

const RECIFE: [number, number] = [-8.0476, -34.877];

interface Props {
  latitude: number | null;
  longitude: number | null;
  /** Sem onPick o mapa só mostra o ponto, sem permitir marcar outro. */
  onPick?: (latitude: number, longitude: number) => void;
  zoom?: number;
  invalid?: boolean;
}

const round = (value: number) => Math.round(value * 1e6) / 1e6;

export default function MapPicker({ latitude, longitude, onPick, zoom = 13, invalid = false }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.CircleMarker | null>(null);
  const pickRef = useRef(onPick);
  pickRef.current = onPick;

  useEffect(() => {
    const start: [number, number] = latitude != null && longitude != null ? [latitude, longitude] : RECIFE;
    const map = L.map(containerRef.current!, { scrollWheelZoom: false }).setView(start, zoom);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap",
    }).addTo(map);
    map.on("click", (event: L.LeafletMouseEvent) =>
      pickRef.current?.(round(event.latlng.lat), round(event.latlng.lng)),
    );
    mapRef.current = map;
    const timer = window.setTimeout(() => map.invalidateSize(), 250);
    return () => {
      window.clearTimeout(timer);
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (latitude == null || longitude == null || Number.isNaN(latitude) || Number.isNaN(longitude)) {
      markerRef.current?.remove();
      markerRef.current = null;
      return;
    }
    const position = L.latLng(latitude, longitude);
    if (markerRef.current) markerRef.current.setLatLng(position);
    else
      markerRef.current = L.circleMarker(position, {
        radius: 9,
        color: "#0B5D3B",
        weight: 3,
        fillColor: "#F2B705",
        fillOpacity: 1,
      }).addTo(map);
    if (!map.getBounds().pad(-0.1).contains(position)) map.setView(position, Math.max(map.getZoom(), 15));
  }, [latitude, longitude]);

  // O Leaflet adiciona classes próprias ao contêiner; por isso as classes que
  // mudam com o estado ficam no elemento de fora, que o React controla.
  return (
    <div className={`map-picker${onPick ? "" : " read-only"}${invalid ? " invalid" : ""}`}>
      <div
        ref={containerRef}
        className="map-canvas"
        aria-label={onPick ? "Mapa para marcar o local de entrega" : "Local de entrega no mapa"}
      />
    </div>
  );
}
