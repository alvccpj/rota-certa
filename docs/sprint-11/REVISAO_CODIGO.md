# Revisão de código da Sprint 11

Grupo 04 - RotaCerta. Revisão técnica em 10/11/2026 sobre a base `043b6a4`,
com as correções da versão 0.11.0-rc.1. O objetivo foi revisar organização,
legibilidade, consistência, tratamento de erros e proteção das informações
nos módulos entregues e confirmar o funcionamento após os ajustes.

## 1 Escopo e método

A revisão combinou leitura dos módulos principais, rastreamento dos fluxos
da interface até as regras e o banco, revisão de configuração e documentação,
execução das suítes e repetição dos casos na aplicação real. Os achados foram
reproduzidos antes de alterar o comportamento. Não se trata de certificação
de segurança, teste de invasão ou prova de ausência de todos os defeitos.

| Área revisada | Arquivos e pontos observados | Resultado |
| --- | --- | --- |
| Entrada e erros da API | main.py, schemas.py e routers; validação, códigos HTTP e respostas | Contratos mantidos; resposta externa inválida passou a ser tratada |
| Autenticação e autorização | security.py, auth.py, users.py; Argon2, JWT, ativação e perfil no banco | Regras cobertas pela suíte; senha retirada dos logs de inicialização |
| Isolamento dos negócios | Filtros de pedidos/clientes/usuários, referências e propriedade de rotas | Testes entre negócios e entregadores repetidos sem falha |
| Pedidos e entregadores | rules.py, orders.py e users.py; carga, raio, janela, transições e histórico | Restrições e mensagens conferidas com os fluxos |
| Atribuição e transações | assignment.py e test_release_s10.py; bloqueios e commit | Oito chamadas simultâneas preservaram capacidade e unicidade de histórico |
| Planejamento e execução | planning.py e routes.py; substituição de planos, início, paradas e sincronização | Fluxos repetidos; sem alteração no algoritmo de planejamento |
| Otimização CPU/GPU | routing.py, gpu.py, benchmark.py e modelos; limites, pool, desempates e métricas | Limites adicionados ao comparador livre; CUDA lido, mas não reexecutado nesta máquina |
| Consultas e CSV | reporting.py e frontend/reporting.ts; filtros, períodos, limites e escape | Prefixos de fórmula precedidos por espaços passaram a ser neutralizados |
| Interface e sessão | App, session, access, guards, formulários e páginas; navegação e erros | Menus por perfil, redirecionamentos e validações repetidos no navegador |
| Componentes e mapas | Field, ConfirmDialog, AutoRefresh, ErrorBoundary, MapPicker e RouteMap | Foco, confirmações, escape de texto e responsividade conferidos |
| Banco e inicialização | models.py, database.py, schema.sql, seed e configuração | Nove tabelas, 14 FKs sem órfãos, DDL/ORM e persistência conferidos |
| Dependências e execução | requirements, package/lockfile, Dockerfiles, Compose e exemplos | Build e npm audit passaram; Compose validado sintaticamente |
| Organização e documentação | README, manuais, fontes finais, geradores, .gitignore e contribuição | Índice vigente, configuração frontend e destinos de evidência organizados |

## 2 Problemas reproduzidos e corrigidos

### BUG 11 Resposta externa inválida na geocodificação

O código tratava erros HTTP e JSON inválido, mas supunha que o JSON válido
sempre era uma lista de endereços com coordenadas. Uma resposta como um objeto
de erro, item sem latitude ou endereço interno fora do formato podia causar
exceção não tratada. Coordenadas como longitude 181 também eram aceitas e
enviadas ao mapa.

O processamento agora verifica a estrutura da lista e do endereço, converte
os campos dentro do tratamento de erros e valida coordenadas nos limites
geográficos. Formatos inválidos resultam em GeocodingUnavailable, e o roteador
retorna 503 com a orientação de marcar o local manualmente. Lista vazia e
coordenadas zero continuam válidas.

Validação: `GeocoderBoundaryTestCase` em `backend/tests/test_delivery_s11.py`,
com respostas simuladas, sem depender da internet. O registro anterior às
correções está em `evidencias/regressoes_antes_backend.txt`; a suíte final
passou nos dois bancos. Situação: corrigido; severidade média.

### BUG 12 Fórmula precedida por espaços no utilitário CSV

O utilitário `csvCell` protegia prefixos de fórmula no primeiro caractere,
mas preservava, sem neutralização, textos como espaço seguido de `=1+1`.
A proteção foi ampliada para considerar espaços antes dos sinais de fórmula,
mantendo aspas, separadores, acentos e demais textos.

Os cinco casos adicionados em `frontend/src/sprint08.test.mjs` falharam antes
da correção e passaram depois. O registro está em
`evidencias/regressoes_antes_frontend.txt`. Trata-se de reforço do utilitário de
exportação; vários campos já são normalizados no cadastro. Não foi constatado
incidente nem execução de fórmula em dados reais. Situação: corrigido;
severidade média na função de exportação.

