# RotaCerta

Sistema inteligente de roteirização de entregas para pequenos negócios locais.

Projeto Integrador das disciplinas **Fábrica de Software** e **Tópicos Avançados em Ciência da Computação**

## Status da Sprint 1

Período concluído: **03/09/2026 a 05/09/2026**.

- [x] Formação da equipe
- [x] Escolha do tema
- [x] Definição do problema
- [x] Objetivos do sistema
- [x] Público-alvo
- [x] Requisitos funcionais e não funcionais
- [x] Casos de uso iniciais
- [x] Product Backlog inicial
- [x] Cronograma inicial
- [x] Repositório GitHub criado

O documento oficial da entrega está disponível em [Documento de Abertura - Sprint 1](./RotaCerta_Documento_Abertura_Sprint1.pdf).

## Status da Sprint 2

Prazo informado pela professora: **19/09/2026**.

- [x] Arquitetura definida
- [x] Diagrama de classes elaborado
- [x] Modelo Entidade-Relacionamento elaborado
- [x] Modelo relacional definido
- [x] Protótipos das telas principais elaborados
- [x] Estrutura inicial do banco implementada
- [x] Projeto organizado em branch própria no GitHub
- [x] Cronograma corrigido para cadência semanal
- [x] Primeira versão do motor sequencial e paralelo implementada e testada

## Status da Sprint 3

Entrega: **estrutura inicial funcionando**.

- [x] Banco de dados PostgreSQL conectado à API (SQLAlchemy + psycopg)
- [x] Login funcional com token JWT e senhas armazenadas com hash Argon2
- [x] Cadastro de usuários pelo administrador e cadastro de novo estabelecimento
- [x] Controle de perfis: administrador, atendente e entregador
- [x] CRUD principal de pedidos persistido no banco
- [x] Execução local com Docker Compose ou sem Docker
- [x] 21 testes automatizados (16 da API e 5 do otimizador)

## Status da Sprint 4

Entrega: **primeiro módulo completo, Pedidos e entregas**.

- [x] Cadastro de clientes com telefone validado e último endereço de entrega
- [x] Busca de endereço pelo OpenStreetMap e marcação do local no mapa
- [x] Atribuição respeitando disponibilidade, capacidade de carga e raio de entrega
- [x] Histórico de cada mudança de situação do pedido (tabela `order_status_history`)
- [x] Entregador informa a própria disponibilidade e conclui as entregas pelo celular
- [x] Validações na interface e na API, com mensagens junto a cada campo
- [x] Navegação por URL com React Router, rotas protegidas por perfil e páginas de acesso negado e inexistente
- [x] Persistência demonstrada desligando e religando o banco e a API
- [x] 48 testes automatizados (43 da API e 5 do otimizador)

## Como executar

### Opção 1: Docker Compose

