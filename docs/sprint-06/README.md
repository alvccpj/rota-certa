# Sprint 06 — Aprimoramento do Sistema

**Projeto:** Rota Certa  
**Grupo:** 04  
**Prazo:** 17/10/2026 às 23h59

Este documento organiza a preparação da Sprint 06. Ele não substitui o documento cumulativo de entrega e não declara como concluídas funcionalidades que ainda serão implementadas.

## 1. Diagnóstico do projeto antes da Sprint 06

| Exigência | Situação em 14/10/2026 | Ação necessária |
|---|---|---|
| Correções da Pré-Banca | **Pendente de informação.** As observações da banca não estão registradas no repositório. | Registrar os comentários reais, implementar as correções e reunir evidências antes da entrega. |
| Terceiro módulo | **Não implementado.** O sistema possui o módulo de pedidos/entregas e o módulo de roteirização/desempenho. | Implementar o módulo proposto de **Painel operacional e relatórios**. |
| Integração entre módulos | **Base existente.** Pedidos alimentam as rotas; a conclusão de rotas altera entregas; execuções do otimizador geram métricas persistidas. | Expor os dados integrados no terceiro módulo e testar os fluxos completos. |
| Melhorias de interface | **Boa base visual e responsiva.** Há identidade visual consistente, estados de tela e visualização desktop/mobile. | Refinar navegação, tela inicial, responsividade do menu e consistência de feedbacks. |
| Ajustes de navegação | **Parcialmente atendido.** Existem rotas protegidas, controle por perfil, menu por função e breadcrumbs. | Criar uma entrada clara para a visão geral e revisar os fluxos entre painel, pedidos, rotas e desempenho. |
| Repositório atualizado | **Atendido até a Sprint 05.** As Sprints 03, 04 e 05 estão integradas à branch principal. | Desenvolver em branch própria, abrir PR, revisar e integrar a Sprint 06. |
| Documento cumulativo | **Atendido somente até a Sprint 05.** | Atualizar o documento para conter as Sprints 01 a 06 e gerar o PDF final. |
| Participação da equipe | **Risco identificado.** O histórico atual registra commits de Álvaro e Vinícius, mas não de Arthur e William. | Dividir tarefas reais e garantir que cada integrante registre sua própria contribuição, sem fabricar autoria. |

## 2. Validações técnicas realizadas

- O build de produção do frontend foi concluído com sucesso.
- A suíte do backend apresentou **76 testes aprovados e 1 ignorado**. O teste ignorado depende de uma GPU CUDA, indisponível na máquina de validação.
- A execução paralela por CPU foi validada fora das restrições do ambiente isolado.
- O banco, autenticação, cadastro, perfis, CRUDs, rotas e métricas já possuem testes automatizados.
- O frontend possui duas vulnerabilidades de severidade alta reportadas pelo `npm audit`, relacionadas à versão atual do Vite e a uma dependência transitiva. A atualização deve ser feita de forma controlada e seguida de novo build e testes.
- O Docker não está instalado na máquina de validação. O projeto também possui procedimento de execução local sem Docker, portanto isso não impede a demonstração.

## 3. Terceiro módulo proposto

### Painel operacional e relatórios

O terceiro módulo consolidará informações dos módulos existentes em uma visão operacional única. A escolha está alinhada aos requisitos funcionais já planejados para painel administrativo e relatórios e evita criar uma funcionalidade desconectada do propósito do Rota Certa.

### Funcionalidades mínimas

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

O painel deverá consultar dados reais do PostgreSQL por meio da API. Não serão utilizados números fixos ou apenas telas ilustrativas.

## 4. Escopo técnico planejado

### Backend

- Criar uma rota de resumo operacional, por exemplo `GET /dashboard/summary`.
- Criar consulta de relatório por período e filtros, reutilizando pedidos, entregadores, rotas e execuções do otimizador.
- Aplicar autenticação e autorização de perfis nas novas rotas.
- Manter a lógica de agregação em serviços separados dos controladores HTTP.
- Adicionar testes de permissões, filtros e consistência dos totais.

