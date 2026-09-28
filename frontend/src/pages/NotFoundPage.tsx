import { Link, useLocation } from "react-router";

export default function NotFoundPage() {
  const { pathname } = useLocation();
  return (
    <section className="page state-page">
      <p className="state-code">Página não encontrada</p>
      <h1>Não existe nada em {pathname}</h1>
      <p className="muted">O endereço pode ter sido digitado errado ou o registro foi removido. Use o menu acima para continuar.</p>
      <Link className="button primary" to="/">
        Ir para o início
      </Link>
    </section>
  );
}
