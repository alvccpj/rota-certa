interface Props {
  latitude: number;
  longitude: number;
  orderId: number;
}

export default function NavigationLink({ latitude, longitude, orderId }: Props) {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || Math.abs(latitude) > 90 || Math.abs(longitude) > 180) {
    return null;
  }
  const destination = encodeURIComponent(`${latitude},${longitude}`);
  return (
    <a
      className="navigation-link"
      href={`https://www.google.com/maps/dir/?api=1&destination=${destination}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Navegar até o pedido #${orderId} no Google Maps (abre em nova aba)`}
    >
      Navegar no Google Maps <span aria-hidden="true">↗</span>
    </a>
  );
}
