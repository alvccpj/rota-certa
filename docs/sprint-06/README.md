# Sprint 06 — Aprimoramento do Sistema

**Projeto:** Rota Certa  
**Grupo:** 04  
**Prazo:** 17/10/2026 às 23h59

Este documento registra o escopo, a implementação e as evidências da Sprint 06. O conteúdo completo também integra o documento cumulativo das Sprints 01 a 06.

## 1. Diagnóstico do projeto antes da Sprint 06

| Exigência | Situação em 14/10/2026 | Ação necessária |
|---|---|---|
| Terceiro módulo | **Concluído.** O Painel operacional e relatórios consolida pedidos, entregadores, rotas e desempenho. | Evidências em `docs/sprint-06/assets`. |
| Integração entre módulos | **Concluída.** Pedidos alimentam as rotas; as rotas e execuções do otimizador aparecem nos indicadores e no relatório. | Validada pela API, pela interface e por testes automatizados. |
| Melhorias de interface | **Concluídas.** Foram criados indicadores, gráficos, alertas, filtros, ações rápidas e estados de carregamento/erro/vazio. | Evidências desktop e mobile. |
| Ajustes de navegação | **Concluídos.** A visão geral tornou-se a entrada dos perfis internos e o menu móvel passou a ser recolhível. | Fluxos entre painel, pedidos, rotas e desempenho validados. |
| Repositório atualizado | **Concluído na branch da Sprint 06.** O código, os testes, as evidências e a documentação estão organizados para revisão. | Abrir PR, revisar e integrar a Sprint 06 à branch principal. |
| Documento cumulativo | **Concluído.** O documento contém as Sprints 01 a 06. | PDF final disponível em `output/pdf`. |
| Participação da equipe | **Parcialmente comprovada.** O histórico registra contribuições próprias de William e Vinícius. | Os demais integrantes devem registrar suas contribuições reais em commits próprios, sem fabricar autoria. |

## 2. Validações técnicas realizadas

- O build de produção do frontend foi concluído com sucesso.
- A suíte combinada do backend apresentou **90 testes aprovados e 1 ignorado**. O teste ignorado depende de uma GPU CUDA, indisponível na máquina de validação.
- A execução paralela por CPU foi validada fora das restrições do ambiente isolado.
- O banco, autenticação, cadastro, perfis, CRUDs, rotas e métricas já possuem testes automatizados.
- O Vite foi atualizado para 7.3.7 e a dependência transitiva vulnerável foi corrigida. O `npm audit` terminou com **zero vulnerabilidades**.
- O Docker não está instalado na máquina de validação. O projeto também possui procedimento de execução local sem Docker, portanto isso não impede a demonstração.

## 3. Terceiro módulo implementado

### Painel operacional e relatórios

O terceiro módulo consolida informações dos módulos existentes em uma visão operacional única. A escolha está alinhada aos requisitos funcionais já planejados para painel administrativo e relatórios e evita criar uma funcionalidade desconectada do propósito do Rota Certa.

### Funcionalidades entregues

1. Exibir indicadores de pedidos por situação: pendentes, atribuídos, em rota, entregues e cancelados.
2. Exibir quantidade de entregadores ativos e a situação das rotas do período.
3. Apresentar indicadores de distância, entregas concluídas e execuções recentes do otimizador.
4. Permitir filtro por período.
5. Exibir atividades ou entregas recentes com acesso ao respectivo detalhe.
6. Disponibilizar ações rápidas para cadastrar pedido, montar rota e consultar desempenho.
7. Restringir os dados conforme o perfil autenticado.
8. Gerar um relatório operacional exportável, preferencialmente em CSV, a partir dos filtros selecionados.

### Integrações demonstráveis

```text
Clientes → Pedidos → Atribuição ao entregador → Roteirização
                                      ↓
                        Execução e conclusão da rota
                                      ↓
              Status das entregas + métricas de desempenho
                                      ↓
                       Painel operacional e relatório
```

O painel consulta dados persistidos por meio da API. As evidências foram produzidas com uma base SQLite local isolada, suportada oficialmente para desenvolvimento e testes; a execução padrão permanece preparada para PostgreSQL.

## 4. Estrutura técnica implementada

### Backend

