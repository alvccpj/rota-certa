import { useEffect } from "react";

/** Atualiza listas visíveis sem apagar filtros nem interromper a leitura. */
export default function AutoRefresh({ onRefresh, updatedAt }: {
  onRefresh: () => Promise<void>;
  updatedAt: Date | null;
}) {
  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === "visible") void onRefresh();
    };
    const timer = window.setInterval(refresh, 15000);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [onRefresh]);

  return <p className="inline-note">
    Atualização automática a cada 15 segundos enquanto esta aba estiver visível.
    {updatedAt && <> Última atualização: <time dateTime={updatedAt.toISOString()}>{updatedAt.toLocaleTimeString("pt-BR")}</time>.</>}
    {" "}<button type="button" className="link" onClick={() => void onRefresh()}>Atualizar agora</button>
  </p>;
}
