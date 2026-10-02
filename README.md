# RotaCerta

Sistema web de roteirização de entregas para pequenos negócios locais. Centraliza o cadastro de clientes, pedidos e entregadores e calcula rotas otimizadas (vizinho mais próximo + 2-opt) com execução sequencial, paralela em CPU e acelerada em GPU com CUDA.

Projeto Integrador das disciplinas **Fábrica de Software** e **Tópicos Avançados em Ciência da Computação**, do 8º período do curso de Ciência da Computação da **UNINASSAU**, turma **8NA** (2026.2).

## Equipe

| Integrante | Matrícula |
| --- | --- |
| Álvaro Jordão | 01748200 |
| Arthur Sales | 01593811 |
| Vinícius Trigueiro | 01794959 |
| William Coelho de Morais | 01263977 |

## Tecnologias

- **Frontend:** React, TypeScript, Vite, React Router e Leaflet (OpenStreetMap)
- **Backend:** Python, FastAPI, SQLAlchemy, JWT e Argon2
- **Banco de dados:** PostgreSQL 16
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

## Como rodar localmente

O passo a passo completo está em **[COMO-RODAR.md](COMO-RODAR.md)**. Ele traz os comandos para PowerShell e Git Bash, cada um com um comentário explicando o que faz, e cobre:

- execução com Docker ou sem Docker;
- criação do usuário e do banco no PostgreSQL;
- como subir a API e o frontend;
- contas de demonstração e endereços de acesso;
- consulta aos dados no banco;
- testes automatizados;
- erros comuns e como resolvê-los.

## Documentação

- Documento cumulativo das Sprints: [`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_05.pdf`](output/pdf/Grupo_04_RotaCerta_Sprints_01_a_05.pdf)
- Documento de abertura (Sprint 1): [`RotaCerta_Documento_Abertura_Sprint1.pdf`](RotaCerta_Documento_Abertura_Sprint1.pdf)
- Evidências por Sprint: [`docs/`](docs/)
- Como rodar localmente: [`COMO-RODAR.md`](COMO-RODAR.md)
- Banco de dados: [`database/README.md`](database/README.md)
- Guia de contribuição: [`CONTRIBUTING.md`](CONTRIBUTING.md)
