import { type FormEvent, useState } from "react";
import { api, type Session } from "../api";

const DEMO_ACCOUNTS = [
  { label: "Administrador", email: "admin@rotacerta.com.br" },
  { label: "Atendente", email: "atendente@rotacerta.com.br" },
  { label: "Entregador", email: "entregador@rotacerta.com.br" },
];
const DEMO_PASSWORD = "rotacerta123";

interface Props {
  onSignedIn: (session: Session) => void;
  notice: string | null;
}

export default function LoginPage({ onSignedIn, notice }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState({
    establishment_name: "",
    depot_address: "",
    full_name: "",
    email: "",
    password: "",
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session =
        mode === "login"
          ? await api<Session>("/auth/login", { method: "POST", body: { email, password } })
          : await api<Session>("/auth/register", { method: "POST", body: register });
      onSignedIn(session);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function switchMode(next: "login" | "register") {
    setMode(next);
    setError(null);
  }

  const field = (key: keyof typeof register) => ({
    value: register[key],
    onChange: (e: { target: { value: string } }) => setRegister({ ...register, [key]: e.target.value }),
  });

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

      <section className="login-panel">
        <form className="login-form" onSubmit={submit} noValidate>
          <h1>{mode === "login" ? "Entrar" : "Cadastrar meu negócio"}</h1>
          <p className="muted">
            {mode === "login"
              ? "Use o e-mail e a senha cadastrados pelo administrador."
              : "Você será o administrador e poderá cadastrar atendentes e entregadores."}
          </p>

          {notice && mode === "login" && <p className="alert info">{notice}</p>}
          {error && (
            <p className="alert error" role="alert">
              {error}
            </p>
          )}

          {mode === "login" ? (
            <>
              <label>
                E-mail
                <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </label>
              <label>
                Senha
                <input
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </label>
            </>
          ) : (
            <>
              <label>
                Nome do negócio
                <input {...field("establishment_name")} placeholder="Ex.: Mercadinho São José" required />
              </label>
              <label>
                Endereço de saída das entregas
                <input {...field("depot_address")} placeholder="Rua, número, bairro e cidade" required />
              </label>
              <label>
                Seu nome
                <input {...field("full_name")} autoComplete="name" required />
              </label>
              <label>
                E-mail
                <input type="email" {...field("email")} autoComplete="email" required />
              </label>
              <label>
                Senha
                <input type="password" {...field("password")} autoComplete="new-password" required />
                <small>Mínimo de 8 caracteres.</small>
              </label>
            </>
          )}

          <button type="submit" className="button primary wide" disabled={busy}>
            {busy ? "Aguarde…" : mode === "login" ? "Entrar" : "Criar conta"}
          </button>

          <p className="switch">
            {mode === "login" ? (
              <>
                Ainda não usa o RotaCerta?{" "}
                <button type="button" className="link" onClick={() => switchMode("register")}>
                  Cadastrar meu negócio
                </button>
              </>
            ) : (
              <>
                Já tem conta?{" "}
                <button type="button" className="link" onClick={() => switchMode("login")}>
                  Entrar
                </button>
              </>
            )}
          </p>
        </form>

        {mode === "login" && (
          <div className="demo">
            <p>Contas de demonstração, senha {DEMO_PASSWORD}</p>
            <div className="demo-buttons">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  className="button quiet"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(DEMO_PASSWORD);
                    setError(null);
                  }}
                >
                  {account.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
