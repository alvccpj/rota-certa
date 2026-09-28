import { type ReactNode, useCallback, useEffect, useState } from "react";

interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel: string;
}

interface Pending extends ConfirmOptions {
  resolve: (confirmed: boolean) => void;
}

/** Confirmação antes de ações que não podem ser desfeitas. */
export function useConfirm(): [ReactNode, (options: ConfirmOptions) => Promise<boolean>] {
  const [pending, setPending] = useState<Pending | null>(null);

  const confirm = useCallback(
    (options: ConfirmOptions) => new Promise<boolean>((resolve) => setPending({ ...options, resolve })),
    [],
  );

  const close = useCallback(
    (confirmed: boolean) => {
      pending?.resolve(confirmed);
      setPending(null);
    },
    [pending],
  );

  useEffect(() => {
    if (!pending) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && close(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [pending, close]);

  const dialog = pending ? (
    <div className="dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close(false)}>
      <div className="dialog" role="alertdialog" aria-modal="true" aria-labelledby="dialog-title" aria-describedby="dialog-text">
        <h2 id="dialog-title">{pending.title}</h2>
        <p id="dialog-text">{pending.message}</p>
        <div className="dialog-actions">
          <button type="button" className="button quiet" onClick={() => close(false)} autoFocus>
            Voltar
          </button>
          <button type="button" className="button danger-solid" onClick={() => close(true)}>
            {pending.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return [dialog, confirm];
}
