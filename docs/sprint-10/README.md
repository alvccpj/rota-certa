# Sprint 10 Versão Release Candidate

**Grupo 04 - RotaCerta | UNINASSAU | Ciência da Computação | Turma 8NA | 2026.2**

Consolidação e verificações em 10/11/2026. Entrega até 14/11/2026 às 23h59,
horário de Recife. Versão candidata `0.10.0-rc.1`, na branch
`codex/sprint-10-release-candidate`, baseada em `f0b9e20` (Sprint 09 integrada).

Repositório: https://github.com/alvccpj/rota-certa

## Identificação da equipe

| Integrante | Matrícula | Responsabilidade inicial registrada na Sprint 01 |
| --- | --- | --- |
| Álvaro Jordão | 01748200 | Scrum Master e Product Owner; organização, requisitos e priorização |
| Arthur Sales | 01593811 | Backend e núcleo de otimização e paralelização |
| Vinícius Trigueiro | 01794959 | Frontend, banco de dados e documentação |
| William Coelho de Morais | 01263977 | Desenvolvimento e testes |
| Guilherme de Luna Barros | 01615925 | Desenvolvimento e validação do sistema |

As responsabilidades acima preservam a identificação inicial da equipe e não
substituem o registro de contribuições no Git. O envio único no Teams cabe ao
Scrum Master Álvaro Jordão, após a revisão da equipe.

## Descrição da candidata e resultado

A versão candidata integra autenticação e perfis, clientes, usuários e entregadores,
pedidos, atribuição manual e automática, roteirização, execução de entregas,
painel, consultas, histórico e comparação de desempenho. O fluxo cadastro de
cliente e pedido, atribuição, geração de rota, início pelo entregador e confirmação
da entrega foi executado no sistema real, com persistência no PostgreSQL.

Os testes executáveis desta rodada terminaram sem falhas. Foi corrigido um
problema de rolagem da interface no celular. A estrutura final do banco permaneceu
compatível com o DDL existente; o contrato das 37 operações HTTP foi exportado e
conferido contra a API em execução. O README passou a reunir os requisitos,
configuração, instalação, banco, comandos, estrutura e equipe.

A candidata está preparada para a demonstração técnica dos módulos verificados.
A aceitação com usuário externo continua pendente. O modo CUDA não foi revalidado
nesta máquina ARM sem GPU NVIDIA; sua execução anterior está preservada na Sprint 09.

## Entregas e localização das evidências

| Entrega obrigatória | Resultado da Sprint 10 | Evidência no repositório |
| --- | --- | --- |
| Sistema estável | Fluxos reais, suítes automatizadas e concorrência sem falhas nos casos executados | `evidencias/casos_de_teste.json`, `testes_backend_postgresql.txt`, `concorrencia.txt` |
| Interface final | Navegação por perfil, validação de formulários, computador e celular; BUG-10 corrigido | `assets/`, `evidencias/interface_rc.json` |
| Banco final | Nove tabelas compatíveis com os modelos, 14 FKs sem órfãos e isolamento verificado | `evidencias/banco_e_contrato.json`, `database/schema.sql` |
| APIs documentadas | 37 operações com métodos, parâmetros, modelos, acesso e exemplos | `docs/api/README.md`, `ENDPOINTS.md`, `openapi.json` |
| README atualizado | Objetivo, tecnologias, requisitos, instalação, banco, execução, estrutura e equipe | `README.md`, `COMO-RODAR.md` |

Os registros citados pelo nome estão em `docs/sprint-10/evidencias/`, e as capturas,
em `docs/sprint-10/assets/`. Os demais caminhos partem da raiz do repositório.
O PDF de entrega é `output/pdf/Grupo_04_RotaCerta_Sprints_01_a_10.pdf`.

## Ambiente e método de verificação

Execução em macOS ARM64, Python 3.14.7, dez processadores lógicos e PostgreSQL
17.10. Foi usado um cluster separado na porta 5540, banco descartável
`rotacerta_rc`, sem alterar o PostgreSQL de desenvolvimento. O roteiro de navegador
usou o schema `sprint10_testes`, API na porta 8020 e Vite na porta 5190.
As suítes do backend recriam somente `rotacerta_testes_automatizados`.

O Chrome foi controlado por Playwright com interface em português e fuso de
Recife. O roteiro reutiliza os 61 casos da Sprint 09, com capturas novas e
registro de procedimento, esperado, obtido e situação. A verificação extra de
interface confere as larguras de 320, 390 e 768 px e o acesso às ações por
rolagem interna da tabela. O teste N19 cobre o menu em 1024, 1280, 1366 e 1920 px.

