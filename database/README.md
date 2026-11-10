# Banco de dados

O arquivo `schema.sql` contém a estrutura relacional do RotaCerta para PostgreSQL 16. Ele é aplicado de uma destas formas:

- **Docker Compose:** o serviço `db` executa o arquivo na primeira inicialização do volume.
- **Sem Docker:** a API executa o arquivo ao iniciar, quando encontra o banco sem a tabela `users`.

Depois do esquema, a API cadastra um estabelecimento de demonstração com usuários e pedidos, desde que o banco ainda não tenha nenhum estabelecimento (`SEED_DEMO_DATA=true`).

## Inicialização

1. Copie `.env.example` para `.env`.
2. Execute `docker compose up --build`.
3. Aguarde o health check do PostgreSQL.
4. Consulte `http://localhost:8000/health`: a resposta deve trazer `"database": "connected"`.

Para recomeçar do zero no Docker, remova o volume com `docker compose down -v`.

O esquema cobre estabelecimentos, usuários, entregadores, clientes, pedidos, histórico de situação dos pedidos, rotas, paradas e execuções de otimização. A tabela `optimization_runs` foi incluída para registrar a comparação sequencial e paralela solicitada na orientação da Sprint 01.

A tabela `order_status_history` foi adicionada na Sprint 04. Bancos criados antes dela recebem a tabela automaticamente quando a API inicia, sem perda de dados.

Na Sprint 05 as tabelas `routes`, `route_stops` e `optimization_runs` passaram a ser usadas pelo módulo de roteirização. A coluna `execution_mode` de `routes` e de `optimization_runs` aceita também `GPU`, e `optimization_runs` ganhou as colunas `purpose` (geração de rotas ou comparação), `input_source` (pedidos reais ou instância sintética), `run_group` (agrupa as execuções de uma mesma comparação), `speedup`, `efficiency` e `same_routes`. Bancos criados antes recebem essas alterações automaticamente quando a API inicia, sem perda de dados.

Na Sprint 08, `route_stops` ganhou a coluna `waiting_minutes`, com a espera prevista até o início da janela de entrega. Bancos existentes recebem a coluna automaticamente quando a API inicia.

Na Sprint 09 os dados de demonstração passaram a gravar as janelas de entrega em UTC. Antes, no SQLite do modo de demonstração, elas ficavam 3 horas antes do previsto (BUG-07). O modelo de dados atualizado está em [`docs/sprint-09/assets/mer_v09.png`](../docs/sprint-09/assets/mer_v09.png). A suíte de testes pode rodar no PostgreSQL com `TEST_DATABASE_URL` (veja `COMO-RODAR.md`).

## Estrutura final da Release Candidate

Na Sprint 10, versão `0.10.0-rc.1`, o DDL continua em `schema.sql`; não foi
necessária uma nova migração. As nove tabelas e suas colunas foram comparadas
com os modelos SQLAlchemy, e as chaves e restrições foram inspecionadas no
PostgreSQL real. O modelo da Sprint 09 permanece válido.

| Tabela | Finalidade e relacionamentos |
| --- | --- |
| establishments | Estabelecimento e ponto de saída; raiz do isolamento da operação. |
| users | Conta, perfil e hash da senha; FK para estabelecimento; e-mail único global. |
| couriers | Perfil de entregador, capacidade e disponibilidade; FK para estabelecimento e usuário; usuário único. |
| customers | Cliente do estabelecimento. |
| orders | Pedido com coordenadas, peso, prioridade, janela e situação; FKs para estabelecimento, cliente e entregador opcional. |
| order_status_history | Eventos do pedido com autor e horário; exclusão do pedido remove seus eventos. |
| routes | Rota do entregador e estabelecimento, data, situação, modo e métricas. |
| route_stops | Paradas da rota; pedido único e sequência única por rota; exclusão da rota remove as paradas. |
| optimization_runs | Execuções do otimizador por estabelecimento, com tempos, distância, speedup e eficiência. |

As PKs são `BIGSERIAL`; as referências são `BIGINT`. Coordenadas e pesos usam
`NUMERIC`; datas e eventos usam `TIMESTAMPTZ`, e a data operacional da rota usa
`DATE`. Há checks para situações, perfis, modos, peso/capacidade positivos,
prioridade, janela, espera e métricas não negativas. A API complementa o DDL:
confere pertencimento ao estabelecimento, transições de situação, raio e
capacidade ativa. Essas regras entre tabelas não são garantidas apenas pelas FKs.

A atribuição automática adquire `SELECT FOR UPDATE` no estabelecimento e,
depois, nos pedidos e entregadores envolvidos. Chamadas dessa operação para o
mesmo estabelecimento aguardam o commit anterior. A Sprint 10 verificou três
lotes com oito chamadas simultâneas, além da fila vazia. Esse ensaio cobre
atribuição automática contra atribuição automática; não é um teste de carga
completo nem de concorrência entre todos os tipos de escrita.

Evidências: [`banco_e_contrato.json`](../docs/sprint-10/evidencias/banco_e_contrato.json),
[`concorrencia.txt`](../docs/sprint-10/evidencias/concorrencia.txt) e
[`testes_backend_postgresql.txt`](../docs/sprint-10/evidencias/testes_backend_postgresql.txt).
Para repetir a inspeção, execute `tools/documentation/verify_release.py`
com `DATABASE_URL` apontando para o schema de testes. Ele consulta a estrutura,
procura referências órfãs e cruza os IDs e situações da API com o SQL em outra conexão.
