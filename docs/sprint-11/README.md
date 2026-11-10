# Sprint 11 Preparação para entrega

**Grupo 04 - RotaCerta | UNINASSAU | Ciência da Computação | Turma 8NA | 2026.2**

Documentação e verificação concluídas em 10/11/2026. Prazo da atividade:
21/11/2026 às 23h59, horário de Recife. Versão 0.11.0-rc.1, preparada na
branch `codex/sprint-11-preparacao-entrega`, a partir de `043b6a4`, com a Sprint 10
já integrada à master. Repositório público: https://github.com/alvccpj/rota-certa

## Identificação da equipe

| Integrante | Matrícula | Responsabilidade inicial registrada |
| --- | --- | --- |
| Álvaro Jordão | 01748200 | Scrum Master e Product Owner; organização, requisitos e priorização |
| Arthur Sales | 01593811 | Backend e núcleo de otimização e paralelização |
| Vinícius Trigueiro | 01794959 | Frontend, banco de dados e documentação |
| William Coelho de Morais | 01263977 | Desenvolvimento e testes |
| Guilherme de Luna Barros | 01615925 | Desenvolvimento e validação do sistema |

As responsabilidades mantêm a identificação histórica da equipe. As
contribuições efetivas devem ser acompanhadas pelo histórico Git e pela revisão
dos integrantes. Somente o Scrum Master Álvaro Jordão realiza o envio no Teams.

## Objetivo e resultado da Sprint

A Sprint 11 prepara o projeto para outra pessoa compreender, executar e usar
o sistema. Foram elaborados o Manual do Usuário ilustrado e o Manual Técnico,
consolidados requisitos/casos de uso/regras e revisados os principais módulos
do código, sua configuração e organização no GitHub.

A revisão resultou em duas correções de comportamento, limites para o
comparador livre, retirada da senha de demonstração dos logs e ajustes nos
roteiros para preservar evidências de Sprints encerradas. Os testes foram
repetidos na versão atual, e os manuais descrevem somente recursos implementados.

O documento de entrega reúne todas as Sprints anteriores e a Parte XI.
Os dois manuais estão incluídos integralmente no PDF e também disponíveis no
repositório. Não é necessário ter a aplicação publicada para ler os materiais.

## Entregas obrigatórias e documentos

| Entrega | Material preparado | Localização |
| --- | --- | --- |
| Manual do Usuário | Acesso, perfis, telas, cadastros, atribuição, rotas, entrega, consultas, mensagens e roteiro de treinamento, com capturas atuais | docs/manuais/MANUAL_DO_USUARIO.md |
| Manual Técnico | Arquitetura, tecnologias, módulos, ambiente, instalação, banco, variáveis sem valores privados, APIs, otimização, testes e manutenção | docs/manuais/MANUAL_TECNICO.md |
| Documentação final | RF01-RF10, RNF01-RNF07, UC01-UC07, regras, decisões e diagramas vigentes | docs/final/DOCUMENTACAO_FINAL.md |
| Revisão do código | Escopo por módulo, defeitos reproduzidos, correções, melhorias e validações | docs/sprint-11/REVISAO_CODIGO.md |
| Organização do GitHub | Índice da documentação, README atualizado, exemplo frontend, modelo de PR e política de arquivos/evidências | docs/README.md, README.md e CONTRIBUTING.md |

No GitHub, todos os materiais desta entrega podem ser acessados a partir de:
https://github.com/alvccpj/rota-certa/tree/codex/sprint-11-preparacao-entrega/docs

Os links permanecem vinculados à branch da entrega; após integração, os
mesmos caminhos ficam disponíveis na master. O PDF único está em
`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_11.pdf`.

## Como os materiais foram preparados

O Manual do Usuário foi escrito a partir dos nomes de campos, botões e menus
da aplicação. As telas foram capturadas no sistema executado, com dados de
demonstração. O texto explica o resultado esperado das ações e como resolver
as mensagens comuns, sem exigir conhecimento de API ou banco para a operação diária.