## Resultados dos testes

| Verificação | Resultado atual | Registro |
| --- | --- | --- |
| Funcionais na aplicação real | 21 aprovados, 1 não executado por ausência de CUDA | `casos_de_teste.json`, F01 a F22 |
| Validação na aplicação real | 20 aprovados, 0 falhas | `casos_de_teste.json`, V01 a V20 |
| Navegação na aplicação real | 19 aprovados, 0 falhas | `casos_de_teste.json`, N01 a N19 |
| Backend em SQLite | 152 descobertos: 149 aprovados, 3 dispensados | `testes_backend_sqlite.txt` |
| Backend em PostgreSQL | 152 descobertos: 151 aprovados, 1 dispensado | `testes_backend_postgresql.txt` |
| Frontend | 50 aprovados, 0 falhas | `testes_frontend.txt` |
| Regressão visual adicional | 320, 390 e 768 px sem overflow da página; ações acessíveis | `interface_rc.json` |
| Build de produção | TypeScript e Vite concluídos | `build.txt` |
| Auditoria npm | Zero vulnerabilidades reportadas nesta execução | `auditoria_npm.json` |
| Banco e contrato | Nove tabelas, 14 FKs sem órfãos, 37 operações sincronizadas | `banco_e_contrato.json` |

No SQLite, são dispensados o teste CUDA e os dois testes específicos de
concorrência PostgreSQL. No PostgreSQL, apenas CUDA é dispensado. Os dois testes
de concorrência já estão incluídos nos 152, não devem ser somados novamente.
No navegador, F16 não foi executado; F22 comparou sequencial e CPU paralela
com 1, 2 e 4 processos, com igualdade das rotas. Nenhum desses resultados
representa homologação externa ou teste de carga de produção.

## Fluxos principais demonstrados

| Fluxo | Procedimento e resultado observado | Casos |
| --- | --- | --- |
| Acesso e cadastro | Login, saída, novo negócio e perfis corretos; negócios isolados | F01 a F03, N01 a N08, N16 |
| Clientes e pedidos | Cadastro, pesquisa, edição e exclusão permitida; dados persistidos | F04 a F13 |
| Distribuição e rotas | Pedido atribuído automaticamente; duas rotas sequenciais com paradas e métricas | F14, F15 |
| Entrega no celular | Entregador iniciou rota e confirmou entrega; autor e horário no histórico | F17 |
| Cancelamento | Motivo válido gravado; motivo curto recusado | F18, V11 |
| Acompanhamento | Indicadores coerentes, relatório filtrado/exportado e histórico pesquisável | F19 a F21 |
| Otimizador | Mesmas rotas nos modos sequencial e CPU paralela na comparação | F22 |
| Persistência | Nova conexão SQL e nova sessão HTTP leram os mesmos 19 IDs e situações do negócio de demonstração | `banco_e_contrato.json` |

As capturas desta Sprint acompanham o PDF. O registro JSON contém os resultados
de todos os 61 casos, inclusive o motivo da não execução de F16. Os prints são
evidências complementares do sistema executado; os testes também verificam
respostas da API e estados persistidos.

## Concorrência na atribuição automática

A pendência técnica da Sprint 09 foi verificada em PostgreSQL real. Em cada
rodada foram criados 30 pedidos de 1 kg e dois entregadores disponíveis de
10 kg. Oito clientes de teste dispararam `POST /orders/auto-assign` após uma
barreira de sincronização, usando sessões de banco independentes. Foram três
rodadas, totalizando 24 requisições concorrentes nesse cenário.

| Rodada | Chamadas simultâneas | Atribuídos únicos | Permaneceram pendentes | Carga por entregador | Eventos de atribuição |
| --- | --- | --- | --- | --- | --- |
| 1 | 8 | 20 | 10 | 10 kg e 10 kg | 20, sem duplicação |
| 2 | 8 | 20 | 10 | 10 kg e 10 kg | 20, sem duplicação |
| 3 | 8 | 20 | 10 | 10 kg e 10 kg | 20, sem duplicação |

Um segundo teste disparou oito chamadas com a fila vazia: todas retornaram
`assigned: []` e `skipped: []`, sem novos eventos. Não houve erro HTTP, estouro
de capacidade nem reatribuição. O bloqueio de linha do estabelecimento existente
em `app/assignment.py` serializou as chamadas dessa operação até o commit.

O ensaio cobre atribuição automática contra atribuição automática no mesmo
estabelecimento. Escritas simultâneas de tipos diferentes e volume elevado
continuam fora dessa comprovação. Reprodução e saída estão em
`backend/tests/test_release_s10.py` e `evidencias/concorrencia.txt`.