### Frontend

- Criar a tela `/painel` para administradores e atendentes.
- Transformar o painel na página inicial dos perfis internos.
- Criar cartões de indicadores, filtros, lista de atividades recentes e ações rápidas.
- Integrar os dados com a API e tratar carregamento, vazio e erro.
- Adicionar exportação do relatório.
- Manter a área `/entregas` como entrada principal do entregador.

### Interface e navegação

- Adicionar “Visão geral” ao menu dos perfis internos.
- Revisar o menu para telas menores e evitar excesso de opções na horizontal.
- Padronizar títulos, breadcrumbs, filtros, botões e mensagens de retorno.
- Garantir indicação clara da página ativa.
- Revisar foco, rótulos e navegação por teclado nos novos componentes.

## 5. Registro obrigatório da Pré-Banca

As observações abaixo deverão ser preenchidas exclusivamente com o retorno real da professora/banca.

| Observação recebida | Ação realizada | Situação | Evidência |
|---|---|---|---|
| Aguardando o registro dos comentários da Pré-Banca. | A definir após o recebimento. | Pendente | A definir |

Não devem ser inventadas correções apenas para completar o documento. Se alguma ação não puder ser concluída, o PDF deve informar a pendência, a justificativa e a medida prevista.

## 6. Plano de execução

### Etapa 1 — Fechamento do escopo

- Registrar as observações da Pré-Banca.
- Confirmar o Painel operacional e relatórios como terceiro módulo.
- Converter cada observação e funcionalidade em tarefa verificável.

### Etapa 2 — Correções e dependências

- Corrigir os itens apontados na Pré-Banca.
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

## 7. Distribuição sugerida de trabalho

Esta divisão é uma sugestão e deve refletir contribuições reais de cada integrante.

| Integrante | Contribuição sugerida |
|---|---|
| Álvaro | Consultas e endpoints do painel, integração com o banco e revisão da arquitetura. |
| Arthur | Testes de integração, permissões, atualização segura das dependências e validação do backend. |
| Vinícius | Tela do painel, filtros, exportação, navegação e melhorias responsivas. |
| William | Validação dos fluxos completos, registro das correções da Pré-Banca, evidências e atualização do documento cumulativo. |

Cada integrante deve trabalhar em branch própria ou em uma branch de tarefa e realizar seus próprios commits identificados. Documentação, testes e evidências são contribuições válidas quando produzidas de fato pelo autor.

## 8. Evidências que deverão entrar no PDF

- Tabela “observação da Pré-Banca × ação realizada × evidência”.
- Painel com dados reais carregados do banco.
- Filtro por período alterando os resultados.
- Relatório gerado a partir dos dados persistidos.
- Fluxo integrado: pedido criado, incluído em rota, concluído e refletido no painel.
- Comparação ou registro das melhorias de interface e navegação.
- Evidência dos perfis e das restrições de acesso.
- Resultado dos testes automatizados e do build.
- Instruções atualizadas de execução local.
- Link do repositório e identificação do Grupo 04.

## 9. Critérios de conclusão

A Sprint 06 somente poderá ser considerada concluída quando:

- as observações reais da Pré-Banca estiverem registradas e tratadas ou justificadas;
- o terceiro módulo estiver funcional, persistente e integrado aos módulos anteriores;
- as melhorias de interface e navegação estiverem implementadas e demonstráveis;
- os fluxos principais passarem nos testes automatizados e na validação manual;
- o repositório refletir contribuições reais da equipe;
- o PDF cumulativo das Sprints 01 a 06 estiver revisado, legível e identificado como **Grupo 04 — Rota Certa**.

## 10. Pendências para iniciar a implementação

1. Obter o texto ou uma transcrição fiel das observações da Pré-Banca.
2. Confirmar com a equipe que o terceiro módulo será o **Painel operacional e relatórios**.

