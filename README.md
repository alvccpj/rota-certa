# RotaCerta

Sistema inteligente de roteirização de entregas para pequenos negócios locais.

Projeto Integrador das disciplinas **Fábrica de Software** e **Tópicos Avançados em Ciência da Computação**, desenvolvido pela turma 8NA da UNINASSAU no semestre 2026.2.

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
- [x] Plano de comparação sequencial e paralela definido

## 1. Formação da equipe

| Integrante | Matrícula | Responsabilidade sugerida |
| --- | --- | --- |
| Álvaro Jordão | 01748200 | Scrum Master e Product Owner: organização das entregas, levantamento e priorização de requisitos e articulação com as orientações |
| Arthur Sales | 01593811 | Desenvolvimento backend e núcleo de otimização/paralelização |
| Vinícius Trigueiro | 01794959 | Desenvolvimento frontend, banco de dados e documentação |

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

## Arquitetura inicial

- **Frontend:** React, TypeScript e Vite.
- **Backend:** FastAPI em Python, com API REST documentada por OpenAPI.
- **Banco de dados:** PostgreSQL 16, inicializado por `database/schema.sql`.
- **Otimização:** módulo Python isolado para vizinho mais próximo, 2-opt e execução paralela.
- **Execução local:** Docker Compose para frontend, API e banco.

Copie `.env.example` para `.env` e execute `docker compose up --build`. A API disponibiliza o endpoint de verificação em `http://localhost:8000/health` e a documentação em `http://localhost:8000/docs`.