## Interface final e correção realizada

A interface mantém a identidade visual verde, amarelo e grafite, com componentes
compartilhados para formulários, confirmações, mensagens, indicadores e mapas.
Os menus respeitam o perfil, a página atual recebe destaque e as páginas protegidas
redirecionam corretamente. O celular usa menu recolhível, cartões de entrega e
rolagem dentro das tabelas largas. Campos inválidos exibem mensagem junto ao
campo, resumo e foco no primeiro erro.

**BUG-10 - Rolagem horizontal indevida em Clientes no celular.** A execução N13
detectou overflow de 251 px na página em uma rodada. A reprodução identificou
o rótulo absoluto de acessibilidade do cabeçalho da tabela fora de um bloco de
posicionamento local. A tabela rolável não continha sua contribuição à largura
do documento no Chrome/macOS observado. Foi incluído `position: relative` em
`.table-wrap` (`frontend/src/styles.css`), mantendo a rolagem da tabela e as
ações acessíveis. Severidade média; situação corrigida.

Após a correção, o documento mediu exatamente 320, 390 e 768 px nas respectivas
larguras; a tabela de 981 px continuou rolável dentro da página. N13 passou e
o roteiro adicional confirmou a visibilidade do botão Excluir após a rolagem.
O caso F08 também passou a aguardar a renderização das linhas filtradas:
a URL era atualizada antes do React concluir a tabela. Esse ajuste foi no
roteiro e não representa um bug adicional do produto.

## Estrutura final do banco de dados

O arquivo `database/schema.sql` é o DDL final da candidata. Não houve nova
migração na Sprint 10; o modelo atualizado da Sprint 09 permanece válido.
As nove tabelas e todas as colunas foram comparadas com os modelos SQLAlchemy.

| Tabela | Colunas | Finalidade e principais vínculos |
| --- | --- | --- |
| establishments | 7 | Negócio e ponto de saída; origem do isolamento |
| users | 8 | Conta, perfil, ativação e hash; FK para negócio; e-mail único |
| couriers | 6 | Capacidade e disponibilidade; FKs para negócio e usuário único |
| customers | 5 | Cliente vinculado ao negócio |
| orders | 13 | Local, peso, prioridade, janela e situação; cliente e entregador opcional |
| order_status_history | 6 | Pedido, situação, observação, autor e horário |
| routes | 10 | Negócio, entregador, data, situação, algoritmo, modo e métricas |
| route_stops | 8 | Rota, pedido único, sequência, chegada, espera e situação |
| optimization_runs | 16 | Comparações/gerações por negócio, modos, tempos, distância e ganho |

As PKs são `BIGSERIAL`, FKs `BIGINT`, medidas `NUMERIC` e instantes
`TIMESTAMPTZ`. Há unicidade de usuário por entregador, pedido por parada e
sequência por rota, além dos checks de perfis, situações, modos, pesos,
capacidade, prioridade, janela, espera e métricas. Os índices atendem às
consultas de pedidos por negócio/situação, entregador, histórico, rotas e execuções.

Foram inspecionadas 14 FKs, todas sem registros órfãos. As consultas de
consistência não encontraram vínculo entre negócios diferentes em pedido/cliente,
pedido/entregador, rota/entregador ou parada/pedido. A API complementa as FKs com
as regras de isolamento, transição, raio e carga. O JSON de inspeção contém
colunas, PKs, FKs, checks, índices, unicidades e contagem de registros.

Para instalação nova, o Compose aplica o DDL no primeiro volume ou a API aplica
o arquivo ao encontrar um PostgreSQL vazio. Bancos anteriores recebem as
atualizações incrementais de `app/database.py`. Os dados de demonstração são
opcionais (`SEED_DEMO_DATA`). Detalhes em `database/README.md`.

## APIs documentadas

O guia permanente está em https://github.com/alvccpj/rota-certa/blob/codex/sprint-10-release-candidate/docs/api/README.md

O catálogo contém as 37 operações HTTP, com métodos, rotas, parâmetros,
obrigatoriedade, modelos de entrada/saída e perfis. O contrato OpenAPI 3.1 inclui
todos os campos, tipos e limites e foi comparado com `GET /openapi.json`, sem
diferenças. O exportador `tools/documentation/export_api_docs.py` permite
atualizar ambos a partir da aplicação.

Com a API ligada: Swagger em `http://localhost:8000/docs`, ReDoc em
`http://localhost:8000/redoc` e contrato em `http://localhost:8000/openapi.json`.
Esses endereços são locais; o guia e o JSON do repositório podem ser consultados
sem um servidor publicado. O PDF inclui o catálogo resumido e uma captura do Swagger.

