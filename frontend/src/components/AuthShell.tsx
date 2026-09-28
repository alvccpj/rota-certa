import type { ReactNode } from "react";

/** Moldura das telas de login e cadastro, com o painel em forma de placa. */
export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="login">
      <section className="login-sign" aria-hidden="true">
        <div className="sign-plate">
          <p className="sign-title">RotaCerta</p>
          <p className="sign-text">Pedidos, entregadores e rotas do dia em um só lugar.</p>
        </div>
        <svg className="sign-route" viewBox="0 0 420 220" preserveAspectRatio="xMidYMid meet">
          <path
            d="M20 190 C 90 190, 90 120, 160 120 S 240 40, 300 60 S 380 150, 400 40"
            fill="none"
            stroke="rgba(255,255,255,0.9)"
            strokeWidth="4"
            strokeDasharray="10 9"
            strokeLinecap="round"
          />
          <circle cx="20" cy="190" r="10" fill="#F2B705" />
          <circle cx="160" cy="120" r="8" fill="#fff" />
          <circle cx="300" cy="60" r="8" fill="#fff" />
          <circle cx="400" cy="40" r="8" fill="#fff" />
        </svg>
      </section>
      <section className="login-panel">{children}</section>
    </div>
  );
}
