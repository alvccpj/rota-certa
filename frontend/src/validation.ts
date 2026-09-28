/** Validações dos formulários, com as mesmas regras aplicadas pela API. */

export type FieldErrors = Record<string, string>;

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function onlyDigits(value: string): string {
  return value.replace(/\D/g, "");
}

/** Formata o telefone como (81) 98800-1001 quando os dígitos estão completos. */
export function formatPhone(value: string): string {
  let digits = onlyDigits(value);
  if (digits.length >= 12 && digits.startsWith("55")) digits = digits.slice(2);
  if (digits.length === 11) return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  if (digits.length === 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return value;
}

/** Aceita vírgula ou ponto como separador decimal. */
export function parseDecimal(value: string): number | null {
  const text = value.trim().replace(",", ".");
  if (!text) return null;
  const number = Number(text);
  return Number.isFinite(number) ? number : null;
}

export const check = {
  required(value: string, message: string): string | null {
    return value.trim() ? null : message;
  },

  personName(value: string, emptyMessage = "Informe o nome."): string | null {
    if (!value.trim()) return emptyMessage;
    const letters = value.match(/\p{L}/gu)?.length ?? 0;
    return letters >= 2 ? null : "Use pelo menos duas letras.";
  },

  email(value: string): string | null {
    if (!value.trim()) return "Informe o e-mail.";
    return EMAIL.test(value.trim()) ? null : "Informe um e-mail válido, como nome@empresa.com.br.";
  },

  phone(value: string, required = false): string | null {
    if (!value.trim()) return required ? "Informe o telefone." : null;
    let digits = onlyDigits(value);
    if (digits.length >= 12 && digits.startsWith("55")) digits = digits.slice(2);
    if ((digits.length === 10 || digits.length === 11) && digits[0] !== "0") return null;
    return "Informe o telefone com DDD, por exemplo (81) 98800-1001.";
  },

  password(value: string, required = true): string | null {
    if (!value) return required ? "Crie uma senha." : null;
    if (value.length < 8) return "Use pelo menos 8 caracteres.";
    if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) return "A senha precisa ter letras e números.";
    return null;
  },

  number(value: string, options: { label: string; min?: number; max?: number; required?: boolean }): string | null {
    const number = parseDecimal(value);
    if (number === null) return value.trim() ? "Informe um número." : options.required === false ? null : `Informe ${options.label}.`;
    if (options.min !== undefined && number <= options.min) return `Informe um valor maior que ${options.min}.`;
    if (options.max !== undefined && number > options.max) return `O valor máximo é ${options.max}.`;
    return null;
  },
};

/** Junta os resultados das validações, descartando os campos sem erro. */
export function collectErrors(entries: Record<string, string | null>): FieldErrors {
  const errors: FieldErrors = {};
  for (const [field, message] of Object.entries(entries)) {
    if (message) errors[field] = message;
  }
  return errors;
}

export function summarize(errors: FieldErrors): string {
  const count = Object.keys(errors).length;
  return count === 1 ? "Corrija o campo destacado para continuar." : `Corrija os ${count} campos destacados para continuar.`;
}

/** Leva o foco ao primeiro campo com erro depois que a tela for atualizada. */
export function focusFirstError(): void {
  window.requestAnimationFrame(() => {
    document.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
  });
}