O login recebe `email` e `password` em JSON e devolve `access_token`,
`token_type` e `user`. As chamadas protegidas usam `Authorization: Bearer TOKEN`.
ADMIN administra usuários, ponto de saída e desempenho; ADMIN e ATTENDANT
operam os módulos de gestão; COURIER opera suas próprias entregas. O endpoint
experimental `/optimizer/compare` é público e não persiste pedidos.

Exemplo de entrada de pedido (substituir o ID do cliente por um ID do próprio negócio):

```json
{"customer_id": 1, "delivery_address": "Rua do Bom Jesus, 197 - Recife",
 "latitude": -8.0617, "longitude": -34.8709, "weight_kg": 2, "priority": 1}
```

`POST /orders` retorna 201 com o pedido, cliente e situação inicial. Em seguida,
`POST /orders/auto-assign` retorna 200 com `assigned` e `skipped`;
`POST /routes/generate` aceita `{"mode":"SEQUENTIAL","workers":1}`.
O entregador consulta `/routes/me`, inicia `/routes/{route_id}/start` com PATCH
e confirma o pedido em `/orders/{order_id}/status` com `{"status":"DELIVERED"}`.
Os filtros e os exemplos completos com curl estão no guia.

| HTTP | Interpretação |
| --- | --- |
| 200 / 201 / 204 | Consulta/operação concluída, criação concluída ou exclusão/desativação sem corpo |
| 401 / 403 | Sessão inválida ou perfil/conta sem acesso |
| 404 | Registro inexistente ou não visível |
| 409 | Conflito de negócio, duplicidade, transição proibida ou GPU indisponível |
| 422 | Campo, janela, identificador ou vínculo inválido |
| 503 | Banco indisponível no health check ou serviço de geocodificação indisponível |

Erros de negócio usam `detail` textual; validações de modelo usam uma lista
`detail` com `loc`, `msg` e `type`. O relatório retorna JSON; a exportação CSV
é feita pela interface. Não há endpoint de CSV.

## README e execução da candidata

README atualizado: https://github.com/alvccpj/rota-certa/blob/codex/sprint-10-release-candidate/README.md

O README identifica projeto, objetivo, tecnologias e os cinco integrantes.
Inclui Git, Python 3.12+, Node.js 20.19+ ou 22.12+ e PostgreSQL 16+ como
requisitos; GPU é opcional. Apresenta instalação com Docker ou manual,
variáveis de ambiente, criação do banco, inicialização, testes e estrutura.
O guia `COMO-RODAR.md` complementa os comandos para Windows.

Execução rápida com Docker, na raiz:

```bash
cp .env.example .env
docker compose up --build
```

O sistema abre em `http://localhost:5173`; a API, em `http://localhost:8000`.
As contas de exemplo são `admin@rotacerta.com.br`, `atendente@rotacerta.com.br`
e `entregador@rotacerta.com.br`, com senha `rotacerta123`. Em instalação manual,
crie usuário e banco PostgreSQL, ajuste `backend/.env`, instale as dependências,
execute `uvicorn app.main:app` em `backend` e `npm run dev` em `frontend`.
A execução desta Sprint foi manual em PostgreSQL; Docker não foi revalidado nesta rodada.

A estrutura está organizada em `backend/app` (API e regras), `backend/tests`
(testes), `frontend/src` (telas/componentes), `database` (DDL), `docs/api`
(contrato e guia), `docs/sprint-*` (histórico), `tools` (roteiros) e `output/pdf`
(documentos de entrega). Backend e frontend identificam a mesma versão RC.

## Principais correções e ajustes

| Registro | Ajuste | Comprovação |
| --- | --- | --- |
| BUG-10 | Contenção do rótulo absoluto na tabela; elimina overflow da página no celular | N13 e `interface_rc.json` |
| Pendência técnica S09 | Dois testes concorrentes em PostgreSQL adicionados | Três lotes com oito chamadas e fila vazia; sem duplicação/carga excedida |
| Documentação de API | Guia, catálogo e contrato exportado | 37 operações; contrato idêntico ao servido |
| Identificação da candidata | Versão `0.10.0-rc.1` no backend e frontend | `/openapi.json` e build |
| Reprodução dos testes | Ambiente permite schema/portas próprios; roteiro aceita destino de evidências e registra dispensas CUDA | Execução em `sprint10_testes` e códigos de saída de falha |
| README e banco | Instalação, estrutura, requisitos e estrutura final documentados | README, guia de execução e documentação do banco |
| Documento de entrega | Histórico preservado e Parte X acrescentada | PDF cumulativo das Sprints 01 a 10 |

