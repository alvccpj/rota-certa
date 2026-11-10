# RotaCerta

Sistema web de roteirização de entregas para pequenos negócios locais. Centraliza o cadastro de clientes, pedidos e entregadores e calcula rotas otimizadas (vizinho mais próximo + 2-opt) com execução sequencial, paralela em CPU e acelerada em GPU com CUDA.

Projeto Integrador das disciplinas **Fábrica de Software** e **Tópicos Avançados em Ciência da Computação**, do 8º período do curso de Ciência da Computação da **UNINASSAU**, turma **8NA** (2026.2).

**Grupo 04 | Versão final `1.0.0` | Sprint 12, 10/11/2026.**
O objetivo é organizar a operação de entregas de pequenos negócios: cadastrar
clientes e pedidos, distribuir a carga entre entregadores, planejar trajetos e
acompanhar entregas com histórico e indicadores. A verificação desta versão,
suas evidências e pendências estão em [Sprint 12](docs/sprint-12/README.md).

Para aprender a usar, consulte o [Manual do Usuário](docs/manuais/MANUAL_DO_USUARIO.md).
Para instalar e manter, consulte o [Manual Técnico](docs/manuais/MANUAL_TECNICO.md).
O [índice da documentação](docs/README.md) reúne requisitos, casos de uso,
diagramas finais, regras, APIs e revisão de código.

## Equipe

| Integrante | Matrícula |
| --- | --- |
| Álvaro Jordão | 01748200 |
| Arthur Sales | 01593811 |
| Vinícius Trigueiro | 01794959 |
| William Coelho de Morais | 01263977 |
| Guilherme de Luna Barros | 01615925 |

## Tecnologias

- **Frontend:** React, TypeScript, Vite, React Router e Leaflet (OpenStreetMap)
- **Backend:** Python, FastAPI, SQLAlchemy, JWT e Argon2
- **Banco de dados:** PostgreSQL 16 ou superior (verificado no 17.10 nesta entrega; 18.1 na Sprint 09)
- **Otimização e paralelização:** módulo Python com execução sequencial, paralela em CPU (múltiplos processos) e em GPU com CUDA

## Otimização e paralelização

O núcleo do RotaCerta calcula, para cada entregador, a ordem das entregas que reduz a distância percorrida, usando a heurística do vizinho mais próximo refinada com 2-opt. Esse é o componente de Tópicos Avançados em Ciência da Computação do projeto.

O mesmo cálculo é executado em três modos, para comparar o desempenho sobre a mesma entrada:

| Modo | Como executa | Situação |
| --- | --- | --- |
| Sequencial | Um processo calcula todas as rotas, uma depois da outra. É a linha de base. | Implementado |
| Paralelo em CPU | As rotas dos entregadores são distribuídas entre vários processos. | Implementado |
| Paralelo em GPU (CUDA) | Um kernel CUDA resolve todas as rotas de uma vez, com um bloco de 256 threads por entregador: as threads dividem a matriz de distâncias, a busca do vizinho mais próximo e a avaliação das trocas do 2-opt. | Implementado |

Os três modos usam a mesma matriz de distâncias e o mesmo critério de desempate, então chegam exatamente às mesmas rotas: a comparação mede só a forma de execução. Ela mostra o tempo de execução, o speedup (tempo sequencial dividido pelo tempo do modo) e a eficiência (speedup dividido pelo número de processos). Cada execução fica registrada na tabela `optimization_runs` e aparece na tela **Desempenho**.

O modo CUDA exige uma GPU NVIDIA e o CuPy (`backend/requirements-gpu.txt`). Em máquinas sem GPU, o sistema continua funcionando com os modos sequencial e paralelo em CPU. O código do otimizador está em [`backend/app/optimizer`](backend/app/optimizer).

## Módulos