Requer o [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env        # no PowerShell: copy .env.example .env
docker compose up --build
```

Se já existir um PostgreSQL instalado usando a porta 5432, altere `POSTGRES_PORT` no `.env` para `5433`.

### Opção 2: sem Docker

Requer Python 3.12 ou superior, Node.js 20 ou superior e um PostgreSQL 16 ou superior instalado.

1. Crie o usuário e o banco no PostgreSQL (pelo pgAdmin ou pelo `psql` com o usuário `postgres`):

   ```sql
   CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';
   CREATE DATABASE rotacerta OWNER rotacerta;
   ```

2. Suba a API. Na primeira execução ela cria as tabelas a partir de `database/schema.sql` e cadastra os dados de demonstração.

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   Para usar outra porta, usuário ou senha do banco, copie `backend/.env.example` para `backend/.env` e ajuste `DATABASE_URL`.

3. Em outro terminal, suba o frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

### Endereços

| Serviço | Endereço |
| --- | --- |
| Sistema | http://localhost:5173 |
| Documentação interativa da API | http://localhost:8000/docs |
| Verificação da API e do banco | http://localhost:8000/health |

### Contas de demonstração

Todas usam a senha `rotacerta123`.

| Perfil | E-mail | Pode fazer |
| --- | --- | --- |
| Administrador | admin@rotacerta.com.br | Gerencia usuários e pedidos, inclusive exclusões |
| Atendente | atendente@rotacerta.com.br | Cadastra, edita e acompanha pedidos |
| Entregador | entregador@rotacerta.com.br | Vê só as próprias entregas e atualiza o andamento |

### Testes

```bash
pip install -r backend/requirements-dev.txt
python -m unittest discover backend/tests -v
```

### Documento da entrega

O documento cumulativo das Sprints 01 a 04 está em `output/pdf/Grupo_04_RotaCerta_Sprints_01_a_04.pdf` (e em `.docx` na pasta `output/docx`). Para regenerá-lo, com o sistema rodando sobre um banco recém-criado e o Google Chrome instalado:

```bash
pip install playwright httpx "psycopg[binary]" python-docx
python tools/documentation/capture_sprint04_evidence.py fluxo      # sistema no ar
python tools/documentation/capture_sprint04_evidence.py sem-api    # depois de desligar API e banco
python tools/documentation/capture_sprint04_evidence.py reinicio   # depois de religar API e banco
python tools/documentation/build_document.py                        # HTML, PDF e DOCX em output/
```

As evidências da Sprint 03 ficam em `docs/sprint-03` e foram geradas por `capture_sprint03_evidence.py`, que trabalha com a versão da API daquela Sprint.

## 1. Formação da equipe

| Integrante | Matrícula | Responsabilidade sugerida |
| --- | --- | --- |
| Álvaro Jordão | 01748200 | Scrum Master e Product Owner: organização das entregas, levantamento e priorização de requisitos e articulação com as orientações |
| Arthur Sales | 01593811 | Desenvolvimento backend e núcleo de otimização/paralelização |
| Vinícius Trigueiro | 01794959 | Desenvolvimento frontend, banco de dados e documentação |
| William Coelho de Morais | 01263977 | Desenvolvimento e testes |

As responsabilidades servem para organizar o trabalho. Todos os integrantes participam do desenvolvimento do sistema como um todo.

## 2. Escolha do tema

**Área:** logística e otimização de processos.

O projeto propõe um sistema web de apoio à roteirização de entregas para pequenos negócios locais, integrando práticas de engenharia de software com otimização computacional e processamento paralelo.

## 3. Definição do problema

Pequenos negócios que realizam suas próprias entregas, como farmácias, mercados, restaurantes e pequenas distribuidoras, normalmente planejam as rotas de forma manual e empírica. A ausência de uma ferramenta de apoio à decisão pode produzir trajetos maiores que o necessário, aumentar custos e causar atrasos.

O problema é relevante porque:

- aumenta os custos com combustível e tempo de trabalho dos entregadores;
- gera atrasos e insatisfação dos clientes;
- dificulta a expansão da operação quando o volume de pedidos cresce;
- soluções profissionais existentes costumam ter custo e complexidade incompatíveis com pequenos negócios.

## 4. Objetivos do sistema

### Objetivo geral

Desenvolver um sistema web que otimize a distribuição de pedidos entre entregadores e determine automaticamente, para cada entregador, uma sequência de entregas que reduza a distância e o tempo total percorrido.

### Resultados esperados

- Reduzir de forma mensurável a distância e o tempo das rotas em comparação com a alocação manual.
- Centralizar o cadastro e o acompanhamento de pedidos e entregadores.
- Calcular rotas para múltiplos entregadores com eficiência e processamento paralelo.
- Oferecer uma interface simples para administradores, atendentes e entregadores em campo.

## 5. Público-alvo

- Pequenos negócios com operação própria de entrega, incluindo farmácias, mercados, restaurantes e pequenas distribuidoras.
- Administradores responsáveis pela operação do negócio.
- Atendentes e operadores responsáveis pelo cadastro dos pedidos.
- Entregadores que consultam e executam as rotas geradas.
- Clientes finais, beneficiados indiretamente por entregas mais rápidas e previsíveis.

## 6. Requisitos funcionais

| ID | Descrição |
| --- | --- |
| RF01 | Cadastrar e autenticar usuários com os perfis administrador, entregador e atendente. |
| RF02 | Cadastrar pedidos com cliente, endereço, prioridade e horário desejado. |
| RF03 | Cadastrar entregadores com disponibilidade e capacidade de carga. |
| RF04 | Gerar automaticamente uma rota otimizada para cada entregador. |
| RF05 | Atribuir pedidos a entregadores de forma manual ou automática. |
| RF06 | Exibir a rota gerada como lista ordenada de paradas e/ou mapa. |
| RF07 | Atualizar o status do pedido entre pendente, em rota e entregue. |
| RF08 | Manter o histórico das entregas realizadas. |
| RF09 | Gerar relatórios de desempenho com tempo médio, distância percorrida e comparação antes/depois da otimização. |
| RF10 | Disponibilizar um painel administrativo com a visão geral das operações do dia. |

## 7. Requisitos não funcionais

| ID | Descrição |
| --- | --- |
| RNF01 | **Desempenho:** calcular rotas em tempo aceitável para múltiplos entregadores simultâneos, utilizando processamento paralelo. |
| RNF02 | **Segurança:** autenticar usuários, controlar o acesso por perfil e armazenar senhas com hash seguro. |
| RNF03 | **Usabilidade:** fornecer uma interface simples e intuitiva, inclusive para entregadores com baixo letramento técnico. |
| RNF04 | **Portabilidade:** funcionar em navegadores e possuir layout responsivo para celulares. |
| RNF05 | **Escalabilidade:** suportar o aumento da quantidade de pedidos e entregadores sem degradação significativa. |
| RNF06 | **Confiabilidade:** persistir pedidos e rotas de forma consistente, sem perda de informações. |
| RNF07 | **Manutenibilidade:** manter o código organizado, documentado e versionado no GitHub. |

## 8. Casos de uso iniciais

| ID | Ator | Caso de uso |
| --- | --- | --- |
| UC01 | Atendente / Administrador | Cadastrar um pedido no sistema. |
| UC02 | Administrador | Cadastrar um entregador. |
| UC03 | Administrador | Solicitar a geração de rotas otimizadas para os pedidos do dia. |
| UC04 | Entregador | Visualizar a rota do dia designada a ele. |
| UC05 | Entregador | Atualizar o status de uma entrega. |
| UC06 | Administrador | Consultar o relatório de desempenho das rotas. |
| UC07 | Todos os perfis | Autenticar-se no sistema. |

Os fluxos principais e alternativos, as pré-condições e as pós-condições serão detalhados nas próximas sprints.

## 9. Product Backlog inicial

### Alta prioridade

- Autenticação e controle de acesso por perfil.
- CRUD de pedidos.
- CRUD de entregadores.
- Modelagem e implementação do banco de dados.
- Motor sequencial de otimização de rotas utilizando vizinho mais próximo e 2-opt.

### Média prioridade

- Visualização da rota como lista ordenada e/ou mapa.
- Atualização do status das entregas.
- Paralelização do motor de otimização com multiprocessing ou joblib.

### Baixa prioridade e evolução

- Relatórios de desempenho e comparação antes/depois da otimização.
- Painel administrativo com métricas consolidadas.
- Evolução do núcleo de otimização para C++/OpenMP ou CUDA.
- Notificações para entregadores e clientes.

## 10. Cronograma inicial

| Sprint | Período previsto | Principais entregas |
| --- | --- | --- |
| Sprint 1 | 03/09 a 05/09 | Formação da equipe, tema, problema, requisitos e backlog inicial. |
| Sprint 2 | 06/09 a 19/09 | Arquitetura, classes, MER, modelo relacional, protótipos, banco inicial e estrutura do projeto. Prazo excepcional devido à liberação tardia. |
| Sprint 3 | 20/09 a 26/09 | Ambiente executável, contrato inicial da API e integração frontend/backend. |
| Sprint 4 | 27/09 a 03/10 | Autenticação, hash de senha e autorização por perfil. |
| Sprint 5 | 04/10 a 10/10 | CRUD de clientes e pedidos. |
| Sprint 6 | 11/10 a 17/10 | CRUD de entregadores, disponibilidade e capacidade. |
| Sprint 7 | 18/10 a 24/10 | Atribuição de pedidos e visualização inicial das rotas. |
| Sprint 8 | 25/10 a 31/10 | Algoritmo sequencial de vizinho mais próximo. |
| Sprint 9 | 01/11 a 07/11 | Refinamento 2-opt e coleta da linha de base. |
| Sprint 10 | 08/11 a 14/11 | Paralelização do cálculo para múltiplos entregadores. |
| Sprint 11 | 15/11 a 21/11 | Experimentos e comparação sequencial versus paralela. |
| Sprint 12 | 22/11 a 28/11 | Relatórios, testes, usabilidade e documentação. |
| Sprint Final | 29/11 a 05/12 | Correções finais, vídeos e preparação para a banca. |

## 11. Repositório

Repositório oficial: [github.com/alvccpj/rota-certa](https://github.com/alvccpj/rota-certa)

O projeto será mantido atualizado ao longo das sprints, com código, documentação e histórico de evolução versionados no GitHub.

## Arquitetura

- **Frontend:** React, TypeScript e Vite; navegação com React Router; mapa com Leaflet e OpenStreetMap.
- **Busca de endereço:** Nominatim (OpenStreetMap), consultado pela API.
- **Backend:** FastAPI em Python, com API REST documentada por OpenAPI.
- **Autenticação:** token JWT, senhas com hash Argon2 e autorização por perfil em cada rota.
- **Banco de dados:** PostgreSQL 16, estrutura em `database/schema.sql`, acesso via SQLAlchemy.
- **Otimização:** módulo Python isolado para vizinho mais próximo, 2-opt e execução paralela.
- **Execução local:** Docker Compose para frontend, API e banco, ou execução manual.

### Endpoints principais

| Método e rota | Perfis | Função |
| --- | --- | --- |
| `POST /auth/login` | Público | Autentica e devolve o token |
| `POST /auth/register` | Público | Cadastra um estabelecimento e o seu administrador |
| `GET /auth/me` | Todos | Dados do usuário logado |
| `GET/POST /users`, `GET/PUT/DELETE /users/{id}` | Administrador | Cadastro, edição e desativação de usuários |
| `GET /couriers` | Administrador, atendente | Entregadores ativos com a carga atual de cada um |
| `PATCH /couriers/me/availability` | Entregador | Informa se está disponível ou fora de serviço |
| `GET/POST /customers`, `GET/PUT /customers/{id}` | Administrador, atendente | Cadastro e busca de clientes |
| `DELETE /customers/{id}` | Administrador | Exclusão de cliente sem pedidos |
| `GET /geocode?q=` | Administrador, atendente | Sugestões de endereço com coordenadas |
| `GET /orders`, `GET /orders/{id}` | Todos | Pedidos do estabelecimento; o detalhe inclui o histórico; o entregador vê só os seus |
| `POST /orders`, `PUT /orders/{id}` | Administrador, atendente | Cadastro e edição de pedidos, com as regras de atribuição |
| `PATCH /orders/{id}/status` | Todos | Andamento com observação; o entregador só avança Atribuído, Em rota e Entregue |
| `DELETE /orders/{id}` | Administrador | Exclusão de pedido |
| `GET /health` | Público | Situação da API e da conexão com o banco |
| `POST /optimizer/compare` | Público | Comparação sequencial e paralela do otimizador |

## Componente computacional avançado

O RotaCerta atende à integração com Tópicos Avançados por meio de otimização de
processamento e paralelização. A proposta não depende de adicionar uma
funcionalidade superficial de inteligência artificial. Python foi escolhido
porque é uma das linguagens prioritárias indicadas para o núcleo computacional
e permite manter a API e os experimentos reproduzíveis no mesmo ambiente.

O endpoint `POST /optimizer/compare` executa vizinho mais próximo e 2-opt nos
modos sequencial e paralelo sobre a mesma entrada. A resposta informa rotas,
distâncias, tempos, workers, speedup e se os dois modos produziram as mesmas
rotas.

Execute os testes do núcleo de otimização na raiz do projeto:

```bash
python -m unittest discover backend/tests -v
```

A implementação inicial possui cinco testes automatizados. As próximas sprints
ampliarão os cenários, persistirão as medições em `optimization_runs` e
integrarão os resultados às telas do sistema.
