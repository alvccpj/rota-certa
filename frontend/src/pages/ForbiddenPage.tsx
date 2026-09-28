import { Link } from "react-router";
import type { Role } from "../api";

const ROLE_PLURALS: Record<Role, string> = {
  ADMIN: "administradores",
  ATTENDANT: "atendentes",
  COURIER: "entregadores",
};

export default function ForbiddenPage({ allowed }: { allowed: Role[] }) {
  const names = allowed.map((role) => ROLE_PLURALS[role]);
  const who = names.length > 1 ? `${names.slice(0, -1).join(", ")} e ${names.at(-1)}` : names[0];
  return (
    <section className="page state-page">
      <p className="state-code">Acesso negado</p>
      <h1>Esta página não está disponível para o seu perfil</h1>
      <p className="muted">
        Ela é usada apenas por {who}. Se você precisa dela, peça ao administrador para revisar o seu perfil.
      </p>
      <Link className="button primary" to="/">
        Voltar para o início
      </Link>
    </section>
  );
}
