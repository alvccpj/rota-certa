export default function RouteMark({ size = 34 }: { size?: number }) {
  return (
    <svg className="route-mark" width={size} height={size} viewBox="0 0 34 34" aria-hidden="true">
      <rect width="34" height="34" rx="7" fill="#0B5D3B" />
      <path d="M9 25c0-6 16-4 16-11 0-3-2-5-5-5" fill="none" stroke="#fff" strokeWidth="2.4" strokeDasharray="3.2 2.6" />
      <circle cx="9" cy="25" r="3.2" fill="#F2B705" />
      <circle cx="20" cy="9" r="3.2" fill="#fff" />
    </svg>
  );
}
