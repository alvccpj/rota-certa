import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router";
import { ROLE_LABELS } from "../labels";
import { useSession, useUser } from "../session";
import ErrorBoundary from "./ErrorBoundary";
import RouteMark from "./RouteMark";

export default function Layout() {
  const user = useUser();
  const { signOut } = useSession();
  const location = useLocation();
  const staff = user.role !== "COURIER";
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => setMenuOpen(false), [location.pathname]);

  const links = [
    staff && { to: "/painel", label: "Visão geral" },
    staff && { to: "/pedidos", label: "Pedidos" },
    staff && { to: "/rotas", label: "Rotas" },
    staff && { to: "/relatorios", label: "Relatórios" },
    staff && { to: "/historico", label: "Histórico" },
    !staff && { to: "/entregas", label: "Minhas entregas" },
    staff && { to: "/clientes", label: "Clientes" },
    user.role === "ADMIN" && { to: "/desempenho", label: "Desempenho" },
    user.role === "ADMIN" && { to: "/usuarios", label: "Usuários" },
  ].filter((link): link is { to: string; label: string } => Boolean(link));

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to="/" className="brand" aria-label="RotaCerta, página inicial">
            <RouteMark />
            <div>
              <strong>RotaCerta</strong>
              <span>{user.establishment.name}</span>
            </div>
          </NavLink>
          <button
            type="button"
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="main-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span aria-hidden="true">☰</span> Menu
          </button>
          <nav id="main-navigation" className={menuOpen ? "tabs open" : "tabs"} aria-label="Seções">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} className={({ isActive }) => (isActive ? "tab active" : "tab")}>
                {link.label}
              </NavLink>
            ))}
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
        <ErrorBoundary key={location.pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  );
}