- Rota de resumo operacional `GET /dashboard/summary`.
- Consulta de relatório `GET /dashboard/report`, reutilizando pedidos, entregadores, rotas e execuções do otimizador.
- Autenticação e autorização para administradores e atendentes.
- Lógica de agregação isolada em `backend/app/reporting.py`.
- Testes de permissões, filtros, período e consistência dos totais.

### Frontend

- Tela `/painel` para administradores e atendentes.
- Painel como página inicial dos perfis internos.
- Cartões de indicadores, filtros, atividades recentes, alertas e ações rápidas.
- Dados carregados da API com tratamento de carregamento, vazio e erro.
- Exportação do relatório em CSV.
- Área `/entregas` mantida como entrada principal do entregador.

### Interface e navegação

- “Visão geral” adicionada ao menu dos perfis internos.
- Menu revisado para telas menores, com navegação recolhível no celular.
- Títulos, filtros, botões e mensagens de retorno padronizados.
- Página ativa indicada visualmente na navegação.
- Rótulos e componentes novos revisados para uso por teclado.

## 5. Registro da execução

### Etapa 1 — Fechamento do escopo

- Confirmar o Painel operacional e relatórios como terceiro módulo.
- Converter cada observação e funcionalidade em tarefa verificável.

### Etapa 2 — Correções e dependências

- Atualizar Vite e a dependência vulnerável de forma controlada.
- Executar novamente auditoria, build e testes.

### Etapa 3 — Implementação do terceiro módulo

- Implementar consultas agregadas e relatório no backend.
- Implementar painel, filtros e exportação no frontend.
- Aplicar regras de acesso por perfil.

### Etapa 4 — Integração e experiência de uso

- Revisar o fluxo completo do cadastro do pedido até a exibição dos resultados no painel.
- Ajustar menu, página inicial, breadcrumbs e responsividade.
- Validar estados de carregamento, erro, ausência de dados e permissão negada.

### Etapa 5 — Qualidade e entrega

- Executar testes automatizados do backend.
- Executar build de produção e auditoria do frontend.
- Realizar demonstração manual com dados persistidos.
- Capturar evidências legíveis de todas as exigências.
- Atualizar o documento cumulativo e gerar o PDF das Sprints 01 a 06.
- Abrir PR, revisar e integrar a branch da Sprint 06.

## 6. Distribuição sugerida de trabalho

Esta divisão é uma sugestão e deve refletir contribuições reais de cada integrante.

| Integrante | Contribuição sugerida |
|---|---|
| Álvaro | Consultas e endpoints do painel, integração com o banco e revisão da arquitetura. |
| Arthur | Testes de integração, permissões, atualização segura das dependências e validação do backend. |
| Vinícius | Tela do painel, filtros, exportação, navegação e melhorias responsivas. |
| William | Validação dos fluxos completos, organização das evidências e atualização do documento cumulativo. |
| Guilherme | Desenvolvimento e validação do sistema. |

Cada integrante deve trabalhar em branch própria ou em uma branch de tarefa e realizar seus próprios commits identificados. Documentação, testes e evidências são contribuições válidas quando produzidas de fato pelo autor.

## 7. Evidências incluídas no PDF

- Painel com dados reais carregados do banco.
- Filtro por período alterando os resultados.
- Relatório gerado a partir dos dados persistidos.
- Fluxo integrado: pedido criado, incluído em rota, concluído e refletido no painel.
- Comparação ou registro das melhorias de interface e navegação.
- Evidência dos perfis e das restrições de acesso.
- Resultado dos testes automatizados e do build.
- Instruções atualizadas de execução local.
- Link do repositório e identificação do Grupo 04.

## 8. Situação dos critérios de conclusão

- Terceiro módulo funcional, persistente e integrado aos módulos anteriores: **concluído**.
- Melhorias de interface e navegação implementadas e demonstráveis: **concluído**.
- Fluxos principais aprovados nos testes automatizados e na validação manual: **concluído**.
- Código, testes e documentação registrados no repositório: **concluído na branch da Sprint 06**.
- PDF cumulativo das Sprints 01 a 06 revisado, legível e identificado como **Grupo 04 — Rota Certa**: **concluído**.

## 9. Decisão de escopo

O terceiro módulo definido para esta Sprint é o **Painel operacional e relatórios**, conforme os requisitos RF09 e RF10 já previstos no planejamento do projeto.

