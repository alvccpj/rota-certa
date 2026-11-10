# Ensaio da apresentação da versão final

Grupo 04 - RotaCerta | Versão 1.0.0 | Execução em 10/11/2026.

## 1 Natureza do ensaio e resultado

Foi executado um ensaio técnico automatizado no sistema real, com Chrome,
API FastAPI e PostgreSQL, contemplando a sequência operacional de apresentação.
Não houve participação simultânea dos integrantes, gravação de falas ou ensaio
humano cronometrado. Esses itens permanecem pendentes; o registro abaixo comprova
a execução técnica, sem atribuir presença ou aprovação fictícia à equipe.

Resultado: oito etapas aprovadas, pedido #15 entregue por Diego Entregador,
duas rotas geradas com pedidos persistidos e comparação CPU concluída. A execução
técnica levou **9,791 segundos**, sem narração nem pausas de explicação. O roteiro
horizontal reserva **570 segundos (9min30s)**, abaixo do limite de 600 segundos.
A duração final com falas precisa ser medida pela equipe; não é inferida do tempo
automatizado.

Evidências completas: `evidencias/ensaio_tecnico.json` e `evidencias/ensaio_execucao.txt`.
Roteiro reproduzível: `tools/documentation/rehearse_sprint12.py`.

## 2 Preparação efetivamente verificada

Ambiente macOS ARM64, Python 3.14.7, PostgreSQL 17.10, Chrome e Playwright.
Foi criado o schema descartável `sprint120_testes` no cluster local de verificação,
com API na porta 8023 e frontend na 5193. O health confirmou conexão PostgreSQL,
a consulta SQL confirmou o schema e o contrato servido confirmou versão 1.0.0.
O roteiro rejeita outro schema antes de executar alterações.

As contas e os pedidos iniciais vieram do seed de demonstração. Nenhum dado
operacional privado foi usado. Um cliente e um pedido foram cadastrados pela
interface, gravados pela API e consultados novamente. Não foram usados mocks nos
fluxos essenciais. O benchmark utilizou entrada sintética explicitamente
identificada, processada pelo algoritmo real.

O ensaio usa uma base diferente da bateria de 61 casos. Assim, a demonstração
começa com situação previsível sem alterar os registros da verificação principal.

## 3 Sequência técnica executada

| Etapa | Ação executada | Resultado observado |
| --- | --- | --- |
| 01 Ambiente e perfis | Health, OpenAPI, login administrador, painel e usuários | Conexão ativa, versão 1.0.0 e quatro usuários iniciais |
| 02 Cadastro | Criar cliente e pedido pela interface, com peso 2,5 kg e janela futura | Pedido #15 persistido como PENDING |
| 03 Atribuição | Solicitar e confirmar atribuição automática | Pedido #15 ASSIGNED a Diego Entregador |
| 04 Otimização operacional | Gerar rotas sequenciais e mostrar mapa/paradas | Duas rotas reais: 5 paradas/21,307 km e 8 paradas/15,934 km |
| 05 Entrega | Autenticar entregador correto, iniciar rota e confirmar pedido | Pedido #15 DELIVERED, com autor registrado |
| 06 Consultas | Abrir relatório, baixar CSV e consultar histórico | Download CSV gerado; histórico exibido |
| 07 Componente avançado | Executar CPU sequencial e paralela na mesma entrada | Quatro configurações concluídas com igualdade das rotas |
| 08 Enquadramento | Abrir painel em viewport 450 x 800, proporção 9:16 | Sem overflow horizontal; captura para planejamento vertical |

A sequência de situações persistida do pedido #15 foi PENDING → ASSIGNED →
IN_ROUTE → DELIVERED. As durações individuais estão no JSON, medidas por relógio
monotônico. A coleta de erros JavaScript terminou vazia após a correção BUG-13.

![Painel real aberto no início do ensaio técnico, em proporção horizontal 16:9.](assets/ensaio_01_painel.png)

![Pedido criado durante o ensaio técnico, antes da atribuição.](assets/ensaio_02_pedido.png)

![Rotas reais geradas durante o ensaio, com ordenação das paradas e mapa.](assets/ensaio_04_rotas.png)

![Confirmação da entrega do mesmo pedido pelo perfil do entregador.](assets/ensaio_05_entrega.png)

## 4 Comparação de processamento executada

Entrada: 8 rotas x 60 paradas = 480 paradas sintéticas, semente 12, três repetições
por configuração. Os valores abaixo são medianas da execução desta máquina e
não uma previsão de desempenho em outros computadores. O teste foi realizado
via endpoint autenticado e o resultado persistido foi exibido na interface.

| Configuração | Tempo em ms | Speedup |
| --- | --- | --- |
| Sequencial | 4,450 | 1,000 |
| CPU, 1 processo | 4,836 | 0,920 |
| CPU, 2 processos | 2,224 | 2,000 |
| CPU, 4 processos | 2,024 | 2,199 |

Todos os resultados indicaram igualdade das rotas. Um processo paralelo foi mais
lento que o sequencial; isso deve ser explicado, sem prometer ganho universal.
A eficiência é speedup dividido pela quantidade de processos, com arredondamento
e ruído de medição. CUDA não foi executado nesta máquina: não há NVIDIA e o
CuPy não está instalado. O produto pode ser demonstrado com os modos CPU reais.

