import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router";
import { api, ApiError, type Session } from "../api";
import AuthShell from "../components/AuthShell";
import Field, { FormAlert } from "../components/Field";
import { useToast } from "../components/Toast";
import { useSession } from "../session";
import { check, collectErrors, type FieldErrors, focusFirstError, summarize } from "../validation";

const EMPTY = { establishment_name: "", depot_address: "", full_name: "", email: "", password: "" };

export default function RegisterPage() {
  const { signIn } = useSession();
  const navigate = useNavigate();
  const notify = useToast();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const input = (key: keyof typeof EMPTY) => ({
    value: form[key],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [key]: e.target.value }),
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    const found = collectErrors({
      establishment_name: check.required(form.establishment_name, "Informe o nome do negócio."),
      depot_address:
        form.depot_address.trim().length >= 5 ? null : "Informe o endereço de onde saem as entregas, com rua e número.",
      full_name: check.personName(form.full_name, "Informe o seu nome."),
      email: check.email(form.email),
      password: check.password(form.password),
    });
    setErrors(found);
    setFormError(Object.keys(found).length ? summarize(found) : null);
    if (Object.keys(found).length) {
      focusFirstError();
      return;
    }
    setBusy(true);
    try {
      const session = await api<Session>("/auth/register", { method: "POST", body: form });
      signIn(session);
      notify(`${form.establishment_name} cadastrado. Você já pode cadastrar a sua equipe.`);
      navigate("/", { replace: true });
    } catch (err) {
      const error = err as ApiError;
      setErrors(error.fields);
      setFormError(error.message);
      focusFirstError();
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <form className="login-form" onSubmit={submit} noValidate>
        <h1>Cadastrar meu negócio</h1>
        <p className="muted">Você será o administrador e poderá cadastrar atendentes e entregadores.</p>
        <FormAlert message={formError} />
        <Field label="Nome do negócio" name="establishment_name" error={errors.establishment_name}>
          {(props) => <input {...props} {...input("establishment_name")} placeholder="Ex.: Mercadinho São José" />}
        </Field>
        <Field label="Endereço de saída das entregas" name="depot_address" error={errors.depot_address}>
          {(props) => <input {...props} {...input("depot_address")} placeholder="Rua, número, bairro e cidade" />}
        </Field>
        <Field label="Seu nome" name="full_name" error={errors.full_name}>
          {(props) => <input {...props} {...input("full_name")} autoComplete="name" />}
        </Field>
        <Field label="E-mail" name="email" error={errors.email}>
          {(props) => <input {...props} {...input("email")} type="email" autoComplete="email" />}
        </Field>
        <Field label="Senha" name="password" error={errors.password} hint="Mínimo de 8 caracteres, com letras e números.">
          {(props) => <input {...props} {...input("password")} type="password" autoComplete="new-password" />}
        </Field>
        <button type="submit" className="button primary wide" disabled={busy}>
          {busy ? "Criando conta…" : "Criar conta"}
        </button>
        <p className="switch">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </AuthShell>
  );
}
