import { type ReactNode, useCallback, useEffect, useId, useRef, useState } from "react";

interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel: string;
  tone?: "primary" | "danger";
}

interface Pending extends ConfirmOptions {
  resolve: (confirmed: boolean) => void;
}

/** Confirmação de ações destrutivas ou em lote, com foco contido no diálogo. */
export function useConfirm(): [ReactNode, (options: ConfirmOptions) => Promise<boolean>] {
  const [pending, setPending] = useState<Pending | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const pendingRef = useRef<Pending | null>(null);
  const id = useId();

  const confirm = useCallback(
    (options: ConfirmOptions) => new Promise<boolean>((resolve) => {
      if (pendingRef.current) {
        resolve(false);
        return;
      }
      previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      const next = { ...options, resolve };
      pendingRef.current = next;
      setPending(next);
    }),
    [],
  );

  const close = useCallback(
    (confirmed: boolean) => {
      pendingRef.current?.resolve(confirmed);
      pendingRef.current = null;
      setPending(null);
      previousFocus.current?.focus();
    },
    [],
  );

  useEffect(() => {
    if (!pending) return;
    dialogRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close(false);
      }
      if (event.key === "Tab") {
        const buttons = dialogRef.current?.querySelectorAll<HTMLButtonElement>("button");
        if (!buttons?.length) return;
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (!dialogRef.current?.contains(document.activeElement) || (event.shiftKey ? document.activeElement === first : document.activeElement === last)) {
          event.preventDefault();
          (event.shiftKey ? last : first).focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [pending, close]);

  useEffect(() => () => {
    pendingRef.current?.resolve(false);
    pendingRef.current = null;
  }, []);

  const dialog = pending ? (
    <div className="dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close(false)}>
      <div ref={dialogRef} className="dialog" role="alertdialog" aria-modal="true" aria-labelledby={`${id}-title`} aria-describedby={`${id}-text`}>
        <h2 id={`${id}-title`}>{pending.title}</h2>
        <p id={`${id}-text`}>{pending.message}</p>
        <div className="dialog-actions">
          <button type="button" className="button quiet" onClick={() => close(false)} autoFocus>
            Voltar
          </button>
          <button type="button" className={`button ${pending.tone === "primary" ? "primary" : "danger-solid"}`} onClick={() => close(true)}>
            {pending.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return [dialog, confirm];
}
