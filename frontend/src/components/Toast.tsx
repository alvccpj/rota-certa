import { type ReactNode, createContext, useCallback, useContext, useEffect, useState } from "react";

type Tone = "success" | "error";
type Notify = (message: string, tone?: Tone) => void;

const ToastContext = createContext<Notify>(() => {});

/** Aviso temporário que continua visível mesmo depois de mudar de página. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; tone: Tone; id: number } | null>(null);

  const notify = useCallback<Notify>((message, tone = "success") => {
    setToast({ message, tone, id: Date.now() });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), toast.tone === "error" ? 6000 : 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div className={`toast toast-${toast?.tone ?? "success"}`} role="status" aria-live="polite">
        {toast?.message}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): Notify {
  return useContext(ToastContext);
}
