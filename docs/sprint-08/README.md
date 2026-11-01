# Sprint 08 - Consolidação funcional

Projeto RotaCerta, Grupo 04, turma 8NA. Implementação e validação em 01/11/2026.
Repositório: https://github.com/alvccpj/rota-certa
Branch: `sprint/08-consolidacao-funcional`, baseada em `master` após o merge da Sprint 07 (PR #10).

## Funcionalidades concluídas e rastreabilidade

| Requisito original | Implementação na versão consolidada |
| --- | --- |
| RF01 Autenticação e perfis | Cadastro do negócio, login, senha Argon2, JWT e autorização consultada no banco a cada requisição. |
| RF02 Pedidos | Cadastro, consulta, edição e exclusão autorizada; cliente, endereço, posição, peso, prioridade e janela. |
| RF03 Entregadores | Cadastro, disponibilidade e carga ativa; bloqueio da redução de capacidade abaixo da carga. |
| RF04 Rotas otimizadas | Vizinho mais próximo e 2-opt; execução sequencial, paralela em CPU e opcional em GPU. |
| RF05 Atribuição | Manual e automática. A automática prioriza urgência e prazo, respeita capacidade, raio e disponibilidade. |
| RF06 Lista e mapa | Sequência de paradas, mapa, previsão de chegada, espera, atraso previsto e link para navegação externa. |
| RF07 Situação | Etapas autorizadas, início de rota, confirmação de entrega e cancelamento com justificativa. |
| RF08 Histórico | Eventos de pedidos com autor e horário, rotas e execuções do otimizador persistidas. |
| RF09 Relatórios | Consultas e CSV filtrados; comparação de tempo, distância, speedup e eficiência. |
| RF10 Painel | Indicadores e alertas calculados com os dados do estabelecimento. |

## Atribuição automática

`POST /orders/auto-assign` exige Administrador ou Atendente. Considera somente pedidos pendentes sem entregador do estabelecimento autenticado. Ordena prioridade (1 antes de 2 e 3), prazo final (ausente por último) e ID. Entre entregadores elegíveis, escolhe a menor carga ativa em kg, com desempate por ID. A carga do lote é somada antes da escolha seguinte.

O entregador precisa estar ativo, com perfil correto e disponível, sem rota em andamento ou pedido em rota. Pedidos vencidos, fora do raio ou sem capacidade disponível permanecem pendentes com motivo explícito. O histórico registra a atribuição e seu autor. Repetir a operação não redistribui pedidos já atribuídos. O botão informa que a ação abrange todos os pendentes, inclusive os ocultos pelos filtros, e exige confirmação.

No PostgreSQL a operação bloqueia a linha do estabelecimento e as linhas selecionadas dentro da transação para serializar chamadas automáticas. A demonstração SQLite não comprova concorrência PostgreSQL; os testes desta entrega validam as regras e persistência. Ensaios concorrentes entre atribuições manuais e automáticas ainda são recomendados antes de uso em produção.

## Horários e modelo de dados

O agendamento acrescenta espera quando a chegada calculada antecede o início da janela. Essa espera se propaga para as paradas seguintes e para a duração da rota. Quando a previsão ultrapassa o fim da janela, a interface mostra o atraso em minutos. As previsões são recalculadas ao iniciar a rota.

`route_stops.waiting_minutes` foi adicionado com valor padrão zero. A atualização é incremental, preserva registros anteriores e pode ser executada novamente. O modelo SQL foi atualizado para instalações novas. `desired_start`, `desired_end`, `delay_minutes` e `timing_status` da resposta são obtidos dos campos já existentes, sem duplicar os pedidos.

## Permissões

| Ação | Administrador | Atendente | Entregador |
| --- | --- | --- | --- |
| Gerir usuários e ponto de saída | Sim | Não | Não |
| Clientes e criação/edição de pedidos | Sim | Sim | Não |
| Excluir pedidos | Sim, com regras da rota | Não | Não |
| Atribuição automática e geração de rotas | Sim | Sim | Não |
| Painel, relatórios e histórico gerencial | Sim | Sim | Não |
| Benchmark de desempenho | Sim | Não | Não |
| Ver/atualizar entrega | Do estabelecimento | Do estabelecimento | Somente a própria |
| Dados de outro estabelecimento | Não | Não | Não |

As restrições são aplicadas na API e na interface. Sem autenticação a API retorna 401; perfil insuficiente retorna 403; IDs de recursos de outro estabelecimento ou entregador retornam 404. A desativação e a alteração de perfil têm efeito nas próximas requisições, inclusive com token emitido anteriormente.

## Regras corrigidas

- Entregador sem cadastro operacional associado não pode visualizar pedidos pendentes sem responsável.
- Não é permitido reduzir a capacidade de carga abaixo dos pedidos ativos.
- Após a saída, cliente, entregador, endereço, coordenadas e peso são protegidos para não mudar uma entrega em execução.
- Pedidos vinculados a rotas iniciadas ou encerradas não são reabertos sobrescrevendo a parada antiga. Para nova entrega, cadastra-se outro pedido; o histórico original é preservado.
- Alterar a janela de um pedido planejado invalida a rota para recalcular os horários.
- Datas recebidas com fusos diferentes são normalizadas para UTC antes de persistir. Representações equivalentes mantêm a mesma previsão e não invalidam o plano.
- Alterar o ponto de saída é bloqueado durante rotas em andamento; em rotas planejadas, exige nova geração.
- A geração e o início verificam acesso ativo do entregador e capacidade. A geração revalida o raio.
- Regenerar rotas preserva os planos dos entregadores que ficaram fora da operação.
- CSV neutraliza texto que poderia ser interpretado como fórmula em planilhas.

## Usabilidade

Confirmação de atribuição em lote com foco de teclado, Escape e retorno ao botão; prevenção de envio duplicado; resumo com pedidos atribuídos e motivos dos recusados; instruções da sequência de planejamento; janelas e atrasos legíveis nas paradas; navegação externa por coordenadas; limpeza de filtros nos estados sem resultados. Os recursos continuam adaptados à tela de celular.

## Ajustes de escopo

Os RF01 a RF10 estão cobertos dentro do escopo operacional acima. Para tornar explícitos os limites das ideias registradas nas sprints anteriores:

- O mapa representa distâncias geográficas por Haversine. A integração OSRM para traçado e matriz viária foi retirada do escopo desta entrega, mantendo navegação externa opcional. Essa escolha evita depender de um servidor externo durante a demonstração e mantém a mesma entrada na comparação entre modos. O sistema não calcula trânsito nem promete o menor percurso viário.
- Prioridade e prazo ordenam a atribuição; janelas geram espera e alerta de atraso. Não há garantia matemática de todas as janelas viáveis nem otimização combinatória com prioridade como restrição rígida. Isso preserva o objetivo comum de distância entre os modos sequencial, CPU e GPU.
- Notificações por WhatsApp, SMS ou push, sugeridas como evolução no backlog inicial, ficam fora do escopo consolidado. O acompanhamento usa painel, histórico e atualização periódica das listas.
- Exportação CSV cobre a necessidade operacional; XLSX e PDF de relatórios não fazem parte dos requisitos finais. O PDF acadêmico cumulativo é gerado separadamente.
- Atribuição é uma heurística determinística por carga; não garante a melhor distribuição global.

## Execução e demonstração

A instalação padrão continua usando PostgreSQL conforme `COMO-RODAR.md`. Para esta máquina, que não possui PostgreSQL nem Docker, há demonstração local persistida:

```powershell
cd "C:\Users\v.ribau.fernandes\Documents\Nassau\rotacerta"
.\backend\.venv\Scripts\python.exe tools/run_local_demo.py
```

Abra http://localhost:5173. Conta administrativa: `admin@rotacerta.com.br`; senha demonstrativa `rotacerta123`. O banco isolado fica em `backend/rotacerta-demo.db`. Ctrl+C encerra os servidores sem apagar os dados. Requer as dependências Python de `backend/requirements.txt` e `npm ci` em `frontend`; não requer pgAdmin. Esse modo não deve ser apresentado como evidência de execução em PostgreSQL.

## Evidências e testes

As capturas reais ficam em `assets/`; os registros reproduzíveis em `evidencias/`. O script `tools/documentation/capture_sprint08_evidence.py` exercita fluxos HTTP e interface em uma instância local de demonstração. Os testes adicionais cobrem atribuição, perfis, isolamento de estabelecimentos, regras de carga, integridade de rotas, janelas e migração. Os resultados finais estão em `evidencias/testes.txt` e `evidencias/frontend.txt`.

Validação em 01/11/2026: 139 testes de backend executados, com 138 aprovados e um ignorado por ausência de CUDA; 15 testes de frontend aprovados; build de produção concluído; auditoria npm com zero vulnerabilidades reportadas. Os registros do build e da auditoria estão em `evidencias/build.txt` e `evidencias/auditoria.json`. Isso não substitui teste de aceitação da equipe nem valida concorrência em PostgreSQL.

## Dificuldades e próximos passos

A revisão exigiu conciliar dados atuais do pedido com paradas já registradas e evitar que alterações retroativas mudassem a história da rota. O tratamento foi proteger dados após a saída e invalidar planos afetados antes da execução. Também foi necessário separar tempo de espera operacional do tempo medido pelo algoritmo.

As próximas etapas são testes de aceitação com a equipe, ensaios de concorrência no PostgreSQL, repetição das medições em máquina com CUDA, revisão final de acessibilidade e preparação da apresentação. A GPU não está disponível nesta máquina e seu teste é registrado como ignorado, sem simular resultado.

O Scrum Master deverá revisar a entrega e anexar somente o PDF cumulativo das Sprints 01 a 08 no Teams. Nenhum envio ao Teams é feito pelo projeto ou pelos scripts.