As nove correções BUG-01 a BUG-09 da Sprint 09 permanecem cobertas pelas suítes
e pelos casos repetidos. Não foi identificado outro defeito bloqueador nos
cenários executados. Esta afirmação se limita à cobertura registrada.

## Pendências e próximos passos

| Pendência ou limite | Ação antes da apresentação final | Responsável pela coordenação |
| --- | --- | --- |
| Aceitação com usuário externo | Realizar sessão guiada de cadastro, atribuição e entrega; registrar observações e corrigir bloqueios encontrados | Scrum Master com apoio da equipe |
| CUDA nesta candidata | Repetir F16 e benchmark na máquina NVIDIA; conferir rotas e métricas. A execução da Sprint 09 é histórica | Backend e otimização |
| Validação humana e integração | Revisar documento e pull request, integrar a candidata ao ramo principal e confirmar os links finais | Equipe e Scrum Master |
| Envio no Teams | Anexar somente o PDF cumulativo até 14/11/2026 às 23h59 | Álvaro Jordão |
| Automação de interface | Avaliar CI com PostgreSQL e navegador; roteiro ainda é manualmente iniciado | Equipe |

Continuam os limites de escopo aprovados nas Sprints 08 e 09: distância
geográfica sem ruas/trânsito, previsões sem garantia de janelas, sem notificações
externas e exportação em CSV. O ensaio concorrente não substitui teste de carga
nem cobre todas as combinações de escritas. GPU pode ser mais lenta em instâncias
pequenas; desempenho deve ser apresentado com a entrada, o hardware e o modo usados.

A candidata não deve receber ampliação de escopo antes da apresentação. Novas
correções exigem repetir a verificação afetada e atualizar as evidências.

## Reprodução da verificação

Com dependências instaladas, PostgreSQL disponível e Google Chrome instalado,
ative o ambiente virtual e execute na raiz. Em Windows, substitua a ativação
por `backend\.venv\Scripts\Activate.ps1`; os comandos Python são os mesmos.

```bash
source backend/.venv/bin/activate
pip install -r backend/requirements-docs.txt
python -m unittest discover backend/tests -v
export TEST_DATABASE_URL=postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta
python -m unittest discover backend/tests -v
unset TEST_DATABASE_URL
npm test --prefix frontend
npm run build --prefix frontend
python tools/documentation/export_api_docs.py
python tools/run_test_environment.py --schema sprint10_testes --api-port 8020 --web-port 5190
```

O último comando recria o schema descartável `sprint10_testes`. Para outro
PostgreSQL, defina `POSTGRES_URL` antes de iniciá-lo. Em outro terminal, execute:

```bash
python tools/documentation/capture_sprint10_evidence.py
RC_DB='postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta'
DATABASE_URL="${RC_DB}?options=-csearch_path%3Dsprint10_testes" \
  python tools/documentation/verify_release.py
```

O exportador atualiza a documentação; o roteiro atualiza os registros e as
capturas desta Sprint. A inspeção consulta o DDL e compara a API com SQL em outra
conexão. Para reconstruir o PDF, execute `tools/documentation/build_sprint10_document.py`
com as dependências de documento descritas no próprio script.

## Roteiro de demonstração para a apresentação

- Entrar como administrador e abrir Visão geral; explicar indicadores e perfis.
- Cadastrar um cliente e um pedido com endereço e posição no mapa.
- Atribuir automaticamente; explicar capacidade, disponibilidade e pedidos não atribuídos.
- Gerar rotas em CPU; mostrar mapa, paradas, distância e previsão.
- Entrar como entregador no celular, iniciar a rota e confirmar a entrega.
- Conferir histórico, painel e relatório; exportar CSV do resultado filtrado.
- Abrir Swagger e executar uma consulta autenticada; mostrar o contrato versionado.
- Mostrar a comparação de desempenho nos modos disponíveis, sem prometer ganho para todo tamanho de entrada.

## Consolidação para entrega

O documento único preserva as páginas 2 a 150 do PDF anterior, substitui a capa
e acrescenta a Parte X com os resultados e evidências atuais. As partes anteriores
permanecem como registros históricos; em caso de divergência, a Sprint 10 descreve
o estado desta candidata. Os integrantes continuam identificados na capa e nesta parte.

Antes do envio, revisar o PDF, conferir o pull request e o README no GitHub.
Somente o Scrum Master envia o documento cumulativo, sem necessidade de anexar
arquivos de código ou PDFs separados na tarefa do Teams.