O Manual Técnico foi conferido com os arquivos de configuração, dependências,
roteadores, modelos e serviços. Ele distingue instalação manual, Compose e
demonstração SQLite; descreve variáveis sem incluir uma senha privada real e
explica que o processamento é uma heurística, sem modelo de IA treinado.

A consolidação mantém os identificadores originais dos requisitos e casos de
uso. Os diagramas de arquitetura e classes foram refeitos conforme a implementação.
O MER da Sprint 09 permanece válido e foi conferido contra o banco atual.
Planejamentos antigos, como OSRM e possíveis notificações, são identificados
como decisões históricas ou limites, sem ser apresentados como recursos disponíveis.

## Ambiente e resultados da verificação

Execução em 10/11/2026, em macOS ARM64, Python 3.14.7 e PostgreSQL 17.10,
num cluster separado da base de desenvolvimento. A aplicação usou o schema
descartável `sprint11_testes`, API 8021 e frontend 5191. Os casos de navegador
usaram Chrome/Playwright em português e fuso de Recife. Os registros abaixo
estão em `docs/sprint-11/evidencias`; as capturas, em `docs/sprint-11/assets`.

| Verificação | Resultado | Registro |
| --- | --- | --- |
| Backend SQLite | 159 descobertos, 156 aprovados e 3 dispensados | testes_backend_sqlite.txt |
| Backend PostgreSQL | 159 descobertos, 158 aprovados e 1 dispensado | testes_backend_postgresql.txt |
| Frontend | 55 aprovados, nenhuma falha | testes_frontend.txt |
| Aplicação no navegador | 60 aprovados, nenhuma falha e 1 não executado | casos_de_teste.json e execucao_casos.txt |
| Interface adicional | Sem overflow em 320, 390 e 768 px; ações da tabela acessíveis | interface_rc.json |
| Build de produção | TypeScript e Vite concluídos | build.txt |
| Auditoria npm | Zero vulnerabilidades reportadas na rodada | auditoria_npm.json |
| Banco e contrato | Nove tabelas, 14 FKs sem órfãos e 37 operações sincronizadas | banco_e_contrato.json |
| Backup/restauração | Cópia restaurada em outro banco descartável; estrutura e dados comparados | backup_restauracao.json |
| Configuração Compose | YAML e interpolação validados; containers não reexecutados | compose.txt |
| Organização e links | Proteção do .gitignore, arquivos locais e padrões explícitos conferidos | organizacao_github.json |

No backend, o teste CUDA é dispensado nesta máquina sem NVIDIA; no SQLite,
também são dispensados os dois testes específicos de concorrência PostgreSQL.
No navegador, F16 é o único não executado. Os sete testes novos de backend e
os cinco casos adicionais de CSV já estão incluídos nos totais. O comportamento
CUDA validado na Sprint 09 é histórico, não uma nova execução nesta candidata.

O procedimento de instalação manual foi exercitado no PostgreSQL e as
instruções de backup/restauração foram testadas em dados descartáveis. As
capturas mostram o produto executado, não protótipos. A execução automatizada
não é substituta de um teste de aceitação com pessoa externa ao desenvolvimento.

## Principais correções e melhorias

| Registro | Problema ou necessidade | Ajuste e resultado |
| --- | --- | --- |
| BUG-11 | Resposta externa de geocodificação fora do formato podia causar erro ou coordenadas inválidas no mapa | Validação de estrutura/posição e retorno 503 com orientação para marcar manualmente |
| BUG-12 | O utilitário CSV não neutralizava prefixos de fórmula precedidos por espaços | Regra ampliada, com cinco regressões passando |
| AJ11-01 | Comparador público sem limite de tamanho de entrada | Até 64 rotas, 500 paradas por rota e 12.000 no total; excessos retornam 422 |
| AJ11-02 | Senha de demonstração impressa na inicialização | Mensagens passam a indicar apenas a criação do seed ou o guia de acesso |
| AJ11-03/04 | Roteiros de documentação podiam gravar em pasta histórica por padrão | Destino explícito de catálogo e opção de destino da inspeção |
| AJ11-05/06 | Documentos dispersos e classes antigas de planejamento | Índice vigente, dois manuais completos, consolidação e diagramas atuais |

