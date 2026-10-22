# Sprint 07 — Sistema quase completo

**Projeto:** Rota Certa  
**Grupo:** 04  
**Prazo:** 24/10/2026 às 23h59

Este registro descreve a evolução prática da Sprint 07 e serve de fonte para o documento cumulativo das Sprints 01 a 07. Os recursos abaixo estão implementados, integrados ao banco e cobertos por validação automatizada e manual.

## 1. Resultado da Sprint

| Entrega obrigatória | Implementação | Situação |
|---|---|---|
| Dashboard | Painel operacional com indicadores reais de pedidos, rotas, entregadores, distância e desempenho, filtráveis por período. | Concluída |
| Relatórios | Tela dedicada que cruza pedidos, clientes, entregadores e rotas. | Concluída |
| Pesquisas | Busca por número do pedido, cliente, telefone, endereço ou entregador. | Concluída |
| Filtros | Período, situação, entregador e prioridade no relatório; período, tipo e situação no histórico. | Concluída |
| Exportação | CSV em UTF-8 com exatamente os registros retornados pelos filtros aplicados. | Concluída |
| Logs ou histórico | Linha do tempo persistida com mudanças de situação dos pedidos e execuções do otimizador. | Concluída |
| Integração | Navegação e dados conectados aos módulos de pedidos, clientes, usuários, rotas e desempenho. | Concluída |

## 2. Dashboard funcional

O dashboard da rota `/painel` continua sendo a entrada dos perfis Administrador e Atendente. Seus indicadores são calculados pela API com dados persistidos do estabelecimento autenticado:

- pedidos totais e distribuição por situação;
- taxa de conclusão;
- rotas planejadas, em andamento e concluídas;
- distância total planejada;
- disponibilidade dos entregadores;
- quantidade e tempo médio das execuções do otimizador;
- alertas operacionais e pedidos recentes.

O período é selecionável e o painel oferece acesso direto a pedidos, roteirização, relatórios, histórico e comparação de desempenho.

## 3. Relatórios, pesquisas e filtros

A tela `/relatorios` consulta `GET /dashboard/report` e apresenta uma visão consolidada de cada pedido. A pesquisa livre considera número, cliente, telefone, endereço e entregador. Os filtros podem ser combinados:

- data inicial e final;
- situação do pedido;
- entregador atribuído;
- prioridade.

O resultado apresenta contadores de pedidos, peso total, pedidos com rota e entregas concluídas. Cada registro mantém acesso ao detalhe do pedido, demonstrando a integração com o CRUD e o histórico individual.

## 4. Exportação CSV

A exportação é aplicável ao Rota Certa porque pequenos negócios precisam compartilhar e arquivar listagens operacionais. O botão **Exportar CSV** gera um arquivo com os registros atualmente filtrados e inclui pedido, cliente, entregador, endereço, situação, prioridade, peso, data de cadastro e dados da rota.

O arquivo usa ponto e vírgula e marcador UTF-8 para abrir corretamente em planilhas configuradas em português. Nenhum dado paralelo ou simulado é montado somente para o arquivo: a exportação utiliza a mesma resposta da API exibida na tabela.

## 5. Histórico operacional

A tela `/historico` reúne duas fontes persistidas em ordem cronológica:

1. alterações de situação dos pedidos, armazenadas em `order_status_history`, com responsável e observação;
2. execuções sequenciais, paralelas ou em GPU do otimizador, armazenadas em `optimization_runs`, com modo, quantidade de pedidos e tempo.

O histórico permite pesquisa e filtros por período, tipo de operação e situação do pedido. Administradores e atendentes podem consultar até 500 eventos recentes do estabelecimento; entregadores não possuem acesso ao painel gerencial.

## 6. Integração com os módulos anteriores

```text
Cliente → Pedido → Entregador → Rota → Entrega
               ↘           ↘       ↙
                   Dashboard
                       ↓
           Relatórios, CSV e histórico
```

- O cadastro de clientes e o CRUD de pedidos fornecem os dados pesquisáveis.
- A atribuição de entregadores alimenta os filtros e o relatório.
- A geração de rotas associa cada pedido ao planejamento e registra a execução do otimizador.
- A atualização da entrega grava novos eventos, refletidos no dashboard e no histórico.
- O controle de perfis restringe todas as consultas ao estabelecimento e aos papéis autorizados.

## 7. Estrutura técnica

### Backend

- `GET /dashboard/summary`: indicadores do dashboard.
- `GET /dashboard/report`: relatório com pesquisa e filtros combináveis.
- `GET /dashboard/history`: histórico consolidado de pedidos e otimização.
- `backend/app/reporting.py`: consultas e agregações isoladas da camada HTTP.
- limite de 366 dias por consulta e 2.000 registros no relatório;
- isolamento por `establishment_id` e autorização para Administrador e Atendente.

### Frontend

- `/painel`: acompanhamento operacional;
- `/relatorios`: consulta, filtros, resumo e exportação;
- `/historico`: linha do tempo pesquisável;
- menu e atalhos atualizados para conectar os três recursos;
- layouts responsivos e estados de carregamento, erro e ausência de resultados.

## 8. Validações realizadas

- **93 testes aprovados** no backend e **1 ignorado** por depender de uma GPU NVIDIA com CUDA indisponível na máquina de validação.
- Build de produção do frontend concluído com TypeScript e Vite.
- Auditoria npm concluída com **zero vulnerabilidades**.
- Testes específicos confirmam filtros por pesquisa, entregador, prioridade e situação.
- Testes específicos confirmam a união do histórico de pedidos com execuções do otimizador e as restrições de perfil.
- Fluxo manual validado no navegador com a base local persistida.

## 9. Evidências

As imagens ficam em `docs/sprint-07/assets` e os resultados textuais em `docs/sprint-07/evidencias`. O PDF cumulativo inclui:

- dashboard carregado com dados reais;
- relatório completo;
- pesquisa e filtros aplicados;
- confirmação da exportação CSV;
- histórico operacional com pedidos e otimização;
- resultados de testes, build e auditoria;
- link do repositório atualizado.

## 10. Dificuldades encontradas

- Preservar uma consulta eficiente ao combinar filtros de várias entidades sem duplicar pedidos ligados a rotas.
- Consolidar eventos com estruturas diferentes em uma única linha do tempo ordenada.
- Garantir que o arquivo exportado corresponda exatamente ao resultado filtrado e mantenha acentuação compatível com planilhas.
- Manter a navegação legível após incluir novas áreas administrativas, especialmente em telas pequenas.

## 11. Próximos passos

- Ampliar os testes de interface de ponta a ponta para todos os filtros.
- Avaliar paginação no servidor quando a operação ultrapassar os limites atuais.
- Acrescentar exportação em PDF somente se houver necessidade real de um documento fechado para impressão.
- Executar ensaios com maior volume de dados e com GPU CUDA disponível.
- Preparar a revisão final de acessibilidade, segurança e apresentação do produto.

## 12. Repositório

Repositório oficial: <https://github.com/alvccpj/rota-certa>

Branch de desenvolvimento desta entrega: `sprint/07-sistema-quase-completo`.
