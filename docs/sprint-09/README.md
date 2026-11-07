# Sprint 09 - Testes, correções e documentação

Projeto RotaCerta, Grupo 04, turma 8NA. Testes executados e documentação revisada em 07/11/2026.
Repositório: https://github.com/alvccpj/rota-certa
Branch: `sprint/09-testes-validacao`, criada a partir de `master` após o merge da Sprint 08 (PR #11).

## Objetivo e resultado

A Sprint 09 verificou o sistema completo antes da versão final: testes funcionais, de validação e de navegação executados na aplicação real, correção dos problemas encontrados e atualização da documentação técnica para a versão atual.

| Verificação | Casos | Aprovados | Onde está o registro |
| --- | --- | --- | --- |
| Testes funcionais (interface e API) | 22 | 22 | evidencias/casos_de_teste.json |
| Testes de validação | 20 | 20 | evidencias/casos_de_teste.json |
| Testes de navegação | 19 | 19 | evidencias/casos_de_teste.json |
| Testes automatizados do backend em SQLite | 150 | 150 | evidencias/testes_backend_sqlite.txt |
| Testes automatizados do backend em PostgreSQL 18.1 | 150 | 150 | evidencias/testes_backend_postgresql.txt |
| Testes automatizados do frontend | 50 | 50 | evidencias/testes_frontend.txt |
| Build de produção e auditoria npm | 2 | 2 | evidencias/build.txt e evidencias/auditoria_npm.json |

Foram encontrados e corrigidos 9 bugs (BUG-01 a BUG-09). Cada correção tem teste de regressão que falha no código anterior e passa no código atual. Não há bug conhecido em aberto; as pendências de escopo estão listadas no fim deste documento.

## Como os testes foram realizados

Os 61 casos de teste são executados pelo script `tools/documentation/capture_sprint09_evidence.py`. Ele abre o sistema no Google Chrome (Playwright), age como o usuário (preenche campos, clica em botões e menus, usa a tela de celular) e confere o resultado na tela e, quando faz sentido, também na API. Cada caso registra o procedimento, o resultado esperado, o resultado obtido e a situação. Quando um caso falha, o motivo é registrado e os demais continuam. Os casos que dependem só do servidor (por exemplo, valores que a interface já bloqueia) foram executados direto na API, como faria um cliente mal-intencionado ou com defeito.

Ambiente da execução oficial:

| Item | Valor |
| --- | --- |
| Data | 07/11/2026, 11h34 (horário de Recife) |
| Banco | PostgreSQL 18.1, schema isolado `sprint09_testes`, recriado antes da execução com os dados de demonstração |
| API e sistema | FastAPI em 127.0.0.1:8019; frontend (Vite) em 127.0.0.1:5189 |
| Navegador | Google Chrome via Playwright, telas de 1366 px (computador) e 390 px (celular) |
| Máquina | Ryzen 7 5700X, 16 threads; GPU NVIDIA GeForce RTX 3060 (CUDA) |

O schema `public`, usado no desenvolvimento, não foi alterado. Antes da execução oficial o roteiro foi rodado algumas vezes durante a investigação; a execução registrada é a última, numa base limpa, com 61 de 61 casos aprovados.

## Como reproduzir

Na raiz do repositório, com o PostgreSQL ligado e as dependências instaladas (`COMO-RODAR.md`):

```powershell
.\backend\.venv\Scripts\python.exe tools/run_test_environment.py
```

O comando recria o schema `sprint09_testes`, sobe a API (porta 8019) e o sistema (porta 5189). Em outro terminal:

```powershell
.\backend\.venv\Scripts\python.exe tools/documentation/capture_sprint09_evidence.py
```

O resultado é gravado em `docs/sprint-09/evidencias/casos_de_teste.json` e as capturas em `docs/sprint-09/assets/`. As suítes automatizadas rodam com os comandos da seção "Testes automatizados" de `COMO-RODAR.md`.

## Testes funcionais

Cobrem os módulos e operações do sistema: autenticação (login, saída e cadastro de negócio), clientes (cadastro, pesquisa, edição e exclusão), pedidos (cadastro, consulta com filtro, edição, exclusão e cancelamento), usuários (cadastro e desativação), atribuição automática, geração de rotas nos modos sequencial e GPU, execução da entrega pelo entregador no celular, painel, relatório com exportação CSV, histórico operacional e comparação de desempenho. A tabela completa, com procedimento, resultado esperado e resultado obtido de cada caso, está em `evidencias/casos_de_teste.json` e no PDF cumulativo.

## Testes de validação

Verificam se o sistema recusa dados inválidos e explica o motivo: campos obrigatórios vazios, formatos inválidos (e-mail, telefone, senha, nome), limites (peso de 0 a 500 kg, raio de 30 km, capacidade abaixo da carga ativa), regras de negócio (janela invertida ou no passado, cancelamento sem motivo, cliente e e-mail duplicados) e entradas que chegam direto à API (endereço só com espaços, fusos misturados, identificadores gigantes, caracteres de controle e token adulterado). Na interface, cada erro aparece junto ao campo, com resumo no topo do formulário e foco no primeiro campo inválido.

## Testes de navegação

Verificam redirecionamentos (página protegida sem login, volta à página pedida, usuário logado abrindo login), menus de cada perfil (cada item abre a tela certa e fica destacado), permissões (acesso negado na interface e 403 na API), isolamento entre estabelecimentos e entre entregadores, páginas inexistentes, identificadores inválidos no endereço, menu no celular, continuidade entre lista, detalhe e edição, sessão expirada e botão Voltar do navegador depois de sair.

## Registro de bugs

| ID | Severidade | Problema | Como foi encontrado | Causa | Correção | Teste de regressão | Situação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-01 | Média | Endereço do pedido, nome do negócio e ponto de saída formados só por espaços eram aceitos e gravados vazios. | Validação direta na API (V14). | O tamanho mínimo era conferido antes de remover os espaços. | Validadores `address_text` e `business_name` conferem o texto já normalizado (`backend/app/schemas.py`). A interface passou a usar a mesma regra. | `test_validation_s09.BlankTextTestCase` (5 testes) e V14. | Corrigido |
| BUG-02 | Alta | Janela de entrega com uma data sem fuso e outra com fuso derrubava a API com erro 500. | Validação direta na API (V15). | Comparação entre data com e sem fuso no validador da janela. | As datas são normalizadas para UTC antes da comparação (`WindowTime` em `schemas.py`). | `WindowTimezoneTestCase` (2 testes) e V15. | Corrigido |
| BUG-03 | Média | Identificador acima de 64 bits no endereço da API (`/orders/99999999999999999999`) gerava erro 500. | Validação direta na API, confirmada no PostgreSQL (V16). | O banco rejeita o número e o erro não era tratado. | Tratador global converte erros de valor do banco (`DataError`, `OverflowError`) em HTTP 422 com mensagem em português (`backend/app/main.py`). | `test_huge_ids_return_validation_error` e V16. | Corrigido |
| BUG-04 | Média | Texto com o caractere nulo (`\u0000`) gerava erro 500 no PostgreSQL. | Validação direta na API no PostgreSQL (V17). | O PostgreSQL não aceita esse caractere em campos de texto. | A normalização de texto remove caracteres de controle; o tratador do BUG-03 cobre os demais campos. | `test_control_characters_are_removed_from_names`, `test_cancellation_reason_made_of_control_characters_is_rejected` e V17. | Corrigido |
| BUG-05 | Baixa | Endereços como `/pedidos/abc` e `/clientes/abc/editar` mostravam "Corrija o campo destacado." numa tela sem formulário. | Teste de navegação (N11). | O erro de validação do parâmetro do endereço era tratado como erro de formulário. | `frontend/src/api.ts` trata erro de parâmetro do endereço como registro não encontrado (404); a edição de pedido mostra a mensagem de não encontrado. | `sprint09.test.mjs` e N11. | Corrigido |
| BUG-06 | Média | Depois do login, o usuário nunca voltava à página que tinha pedido; sempre ia para o início. | Teste de navegação (N02). | Ao criar a sessão, o redirecionamento de "já está logado" da tela de login acontecia antes da navegação para a página pedida. | `frontend/src/access.ts` decide o destino conforme o perfil e é usado pelo login e pelo redirecionamento; página não permitida ao perfil leva ao início dele. | `sprint09.test.mjs` (18 testes) e N01 a N03. | Corrigido |
| BUG-07 | Média | No modo de demonstração SQLite (Sprint 08), as janelas dos pedidos de exemplo ficavam 3 horas antes do previsto. Um teste da Sprint 08 passava só por causa disso e falhava no PostgreSQL. | Execução da suíte de backend no PostgreSQL, feita pela primeira vez nesta Sprint. | Os dados de exemplo eram gravados no fuso de Recife; o SQLite descarta o fuso e a aplicação lê a data como UTC. | Os dados de exemplo são gravados em UTC (`backend/app/seed.py`); o teste da Sprint 08 usa um entregador próprio. | `SeedWindowTestCase` e `test_generated_wait_survives_a_new_database_session`, nos dois bancos. | Corrigido |
| BUG-08 | Baixa | Com a sessão expirada, o sistema voltava ao login sem o aviso "Sua sessão expirou". | Teste de navegação (N15). | O aviso ia no estado da navegação e era substituído pelo redirecionamento das páginas protegidas. | O aviso fica no contexto da sessão; a página atual é guardada para o usuário voltar a ela (`frontend/src/session.tsx`). | N15, conferido também contra o código anterior. | Corrigido |
| BUG-09 | Média | No computador, o menu do administrador cortava o item Usuários em todas as larguras, sem barra de rolagem visível. | Revisão das capturas dos testes de navegação; medição em 1280 a 1920 px. | Os 8 itens precisavam de 815 px e dividiam a linha com a marca e a conta, restando 689 px. | O menu passou para uma linha própria abaixo da marca e da conta, com quebra se necessário (`frontend/src/styles.css`). No celular continua o botão Menu. | N19 (1024, 1280, 1366 e 1920 px) e N13. | Corrigido |

Além dos bugs do sistema, a primeira execução do roteiro teve dois casos reprovados por falhas do próprio roteiro: leitura errada do formato de `/optimizer/capabilities` (F16) e uma corrida no N15, que adulterava o token antes de o sistema terminar de confirmar a sessão e regravá-lo. O roteiro foi corrigido e a execução oficial foi refeita do zero.

## Testes automatizados

A suíte do backend passou a rodar também no PostgreSQL real com a variável `TEST_DATABASE_URL`. Cada teste recria um schema descartável aplicando `database/schema.sql`, o mesmo DDL usado na instalação. Essa execução encontrou o BUG-07, que o SQLite escondia, e fecha a pendência da Sprint 08 de validar o comportamento em PostgreSQL.

| Suíte | Resultado | Observação |
| --- | --- | --- |
| Backend em SQLite em memória | 150 de 150 aprovados | Inclui 11 testes novos da Sprint 09; o teste de GPU executou na RTX 3060. |
| Backend em PostgreSQL 18.1 | 150 de 150 aprovados | Mesma suíte, no schema `rotacerta_testes_automatizados`. |
| Frontend (`node --test`) | 50 de 50 aprovados | 15 da Sprint 08 e 35 novos: destino após login, tratamento de erros da API e validações dos formulários. |
| Build de produção | Concluído | `tsc -b` e `vite build` sem erros. |
| Auditoria npm | 0 vulnerabilidades | `npm audit` em 07/11/2026. |

## Atualização da documentação

| Documento | Atualização |
| --- | --- |
| Arquitetura (`assets/arquitetura_v09.png`) | Substitui a da Sprint 02: retira o adaptador OSRM, fora do escopo desde a Sprint 08; inclui GPU com CUDA, geocodificação por Nominatim, distância Haversine, perfis, isolamento por estabelecimento e os serviços de regras, atribuição e relatórios. |
| Modelo de dados (`assets/mer_v09.png`) | Gerado a partir do schema atual: inclui `order_status_history` (Sprint 04), as métricas de `optimization_runs` (Sprint 05), `route_stops.waiting_minutes` (Sprint 08) e as restrições de unicidade. |
| Requisitos | Situação de cada requisito RF01 a RF10 na versão atual, na tabela abaixo. |
| `README.md` | Módulo da Sprint 09, link para o PDF 01 a 09 e para os testes. |
| `COMO-RODAR.md` | Testes no PostgreSQL, testes de frontend, ambiente de testes isolado e execução dos casos de teste. |
| `database/README.md` | Alterações das Sprints 08 e 09 e link para o modelo de dados atualizado. |
| Diagrama de classes da Sprint 02 | Mantido como registro do planejamento. A estrutura implementada é descrita pela arquitetura e pelo modelo de dados acima e pelos módulos de `backend/app`. |

## Requisitos na versão atual

| Requisito | Situação | Verificado por |
| --- | --- | --- |
| RF01 Autenticação e perfis | Implementado | F01 a F03, F11, F12, V01 a V03, V20, N01 a N08, N12, N15, N18 |
| RF02 Pedidos | Implementado | F07 a F10, F18, V06 a V11, V14, V15 |
| RF03 Entregadores | Implementado | F11, F12, V13, V19 |
| RF04 Rotas otimizadas | Implementado (sequencial, CPU e GPU) | F15, F16, F22 |
| RF05 Atribuição | Implementado (manual e automática) | F14 |
| RF06 Lista e mapa | Implementado | F15, F17, N06 |
| RF07 Situação da entrega | Implementado | F17, F18, V11 |
| RF08 Histórico | Implementado | F17, F18, F21 |
| RF09 Relatórios | Implementado (CSV) | F20, V18 |
| RF10 Painel | Implementado | F19 |

Os limites de escopo registrados na Sprint 08 continuam válidos: distâncias geográficas sem trânsito, janelas como previsão e não como garantia, sem notificações externas e exportação somente em CSV.

## Pendências e ações previstas

- Concorrência no PostgreSQL: as regras agora são testadas no PostgreSQL real, mas ainda não houve ensaio com várias atribuições automáticas simultâneas. Ação: teste com requisições paralelas a `/orders/auto-assign` na Sprint 10.
- Teste de aceitação com usuários: os casos foram executados pela equipe com o roteiro automatizado. Ação: sessão guiada com um usuário que não participou do desenvolvimento, usando o roteiro desta Sprint, antes da apresentação final.
- Desempenho da GPU: com 480 pedidos (F22), a GPU foi mais lenta que a CPU paralela, porque o custo de enviar os dados à GPU supera o ganho nesse tamanho. Não é defeito; a comparação com instâncias maiores está na tela Desempenho e será apresentada na entrega final.
- Testes de interface no repositório: o roteiro Playwright exige o ambiente de testes ligado e ainda não roda em integração contínua. Ação: avaliar um fluxo de GitHub Actions com PostgreSQL de serviço.

## Dificuldades encontradas

- Bugs que só aparecem num dos bancos: o BUG-07 ficava escondido no SQLite e só apareceu quando a suíte passou a rodar no PostgreSQL. A solução foi manter as duas execuções.
- Diferenciar falha do sistema de falha do teste: dois casos reprovaram na primeira execução por erro do roteiro. Cada reprovação foi investigada antes de ser registrada; o BUG-08 foi confirmado executando o mesmo cenário no código anterior.
- Evitar alterar o banco de desenvolvimento: os testes de interface criam e excluem registros. Por isso foram feitos num schema isolado, recriado a cada execução.

## Próximos passos

Sprint 10: ensaio de concorrência, teste de aceitação com usuário externo, revisão final da apresentação e congelamento da versão final. O Scrum Master deve revisar este documento e anexar no Teams somente o PDF cumulativo das Sprints 01 a 09 (`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_09.pdf`).
