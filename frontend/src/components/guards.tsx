import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { homePath, landingPath } from "../access";
import type { Role } from "../api";
import ForbiddenPage from "../pages/ForbiddenPage";
import { useSession, useUser } from "../session";

/** Envia para o login quem ainda não entrou, guardando a página pedida. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useSession();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  return children;
}

/**
 * Login e cadastro não fazem sentido para quem já está logado. Ao entrar, este
 * redirecionamento acontece antes do navigate do formulário, por isso ele
 * mesmo devolve o usuário à página que pediu antes do login (Sprint 09, BUG-06).
 */
export function PublicOnly({ children }: { children: ReactNode }) {
  const { user } = useSession();
  const location = useLocation();
  if (user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={landingPath(user.role, from)} replace />;
  }
  return children;
}

export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const user = useUser();
  if (!roles.includes(user.role)) return <ForbiddenPage allowed={roles} />;
  return children;
}

export function HomeRedirect() {
  const user = useUser();
  return <Navigate to={homePath(user.role)} replace />;
}
