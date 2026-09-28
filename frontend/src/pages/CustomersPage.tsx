import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { api, type Customer } from "../api";
import { useConfirm } from "../components/ConfirmDialog";
import { useToast } from "../components/Toast";
import { useUser } from "../session";

export default function CustomersPage() {
  const user = useUser();
  const notify = useToast();
  const [dialog, confirm] = useConfirm();
  const [params, setParams] = useSearchParams();
  const search = params.get("busca") ?? "";
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setCustomers(await api<Customer[]>("/customers"));
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(customer: Customer) {
    const confirmed = await confirm({
      title: `Excluir ${customer.full_name}?`,
      message: "O cadastro será apagado definitivamente. Clientes com pedidos não podem ser excluídos.",
      confirmLabel: "Excluir cliente",
    });
    if (!confirmed) return;
    try {
      await api(`/customers/${customer.id}`, { method: "DELETE" });
      notify(`${customer.full_name} foi excluído.`);
      load();
    } catch (err) {
      notify((err as Error).message, "error");
    }
  }

  const term = search.trim().toLocaleLowerCase("pt-BR");
  const visible = customers.filter((customer) =>
    `${customer.full_name} ${customer.phone ?? ""}`.toLocaleLowerCase("pt-BR").includes(term),
  );

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Clientes</h1>
          <p className="muted">Quem recebe as entregas. O último endereço usado aparece ao cadastrar um novo pedido.</p>
        </div>
        <Link className="button primary" to="/clientes/novo">
          Novo cliente
        </Link>
      </div>

      <label className="search">
        <span className="sr-only">Buscar clientes</span>
        <input
          type="search"
          placeholder="Buscar por nome ou telefone"
          value={search}
          onChange={(e) => setParams(e.target.value ? { busca: e.target.value } : {}, { replace: true })}
        />
      </label>

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="muted">Carregando clientes…</p>
      ) : visible.length === 0 ? (
        <div className="empty">
          <p>{customers.length === 0 ? "Nenhum cliente cadastrado ainda." : "Nenhum cliente encontrado com essa busca."}</p>
          {customers.length === 0 && (
            <Link className="button primary" to="/clientes/novo">
              Cadastrar o primeiro cliente
            </Link>
          )}
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Nome</th>
                <th scope="col">Telefone</th>
                <th scope="col">Pedidos</th>
                <th scope="col">Último endereço de entrega</th>
                <th scope="col">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((customer) => (
                <tr key={customer.id}>
                  <td>
                    <strong>{customer.full_name}</strong>
                  </td>
                  <td className="nowrap">{customer.phone ?? <span className="muted">Sem telefone</span>}</td>
                  <td>
                    {customer.order_count > 0 ? (
                      <Link to={`/pedidos?busca=${encodeURIComponent(customer.full_name)}`}>
                        {customer.order_count} {customer.order_count === 1 ? "pedido" : "pedidos"}
                      </Link>
                    ) : (
                      <span className="muted">Nenhum</span>
                    )}
                  </td>
                  <td>{customer.last_address ?? <span className="muted">Ainda sem entregas</span>}</td>
                  <td className="row-actions">
                    <Link className="button quiet small" to={`/pedidos/novo?cliente=${customer.id}`}>
                      Novo pedido
                    </Link>
                    <Link className="button quiet small" to={`/clientes/${customer.id}/editar`}>
                      Editar
                    </Link>
                    {user.role === "ADMIN" && (
                      <button type="button" className="button danger small" onClick={() => remove(customer)}>
                        Excluir
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {dialog}
    </section>
  );
}
