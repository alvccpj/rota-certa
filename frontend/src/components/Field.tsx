import type { ReactNode } from "react";

export interface ControlProps {
  id: string;
  name: string;
  "aria-invalid": boolean;
  "aria-describedby"?: string;
}

interface Props {
  label: string;
  name: string;
  error?: string;
  hint?: string;
  children: (props: ControlProps) => ReactNode;
}

/** Rótulo, controle e mensagem de erro ligados por id para leitores de tela. */
export default function Field({ label, name, error, hint, children }: Props) {
  const id = `campo-${name}`;
  const describedBy = error ? `${id}-erro` : hint ? `${id}-dica` : undefined;
  return (
    <div className={error ? "field has-error" : "field"}>
      <label htmlFor={id}>{label}</label>
      {children({ id, name, "aria-invalid": Boolean(error), "aria-describedby": describedBy })}
      {error ? (
        <p className="field-error" id={`${id}-erro`}>
          {error}
        </p>
      ) : (
        hint && <small id={`${id}-dica`}>{hint}</small>
      )}
    </div>
  );
}

export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="alert error" role="alert">
      {message}
    </p>
  );
}
