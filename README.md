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
| Guilherme de Luna Barros | 01615925 |

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
| Painel operacional e relatórios | 06 | Indicadores integrados de pedidos, entregadores, rotas e desempenho, filtros por período, alertas operacionais, ações rápidas e relatório CSV |
| Consultas e rastreabilidade | 07 | Relatórios pesquisáveis com filtros combináveis, exportação CSV do resultado e histórico cronológico de pedidos e execuções do otimizador |

## Como interpretar as rotas

O mapa mostra a sequência de paradas; as distâncias são geográficas (Haversine),
sem considerar ruas ou trânsito. Os horários estimados usam velocidade média e
tempo de atendimento configurados. Prioridade e janela de entrega orientam a
equipe, mas ainda não são restrições do algoritmo.

Depois de gerar rotas, a tela compara a distância na ordem original dos pedidos
(por ID), após o vizinho mais próximo e após o 2-opt, incluindo o retorno ao
ponto de saída. Essa comparação considera apenas os pedidos da geração atual,
fica visível até sair da página e é calculada fora da medição de desempenho.
A heurística não garante o ótimo global nem melhoria sobre toda ordem original.

O cancelamento exige motivo com pelo menos cinco caracteres após normalizar
espaços. Ao editar pedidos, uma nova janela não pode terminar no passado;
preservar a janela antiga permite corrigir outros dados de um pedido atrasado.

## Como rodar localmente

### Regras de operação e acompanhamento

- Desativar um entregador ou retirar seu perfil exige resolver os pedidos atribuídos
  e em rota. Tanto a edição quanto a desativação aplicam a mesma regra; a tela de
  usuários mostra links para os pedidos ativos. Colocar fora de serviço é bloqueado
  enquanto houver pedidos em rota.
- Administrador e atendente seguem as etapas Pendente → Atribuído → Em rota →
  Entregue. Podem cancelar pedidos abertos e reabrir os encerrados como pendentes,
  sem entregador. Atribuídos também podem voltar a pendentes. Entregadores apenas
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

## Documentação

- Documento cumulativo das Sprints: [`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_07.pdf`](output/pdf/Grupo_04_RotaCerta_Sprints_01_a_07.pdf)
- Documento de abertura (Sprint 1): [`RotaCerta_Documento_Abertura_Sprint1.pdf`](RotaCerta_Documento_Abertura_Sprint1.pdf)
- Evidências por Sprint: [`docs/`](docs/)
- Como rodar localmente: [`COMO-RODAR.md`](COMO-RODAR.md)
- Banco de dados: [`database/README.md`](database/README.md)
- Guia de contribuição: [`CONTRIBUTING.md`](CONTRIBUTING.md)