A revisão detalhada e as reproduções anteriores às correções estão em
`REVISAO_CODIGO.md` e nos arquivos `regressoes_antes_*`. Esses arquivos registram
falhas deliberadamente reproduzidas no código anterior. Os registros finais
`testes_*` e `casos_de_teste.json` não apresentam falhas executadas.

## Organização do repositório

Código permanece em backend/frontend; o DDL, em database; manuais e contratos,
em docs; os geradores e executores, em tools. A raiz identifica projeto, objetivo,
tecnologias, instalação, estrutura e integrantes. Foi incluído exemplo de
configuração do frontend, sem segredo, e revisado o modelo de PR para registrar validação.

Arquivos .env, bases locais, caches, ambientes virtuais, node_modules, builds
e materiais temporários de QA são ignorados. PDFs cumulativos, imagens usadas
na documentação e registros anteriores permanecem como histórico intencional.
O verificador não imprime valores de credenciais e registra seus limites:
ele não examina todo o histórico Git nem todos os possíveis formatos de segredo.

O repositório foi confirmado como público. Os manuais e diagramas podem ser
consultados pela avaliação no GitHub. As alterações devem ser organizadas em
commits de correção e de documentação, com pull request para revisão humana.
Não são atribuídas contribuições fictícias a outros integrantes.

## Pendências e próximos passos

| Pendência | Próximo passo | Coordenação |
| --- | --- | --- |
| Aceitação com usuário externo | Usar o roteiro final do Manual do Usuário, registrar dúvidas e corrigir bloqueios reais | Scrum Master e equipe |
| Revalidação CUDA | Repetir F16 e comparação em máquina NVIDIA, com versões/hardware registrados | Backend e otimização |
| Revisão humana | Conferir os manuais, PDF e PR com outro integrante antes da integração | Equipe |
| Envio no Teams | Anexar somente o PDF cumulativo até 21/11/2026 às 23h59 | Álvaro Jordão |
| Demonstração final | Ensaiar cadastro, atribuição, rota, entrega, relatório e explicação do algoritmo | Toda a equipe |

Continuam os limites de escopo: trajetos geográficos sem trânsito, previsões
sem garantia de janelas, exportação CSV e ausência de notificações externas/GPS
ao vivo. Carga elevada, múltiplos navegadores e combinações de escritas ainda
precisam de homologação específica. A infraestrutura atual não é apresentada
como uma publicação de produção pronta com HTTPS, rate limit e alta disponibilidade.

## Reprodução e entrega

Os comandos completos estão no Manual Técnico. A sequência de verificação é:
suíte SQLite, suíte PostgreSQL com TEST_DATABASE_URL, `npm test`, build,
ambiente isolado da Sprint 11, roteiro de navegador e inspeção de banco/contrato.
O exportador da API e o gerador dos diagramas mantêm as fontes reproduzíveis.

O PDF é produzido por `tools/documentation/build_sprint11_document.py` usando
os documentos e capturas versionados. A capa é atualizada; as páginas 2 a 169
do PDF anterior são preservadas. A Parte XI começa na página 170 e reúne este
registro, os dois manuais completos, a documentação final e a revisão de código.

Após revisar o material, somente o Scrum Master envia o arquivo
`Grupo_04_RotaCerta_Sprints_01_a_11.pdf` na tarefa do Teams. Não é necessário
anexar manuais ou Sprints em arquivos separados.