## 3 Melhorias de robustez e organização

| ID | Melhoria | Verificação |
| --- | --- | --- |
| AJ11-01 | Comparador público limitado a 64 rotas, 500 paradas por rota e 12.000 no total, antes de iniciar o cálculo | Quatro testes de limites, incluindo aceitação da fronteira; contrato atualizado |
| AJ11-02 | Remoção da senha de demonstração dos logs e do import que só era usado para imprimi-la | Revisão de main.py e dos executores; sem alteração da autenticação |
| AJ11-03 | Exportador de API registra JSON de evidência apenas quando recebe destino explícito | Nova exportação na pasta da Sprint 11, sem sobrescrever a Sprint 10 |
| AJ11-04 | Inspeção do banco aceita destino de evidência por parâmetro | Nova inspeção no schema sprint11_testes |
| AJ11-05 | Adição de frontend/.env.example e índice de documentação; revisão do modelo de pull request existente | Links locais e organização conferidos; nenhum segredo no exemplo frontend |
| AJ11-06 | Manuais completos, documentação final e novos diagramas de arquitetura/classes | Conferência com telas, rotas e modelos implementados; PDF renderizado |

Os limites do comparador reduzem entradas desproporcionais, mas não substituem
controle de taxa ou de recursos da infraestrutura. Não houve mudança do DDL,
do desempate do algoritmo ou da regra de atribuição automática.

## 4 Legibilidade e código desnecessário

A separação entre roteadores, serviços, regras, modelos e interface foi mantida.
As correções usam os mecanismos de exceção e validação existentes, com mudanças
pequenas e testes focados no comportamento. O import da senha no inicializador
foi removido junto da impressão desnecessária. Não foram eliminadas funcionalidades
válidas apenas para reduzir arquivos.

Geradores de documentos anteriores, PDFs cumulativos e registros de Sprint
são histórico intencional. Os módulos de GPU permanecem porque fazem parte do
produto, mesmo sem execução nesta máquina. Caches, builds e bases locais não
são materiais da entrega e estão cobertos pelo .gitignore.

## 5 Verificação das informações e do repositório

O procedimento `tools/documentation/audit_repository.py` verifica arquivos
locais indevidos, proteção do .gitignore, links Markdown relativos e padrões
explícitos de chaves privadas/tokens em arquivos atuais de texto. O resultado
completo está em `evidencias/organizacao_github.json`. Valores encontrados não
são impressos pelo verificador.

Os exemplos de conexão/conta de desenvolvimento já presentes no projeto são
públicos e identificados como demonstração. Os novos manuais não publicam
senhas reais, tokens ou chaves de ambiente. Essa revisão não percorre todo o
histórico Git nem serviços externos e não permite afirmar que qualquer formato
de segredo seria detectado automaticamente.

O repositório é público; manuais e figuras ficam versionados para avaliação.
A branch da Sprint é `codex/sprint-11-preparacao-entrega`. O histórico deve
apresentar a correção técnica e a documentação em commits identificáveis,
com pull request para revisão humana antes da integração.

## 6 Resultados após as correções

| Verificação | Resultado |
| --- | --- |
| Backend PostgreSQL 17.10 | 159 descobertos: 158 aprovados e 1 dispensado por falta de CUDA |
| Backend SQLite | 159 descobertos: 156 aprovados e 3 dispensados, incluindo os dois de concorrência PostgreSQL |
| Frontend | 55 aprovados, sem falhas |
| Navegador | 60 aprovados, nenhum reprovado e F16 não executado por falta de CUDA |
| Interface adicional | 320, 390 e 768 px sem overflow e ações alcançáveis por rolagem interna |
| Build e auditoria npm | Build concluído e zero vulnerabilidades reportadas nesta execução |
| Banco e contrato | Nove tabelas, 14 FKs sem órfãos e 37 operações com contrato sincronizado |
| Backup e restauração | Banco descartável exportado e restaurado em outro banco; dados conferidos |

Os sete novos testes de backend e os cinco casos adicionais de frontend já
estão incluídos nesses totais. A execução que reproduz defeitos antes de corrigi-los
é mantida separada; os resultados finais são os arquivos `testes_*` e
`casos_de_teste.json`. Os testes foram realizados pela equipe por ferramentas,
sem simular uma aceitação externa inexistente.

## 7 Pendências para continuidade

Permanecem pendentes a sessão guiada com usuário externo, a revalidação CUDA
em máquina NVIDIA e a revisão humana do material. Não foram homologados
publicação de produção, carga elevada, todos os navegadores ou combinações
de escritas concorrentes. A subida do Compose não foi reexecutada, apenas sua
configuração foi validada.

Como continuidade técnica, a equipe pode adotar migrações formais, CI de
navegador, limites gerais de requisição e estratégia de publicação. Esses
itens são registrados como próximos passos, não como entregas já implementadas.
