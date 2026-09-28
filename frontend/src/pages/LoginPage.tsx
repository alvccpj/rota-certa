import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { api, ApiError, type Session } from "../api";
import AuthShell from "../components/AuthShell";
import Field, { FormAlert } from "../components/Field";
import { useSession } from "../session";
import { check, collectErrors, type FieldErrors, focusFirstError } from "../validation";

const DEMO_ACCOUNTS = [
  { label: "Administrador", email: "admin@rotacerta.com.br" },
  { label: "Atendente", email: "atendente@rotacerta.com.br" },
  { label: "Entregador", email: "entregador@rotacerta.com.br" },
];
const DEMO_PASSWORD = "rotacerta123";

export default function LoginPage() {
  const { signIn } = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { from?: string; notice?: string } | null;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = collectErrors({
      email: check.email(email),
      password: check.required(password, "Informe a senha."),
    });
    setErrors(found);
    setFormError(null);
    if (Object.keys(found).length) {
      focusFirstError();
      return;
    }
    setBusy(true);
    try {
      const session = await api<Session>("/auth/login", { method: "POST", body: { email, password } });
      signIn(session);
      navigate(state?.from ?? "/", { replace: true });
    } catch (err) {
      const error = err as ApiError;
      setErrors(error.fields ?? {});
      setFormError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <form className="login-form" onSubmit={submit} noValidate>
        <h1>Entrar</h1>
        <p className="muted">Use o e-mail e a senha cadastrados pelo administrador.</p>
        {state?.notice && !formError && <p className="alert info">{state.notice}</p>}
        <FormAlert message={formError} />
        <Field label="E-mail" name="email" error={errors.email}>
          {(props) => (
            <input {...props} type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
          )}
        </Field>
        <Field label="Senha" name="password" error={errors.password}>
          {(props) => (
            <input
              {...props}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          )}
        </Field>
        <button type="submit" className="button primary wide" disabled={busy}>
          {busy ? "Entrando…" : "Entrar"}
        </button>
        <p className="switch">
          Ainda não usa o RotaCerta? <Link to="/cadastro">Cadastrar meu negócio</Link>
        </p>
      </form>

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
                setErrors({});
                setFormError(null);
              }}
            >
              {account.label}
            </button>
          ))}
        </div>
      </div>
    </AuthShell>
  );
}
