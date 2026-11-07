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
  signOut: (notice?: string, from?: string) => void;
  updateUser: (user: User) => void;
  /** Aviso para a tela de login, como o de sessão expirada. */
  notice: string | null;
}

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(readStoredSession);
  // O aviso fica no contexto, e não no state da navegação: ao zerar a sessão o
  // RequireAuth também redireciona e substituía esse state (Sprint 09, BUG-08).
  const [notice, setNotice] = useState<string | null>(null);

  const signOut = useCallback(
    (message?: string, from?: string) => {
      storeSession(null);
      configureApi(null, () => {});
      setNotice(message ?? null);
      setSession(null);
      navigate("/login", { replace: true, state: from ? { from } : undefined });
    },
    [navigate],
  );

  const signIn = useCallback((next: Session) => {
    storeSession(next);
    setNotice(null);
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

  // A página atual é guardada para o usuário voltar a ela depois de entrar de novo.
  configureApi(session?.access_token ?? null, () =>
    signOut("Sua sessão expirou. Entre novamente para continuar.", window.location.pathname + window.location.search),
  );

  useEffect(() => {
    if (!session) return;
    // Confirma o token salvo e atualiza o perfil caso o administrador o tenha alterado.
    api<User>("/auth/me").then(updateUser).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token]);

  const value = useMemo(
    () => ({ user: session?.user ?? null, signIn, signOut, updateUser, notice }),
    [session, signIn, signOut, updateUser, notice],
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
