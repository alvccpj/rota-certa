# Banco de dados

O arquivo `schema.sql` contém a estrutura relacional inicial do RotaCerta para PostgreSQL 16. O serviço `db` definido em `compose.yaml` executa esse arquivo automaticamente na primeira inicialização do volume.

## Inicialização

1. Copie `.env.example` para `.env`.
2. Execute `docker compose up --build`.
3. Aguarde o health check do PostgreSQL.
4. Consulte a API em `http://localhost:8000/health`.

O esquema cobre estabelecimentos, usuários, entregadores, clientes, pedidos, rotas, paradas e execuções de otimização. A tabela `optimization_runs` foi incluída para registrar a comparação sequencial e paralela solicitada na orientação da Sprint 01.
