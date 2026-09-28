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
