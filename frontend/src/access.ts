import type { Role } from "./api";

/** Página inicial de cada perfil. */
export function homePath(role: Role): string {
  return role === "COURIER" ? "/entregas" : "/painel";
}

/**
 * Espelha as restrições de RequireRole em App.tsx. Usado para decidir se a
 * página pedida antes do login pode ser reaberta com o perfil que entrou.
 */
export function canAccess(role: Role, path: string): boolean {
  const pathname = path.split(/[?#]/)[0].replace(/\/+$/, "") || "/";
  if (role === "COURIER") return pathname === "/entregas" || /^\/pedidos\/\d+$/.test(pathname);
  if (pathname === "/entregas") return false;
  if (role !== "ADMIN" && /^\/(desempenho|usuarios)(\/|$)/.test(pathname)) return false;
  return true;
}

/** Destino depois do login: a página pedida, se for interna e permitida; senão, o início do perfil. */
export function landingPath(role: Role, from?: string | null): string {
  const internal = typeof from === "string" && from.startsWith("/") && !from.startsWith("//");
  if (!internal || from === "/" || /^\/(login|cadastro)(\/|\?|$)/.test(from)) return homePath(role);
  return canAccess(role, from) ? from : homePath(role);
}