| Módulo | Sprint | O que faz |
| --- | --- | --- |
| Pedidos e entregas | 04 | Clientes, pedidos com local no mapa, atribuição por disponibilidade, capacidade e raio, histórico de situação e entregas pelo celular |
| Roteirização e desempenho | 05 | Rotas otimizadas a partir dos pedidos atribuídos, mapa com o trajeto de cada entregador, início e conclusão da rota pelo entregador e comparação sequencial, paralela e GPU |
| Painel operacional e relatórios | 06 | Indicadores integrados de pedidos, entregadores, rotas e desempenho, filtros por período, alertas operacionais, ações rápidas e relatório CSV |
| Consultas e rastreabilidade | 07 | Relatórios pesquisáveis com filtros combináveis, exportação CSV do resultado e histórico cronológico de pedidos e execuções do otimizador |
| Consolidação funcional | 08 | Atribuição automática, espera e avisos de atraso, revisão de permissões e proteção de dados das rotas |
| Testes e correções | 09 | 61 casos de teste funcionais, de validação e de navegação na aplicação real, 9 bugs corrigidos com testes de regressão, suíte do backend também no PostgreSQL e documentação técnica atualizada ([Sprint 09](docs/sprint-09/README.md)) |
| Release Candidate | 10 | Revisão dos fluxos e da interface, ensaio de atribuição concorrente em PostgreSQL, contrato OpenAPI exportado, catálogo de endpoints e documento cumulativo ([Sprint 10](docs/sprint-10/README.md)) |
| Versão final | 12 | Congelamento 1.0.0, nova verificação, roteiro dos vídeos e ensaio técnico ([Sprint 12](docs/sprint-12/README.md)) |
| Preparação para entrega | 11 | Manuais do usuário e técnico, documentação final consolidada, revisão de código com correções e organização do repositório ([Sprint 11](docs/sprint-11/README.md)) |

## Como interpretar as rotas

O mapa mostra a sequência de paradas; as distâncias são geográficas (Haversine),
sem considerar ruas ou trânsito. Os horários estimados usam velocidade média e
tempo de atendimento configurados. Prioridade e janela de entrega orientam a
equipe. A atribuição automática prioriza urgência e prazo; o agendamento inclui
espera até a janela e sinaliza atrasos. A ordem das paradas otimiza distância,
sem garantia de cumprimento de todas as janelas. Veja o escopo final em [Sprint 08](docs/sprint-08/README.md)
e a verificação completa em [Sprint 09](docs/sprint-09/README.md).

Depois de gerar rotas, a tela compara a distância na ordem original dos pedidos
(por ID), após o vizinho mais próximo e após o 2-opt, incluindo o retorno ao
ponto de saída. Essa comparação considera apenas os pedidos da geração atual,
fica visível até sair da página e é calculada fora da medição de desempenho.
A heurística não garante o ótimo global nem melhoria sobre toda ordem original.

O cancelamento exige motivo com pelo menos cinco caracteres após normalizar
espaços. Ao editar pedidos, uma nova janela não pode terminar no passado;
preservar a janela antiga permite corrigir outros dados de um pedido atrasado.

## Como rodar localmente

### Requisitos e instalação

- Git; Python 3.12 ou superior; Node.js 20.19+ ou 22.12+; PostgreSQL 16+.
- Docker com Compose é uma alternativa à instalação manual.
- GPU NVIDIA/CUDA é opcional. Sem ela, use os modos sequencial e paralelo em CPU.

Com Docker, na raiz do repositório:

```bash
git clone https://github.com/alvccpj/rota-certa.git
cd rota-certa
cp .env.example .env
docker compose up --build
```

O Compose cria o banco e aplica `database/schema.sql` na primeira inicialização.
Abra `http://localhost:5173`; API em `http://localhost:8000`, Swagger em
`http://localhost:8000/docs`. Confirme `database: connected` em `/health`.
Se a porta 5432 já estiver ocupada, configure `POSTGRES_PORT=5433` no `.env`.

