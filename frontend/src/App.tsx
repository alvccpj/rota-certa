import { useCallback, useEffect, useState } from "react";
import { api, configureApi, type Session, type User } from "./api";
import RouteMark from "./components/RouteMark";
import { ROLE_LABELS } from "./labels";
import LoginPage from "./pages/LoginPage";
import OrdersPage from "./pages/OrdersPage";
import UsersPage from "./pages/UsersPage";

const STORAGE_KEY = "rotacerta.session";
type Page = "orders" | "users";

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

export default function App() {
  const [session, setSession] = useState<Session | null>(readStoredSession);
  const [page, setPage] = useState<Page>("orders");
  const [notice, setNotice] = useState<string | null>(null);

  const signOut = useCallback((message: string | null = null) => {
    storeSession(null);
    configureApi(null, () => {});
    setSession(null);
    setPage("orders");
    setNotice(message);
  }, []);

  const signIn = useCallback((next: Session) => {
    storeSession(next);
    setNotice(null);
    setSession(next);
  }, []);

  configureApi(session?.access_token ?? null, () => signOut("Sua sessão expirou. Entre novamente."));

  useEffect(() => {
    if (!session) return;
    // Confirma o token salvo e atualiza o perfil caso o administrador o tenha alterado.
    api<User>("/auth/me")
      .then((user) => {
        const refreshed = { ...session, user };
        storeSession(refreshed);
        setSession(refreshed);
      })
      .catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.access_token]);

  if (!session) return <LoginPage onSignedIn={signIn} notice={notice} />;

  const { user } = session;
  const isAdmin = user.role === "ADMIN";
  const current = isAdmin ? page : "orders";

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <RouteMark />
            <div>
              <strong>RotaCerta</strong>
              <span>{user.establishment.name}</span>
            </div>
          </div>
          <nav className="tabs" aria-label="Seções">
            <button
              type="button"
              className={current === "orders" ? "tab active" : "tab"}
              onClick={() => setPage("orders")}
            >
              {user.role === "COURIER" ? "Minhas entregas" : "Pedidos"}
            </button>
            {isAdmin && (
              <button
                type="button"
                className={current === "users" ? "tab active" : "tab"}
                onClick={() => setPage("users")}
              >
                Usuários
              </button>
            )}
          </nav>
          <div className="account">
            <div className="account-name">
              <strong>{user.full_name}</strong>
              <span className={`role role-${user.role.toLowerCase()}`}>{ROLE_LABELS[user.role]}</span>
            </div>
            <button type="button" className="button ghost-dark" onClick={() => signOut()}>
              Sair
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        {current === "orders" ? <OrdersPage user={user} /> : <UsersPage currentUser={user} />}
      </main>
    </div>
  );
}