![Resultados reais da comparação CPU realizada no ensaio.](assets/ensaio_08_desempenho.png)

## 5 Problemas encontrados e resolução

Na preparação do ensaio, o formulário de pedido iniciou uma transição CSS de zoom
do Leaflet e a navegação desmontou o mapa antes do término. O callback acessou
`_leaflet_pos` de um elemento já removido, produzindo erro JavaScript.

O BUG-13 foi isolado em roteiro próprio: dez navegações de pedido e cinco de
rotas. Antes da correção houve dez erros, com stack registrado em
`evidencias/regressao_mapas_antes.json`. Foi desativada a animação CSS de zoom
nos dois componentes de mapa, preservando marcação, zoom, reenquadramento e
paradas. Depois da correção, as mesmas 15 navegações produziram zero erros,
conforme `evidencias/regressao_mapas.json`.

O executor de ensaio também foi ajustado para aceitar o retorno à página anterior
ao autenticar, comportamento previsto da navegação. Isso foi um ajuste do roteiro,
não um defeito de login. Após ambos os ajustes, o ensaio completo passou.
Os casos de navegador, testes frontend e build foram repetidos na versão corrigida.

## 6 Sequência de falas e controle de tempo

A distribuição proposta está no planejamento dos vídeos: Álvaro abre e encerra;
Vinícius explica arquitetura e qualidade; William conduz cadastros; Arthur explica
atribuição, algoritmo e comparação; Guilherme demonstra a entrega. Não se registra
que essas falas já ocorreram. A equipe deve validar a proposta e ensaiar com o
mesmo computador, contas e sequência que serão usados na apresentação.

O roteiro horizontal soma 9min30s. Marcar passagens em 01:30 (arquitetura), 02:30
(cadastro), 04:00 (rotas), 05:30 (entrega), 06:45 (comparação), 08:15 (qualidade)
e 09:00 (encerramento). Uma pessoa opera o cronômetro e sinaliza o limite de fala.
Se ultrapassar dez minutos, reduzir contexto e pausas e repetir o ensaio falado.
O benchmark pode ter duração diferente na máquina final; preparar sua execução
antes de iniciar a fala correspondente e manter o resultado identificado.

## 7 Procedimento para repetir a preparação técnica

Com dependências instaladas, configurar `POSTGRES_URL` para uma base local de
testes conforme o Manual Técnico. O comando abaixo **recria** somente o schema
`sprint120_testes`; não usá-lo sobre dados que precisem ser preservados.

```bash
python tools/run_test_environment.py --schema sprint120_testes --api-port 8023 --web-port 5193
```

Em outro terminal, definir `REHEARSAL_DATABASE_URL` para o mesmo banco e schema,
com driver PostgreSQL nativo, e executar:

```bash
python tools/documentation/rehearse_sprint12.py
```

Exemplo de URL sem senha real: `postgresql://USUARIO:SENHA@HOST:PORTA/BANCO?options=-csearch_path%3Dsprint120_testes`.
O padrão local do executor aponta para o cluster descartável desta verificação;
seu ambiente deve ser configurado explicitamente em outra máquina. Variáveis
`REHEARSAL_API_URL` e `REHEARSAL_APP_URL` permitem indicar os endereços dos serviços.
A consulta SQL de segurança confere o schema; confirme que a API usa essa mesma
base antes de executar. Recriar o ambiente entre repetições evita estado acumulado.

Para repetir a regressão dos mapas, manter o ambiente da bateria principal no
ar e executar `python tools/documentation/verify_map_navigation.py`. O roteiro
preenche coordenadas e navega, sem salvar pedidos.

## 8 Preparação da apresentação com a equipe

1. Reservar a máquina final, verificar energia, rede, navegador e resolução.
2. Fazer checkout da tag v1.0.0 e conferir o manifesto; subir PostgreSQL, API e frontend.
3. Conferir health, contas de demonstração, pedidos e disponibilidade dos entregadores.
4. Ensaiar todos os blocos com os cinco integrantes e registrar o tempo real.
5. Conferir funcionamento do mapa e preparar explicação das dependências externas.
6. Repetir CPU e, somente se disponível, CUDA na máquina que será demonstrada.
7. Gravar os dois formatos e revisar duração, áudio, legendas e marcações.

Se a internet falhar, manter o fluxo com coordenadas conhecidas e explicar que
os tiles externos podem não carregar. Uma captura anterior pode ajudar a explicar
a arquitetura, mas não substitui a demonstração de pedidos, persistência e
algoritmo em execução. Se um serviço local falhar, corrigir a causa e repetir o
ensaio antes da apresentação, sem esconder uma execução interrompida.

## 9 Pendências finais do ensaio

O ensaio humano completo com distribuição de falas, medição final e aprovação dos
integrantes está pendente. Também permanecem aceitação externa e produção dos
vídeos. CUDA só exige nova execução se for apresentado. Esses limites devem ser
confirmados pelo Scrum Master antes da entrega final; esta documentação não
comprova presença ou concordância de pessoas que não participaram da sessão.