Sem Docker (Bash no macOS/Linux; versão Windows em [COMO-RODAR](COMO-RODAR.md)):

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
npm ci --prefix frontend
cp backend/.env.example backend/.env
```

No PostgreSQL, conectado como um usuário administrador, execute separadamente:

```sql
CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';
CREATE DATABASE rotacerta OWNER rotacerta;
```

Em `backend/.env`, ajuste `DATABASE_URL` para o banco criado, por exemplo
`postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta`.
Na primeira inicialização a API cria as nove tabelas e, com `SEED_DEMO_DATA=true`,
os dados de exemplo. Bancos de versões anteriores recebem as atualizações
incrementais descritas em [database/README.md](database/README.md).

Execute em dois terminais:

```bash
# Terminal 1, com o ambiente virtual ativado
cd backend
uvicorn app.main:app --reload
```

```bash
# Terminal 2, a partir da raiz
cd frontend
npm run dev
```

Login de demonstração: `admin@rotacerta.com.br`, `atendente@rotacerta.com.br` ou
`entregador@rotacerta.com.br`; senha `rotacerta123`. `JWT_SECRET` configura a chave
de autenticação e `CORS_ORIGINS` os endereços aceitos pelo backend;
`VITE_API_URL` configura o endereço da API no frontend.

### Verificar a versão

Na raiz, com o ambiente virtual ativado:

```bash
python -m unittest discover backend/tests -v
npm test --prefix frontend
npm run build --prefix frontend
```

Para validar concorrência e o DDL real, execute também a suíte com
`TEST_DATABASE_URL` apontando para PostgreSQL. Ela recria somente o schema
descartável `rotacerta_testes_automatizados`. Passo a passo e roteiro de navegador
em [Sprint 12](docs/sprint-12/README.md). Dependências opcionais do roteiro:
`pip install -r backend/requirements-docs.txt` e Google Chrome instalado.

### Estrutura do projeto

```text
backend/app/             API, modelos, regras, autenticação e serviços
backend/app/routers/     Endpoints por módulo
backend/app/optimizer/   Algoritmos sequencial, CPU paralela e GPU
backend/tests/           Testes automatizados de API e regras
frontend/src/pages/     Telas React
frontend/src/components/ Componentes e navegação
database/               DDL PostgreSQL e orientações
docs/api/               Guia, catálogo de endpoints e OpenAPI
docs/sprint-*/          Registros e evidências por sprint
tools/                  Execução local e geração de evidências/documentos
output/pdf/             PDFs cumulativos para entrega
```

### Regras de operação e acompanhamento

- Desativar um entregador ou retirar seu perfil exige resolver os pedidos atribuídos
  e em rota. Tanto a edição quanto a desativação aplicam a mesma regra; a tela de
  usuários mostra links para os pedidos ativos. Colocar fora de serviço é bloqueado
  enquanto houver pedidos em rota.
- Administrador e atendente seguem as etapas Pendente → Atribuído → Em rota →
  Entregue. Podem cancelar pedidos abertos e reabrir os encerrados como pendentes,
  sem entregador, desde que não pertençam a uma rota já iniciada. Nessa situação,
  uma nova entrega exige novo pedido para preservar o histórico. Atribuídos também podem voltar a pendentes. Entregadores apenas
  avançam de Atribuído para Em rota e de Em rota para Entregue.
- As listas Pedidos e Minhas entregas consultam novamente a API a cada 15 segundos,
  apenas com a aba visível, e ao retornar à aba. Os filtros são preservados e a hora
  da última consulta bem-sucedida é exibida. Não há necessidade de WebSockets.

O passo a passo completo está em **[COMO-RODAR.md](COMO-RODAR.md)**. Ele traz os comandos para PowerShell e Git Bash, cada um com um comentário explicando o que faz, e cobre:

- execução com Docker ou sem Docker;
- criação do usuário e do banco no PostgreSQL;
- como subir a API e o frontend;
- contas de demonstração e endereços de acesso;
- consulta aos dados no banco;
- testes automatizados;
- erros comuns e como resolvê-los.

## Versão final e Code Freeze

A versão estável de apresentação é a tag [`v1.0.0`](https://github.com/alvccpj/rota-certa/tree/v1.0.0).
Para reproduzir o código congelado: `git fetch --tags` e `git switch --detach v1.0.0`.
Confira a integridade com `python tools/documentation/verify_code_freeze.py`.
Novas funcionalidades ficam fora desta entrega. O procedimento de correção crítica,
validações, limites conhecidos, roteiros dos vídeos e ensaio técnico estão na
[Sprint 12](docs/sprint-12/README.md) e no [registro de congelamento](docs/sprint-12/CODE_FREEZE.md).
O ensaio técnico foi automatizado; falas da equipe, gravação e aceitação humana
precisam ser realizadas pelos integrantes. A GPU CUDA depende de hardware NVIDIA.

## Documentação

- Documento cumulativo das Sprints: [`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_12.pdf`](output/pdf/Grupo_04_RotaCerta_Sprints_01_a_12.pdf)
- Versão final, verificações e pendências: [`docs/sprint-12/README.md`](docs/sprint-12/README.md)
- Manuais, requisitos e documentação final: [`docs/README.md`](docs/README.md)
- APIs (autenticação, exemplos, rotas e modelos): [`docs/api/README.md`](docs/api/README.md)
- Arquitetura, classes e modelo de dados atuais: [`docs/final/DOCUMENTACAO_FINAL.md`](docs/final/DOCUMENTACAO_FINAL.md)
- Casos de teste e registro de bugs: [`docs/sprint-09/README.md`](docs/sprint-09/README.md)
- Documento de abertura (Sprint 1): [`RotaCerta_Documento_Abertura_Sprint1.pdf`](RotaCerta_Documento_Abertura_Sprint1.pdf)
- Evidências por Sprint: [`docs/`](docs/)
- Como rodar localmente: [`COMO-RODAR.md`](COMO-RODAR.md)
- Banco de dados: [`database/README.md`](database/README.md)
- Guia de contribuição: [`CONTRIBUTING.md`](CONTRIBUTING.md)
