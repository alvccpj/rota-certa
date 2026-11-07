# Checklist de revisão da Sprint 09

Revisão em 07/11/2026. Grupo 04 - RotaCerta.

- [x] Testes funcionais: 22 casos cobrindo autenticação, clientes, pedidos, usuários, atribuição, rotas (sequencial e GPU), entrega, painel, relatórios, histórico e desempenho.
- [x] Testes de validação: 20 casos com campos obrigatórios, formatos, limites, regras de negócio e entradas diretas na API.
- [x] Testes de navegação: 19 casos com redirecionamentos, menus por perfil, permissões, isolamento, páginas inexistentes, celular e sessão expirada.
- [x] Execução oficial em base limpa no PostgreSQL 18.1: 61 de 61 casos aprovados, com procedimento, esperado e obtido em `evidencias/casos_de_teste.json`.
- [x] 9 bugs registrados com causa, correção e teste de regressão; todos corrigidos.
- [x] Suíte do backend nos dois bancos: 150 de 150 em SQLite e 150 de 150 em PostgreSQL.
- [x] Frontend: 50 de 50 testes; build de produção concluído; auditoria npm sem vulnerabilidades.
- [x] Arquitetura e modelo de dados atualizados; README, COMO-RODAR e database/README revisados.
- [x] PDF cumulativo das Sprints 01 a 09 gerado (`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_09.pdf`).

## Antes do envio

- [ ] Push da branch `sprint/09-testes-validacao` e abertura do pull request.
- [ ] Revisão do PDF pela equipe e merge do pull request.
- [ ] Envio do PDF no Teams pelo Scrum Master.
- [ ] Ensaio da demonstração: `tools/run_test_environment.py` e `tools/documentation/capture_sprint09_evidence.py` (cerca de 4 minutos).
