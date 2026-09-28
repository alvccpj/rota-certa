import { type ReactNode, createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import { api, configureApi, type Session, type User } from "./api";

const STORAGE_KEY = "rotacerta.session";

function readStoredSession(): Session | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

function storeSession(session: Session | null) {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Sem armazenamento local a sessão dura até recarregar a página.
  }
}

interface SessionValue {
  user: User | null;
  signIn: (session: Session) => void;
  signOut: (notice?: string) => void;
  updateUser: (user: User) => void;
}

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(readStoredSession);

  const signOut = useCallback(
    (notice?: string) => {
      storeSession(null);
      configureApi(null, () => {});
      setSession(null);
      navigate("/login", { replace: true, state: notice ? { notice } : undefined });
    },
    [navigate],
  );

  const signIn = useCallback((next: Session) => {
    storeSession(next);
    setSession(next);
  }, []);

  const updateUser = useCallback((user: User) => {
    setSession((current) => {
      if (!current) return current;
      const next = { ...current, user };
      storeSession(next);
      return next;
    });
  }, []);

  configureApi(session?.access_token ?? null, () => signOut("Sua sessão expirou. Entre novamente para continuar."));

  useEffect(() => {
    if (!session) return;
    // Confirma o token salvo e atualiza o perfil caso o administrador o tenha alterado.
    api<User>("/auth/me").then(updateUser).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token]);

  const value = useMemo(
    () => ({ user: session?.user ?? null, signIn, signOut, updateUser }),
    [session, signIn, signOut, updateUser],
  );
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession precisa estar dentro de SessionProvider");
  return context;
}

/** Usuário logado; só deve ser usado em páginas protegidas por RequireAuth. */
export function useUser(): User {
  const { user } = useSession();
  if (!user) throw new Error("Página protegida acessada sem sessão");
  return user;
}
