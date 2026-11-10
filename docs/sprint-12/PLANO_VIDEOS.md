# Planejamento dos vídeos da versão final

Grupo 04 - RotaCerta | Versão 1.0.0 | Preparação em 10/11/2026.
O requisito da Sprint 12 permite planejamento ou versão preliminar. Esta entrega
contém roteiro, sequência visual, distribuição proposta, textos e plano de produção
dos dois vídeos. Não há gravação de voz, vídeo final ou publicação no Instagram
realizados em nome da equipe.

## 1 Vídeo horizontal: apresentação completa

Formato 16:9, resolução proposta 1920 x 1080, exportação MP4/H.264, áudio AAC,
30 fps. Duração planejada de 9min30s, com margem de 30s até o limite de 10min.
A leitura deve ser ensaiada em voz alta: o tempo abaixo é orçamento, não medição
de falas realizadas. Os nomes indicam distribuição proposta para validação da equipe.

| Intervalo | Responsável proposto | Conteúdo e ação na tela |
| --- | --- | --- |
| 00:00-00:45 | Álvaro Jordão | Identificar Grupo 04, integrantes e problema dos pequenos negócios |
| 00:45-01:30 | Álvaro Jordão | Explicar solução e perfis; login e painel real |
| 01:30-02:30 | Vinícius Trigueiro | Arquitetura, tecnologias, API e estrutura relacional |
| 02:30-04:00 | William Coelho de Morais | Cadastrar cliente e pedido; endereço, peso, prioridade e janela |
| 04:00-05:30 | Arthur Sales | Atribuir pedidos, gerar rota e explicar vizinho mais próximo + 2-opt |
| 05:30-06:45 | Guilherme de Luna Barros | Perfil entregador: iniciar rota, confirmar entrega e histórico |
| 06:45-08:15 | Arthur Sales | Comparar CPU sequencial/paralela; entrada, mediana, igualdade e limites CUDA |
| 08:15-09:00 | Vinícius Trigueiro | Relatório/CSV, consistência no PostgreSQL e testes da versão final |
| 09:00-09:30 | Álvaro Jordão | Código congelado v1.0.0, limites, aprendizado e encerramento |

## 2 Texto-base e direção do vídeo horizontal

### Abertura e problema - Álvaro

“Somos o Grupo 04 e este é o RotaCerta. Pequenos negócios precisam receber pedidos,
definir quem fará cada entrega e acompanhar o que já foi concluído. Quando essas
informações ficam espalhadas, a operação perde visibilidade e a escolha das rotas
fica mais difícil. Nosso projeto reúne essas tarefas em uma aplicação web.”

Mostrar título e nomes por alguns segundos. Trocar para o sistema executado,
sem deixar a apresentação inteira em slides. Usar apenas dados de demonstração.

### Solução e perfis - Álvaro

“O administrador organiza o negócio e os usuários. O atendente registra e acompanha
pedidos. O entregador visualiza suas entregas e confirma as etapas. Aqui entramos
como administrador e o painel reúne os indicadores da operação. Cada estabelecimento
possui seus próprios dados e o acesso depende do perfil.”

Exibir login brevemente, omitir digitação de senha na edição e mostrar o painel.
Explicar que o cliente final não tem área própria nesta versão.

### Arquitetura e tecnologias - Vinícius

“A interface usa React e TypeScript, com Vite. Ela acessa uma API FastAPI em Python,
que valida as regras e persiste as informações no PostgreSQL usando SQLAlchemy.
O acesso usa token JWT. O modelo possui nove tabelas, incluindo estabelecimentos,
usuários, entregadores, clientes, pedidos, rotas, paradas, histórico e execuções
do otimizador. Os contratos e exemplos estão documentados em OpenAPI.”

Mostrar diagrama de arquitetura e MER em tela inteira, depois `/docs`. Não ler
as 37 operações nem expor variáveis privadas. A figura revisada na Sprint 11
continua válida: não houve mudança de arquitetura na versão final.

### Cadastro e operação - William

“Vamos acompanhar um pedido real de demonstração. Cadastramos o cliente, informamos
endereço e posição no mapa, peso, prioridade e janela desejada. O sistema valida
esses dados antes de salvar. O pedido nasce pendente e já pode ser consultado.”

Preencher um cliente novo, sem reaproveitar o mesmo telefone de uma tentativa
anterior. Cadastrar pedido de 2,5 kg, prioridade alta e janela futura em Recife.
Usar coordenadas locais conferidas; a marcação manual permite demonstrar mesmo
se a geocodificação externa estiver indisponível. Não usar resposta de API mockada.

### Atribuição, rota e algoritmo - Arthur

“A atribuição considera elegibilidade, disponibilidade e capacidade do entregador.
Depois, a roteirização ordena as paradas com vizinho mais próximo e melhora o
percurso usando 2-opt. A rota parte do ponto do estabelecimento e retorna a ele.
A mesma lógica pode executar de forma sequencial ou paralela em CPU.”

Clicar em Atribuir automaticamente e confirmar. Mostrar resumo, gerar rotas e
apontar paradas ordenadas, distância e previsão. Explicar que é uma heurística,
sem garantia de ótimo global. As linhas e distâncias são geográficas aproximadas;
não representam ruas, trânsito ou GPS ao vivo. A janela produz estimativas e
alertas, sem garantia de cumprimento.

### Execução e rastreabilidade - Guilherme

“Agora usamos o perfil de quem recebeu o pedido. O entregador inicia a rota e
confirma a entrega. Ao voltar à consulta, a situação foi atualizada e o histórico
registra quem realizou a ação e quando. Os dados permanecem no banco.”

Abrir uma sessão separada no navegador para o entregador correto, iniciar a rota
e confirmar o mesmo pedido. Não confirmar uma entrega diferente na montagem.
Mostrar a situação Entregue e o evento correspondente no histórico.

### Componente computacional - Arthur

“A comparação executa a mesma entrada nos modos disponíveis e confere se as rotas
coincidem. Medimos o tempo e calculamos speedup como tempo sequencial dividido
pelo tempo paralelo. A eficiência da CPU é esse ganho dividido pelo número de
processos. Um conjunto pequeno pode ser mais lento em paralelo pelo custo de
coordenação. Não prometemos ganho onde a medição não mostrou.”

Mostrar comparação CPU com 8 rotas, 60 paradas por rota, processos 1/2/4 e três
repetições, usando a mediana. Identificar claramente a entrada sintética como
carga de benchmark. O cadastro e as rotas operacionais anteriores usam dados
persistidos. Explicar que o modo CUDA usa CuPy e kernel próprio e exige NVIDIA.
Nesta máquina ARM64, mostrar a indisponibilidade; não apresentar o resultado
histórico da Sprint 09 como nova execução. Se for gravar CUDA, repetir e registrar
na máquina compatível antes da edição.

### Qualidade e encerramento - Vinícius e Álvaro

“Os relatórios permitem consultar a operação e exportar CSV. Conferimos a estrutura
do banco e a leitura dos pedidos pela API e por outra conexão SQL. A entrega reúne
testes de backend, frontend e navegador, incluindo validações e permissões.”

Mostrar relatório e exportação, sem abrir dados privados. Encerrar com:
“A versão final está identificada pela tag v1.0.0, com código congelado para a
apresentação. O repositório contém instruções, manuais e evidências. Este é o
RotaCerta: organização de entregas e comparação de estratégias de processamento.”

## 3 Vídeo vertical: roteiro de divulgação

Formato obrigatório 9:16. Proposta: 1080 x 1920, MP4/H.264, 30 fps e aproximadamente
45 segundos. O enunciado não define duração máxima para este formato. A peça
prioriza leitura rápida e cortes do produto real, com legenda acessível e narração
ou fala gravada por integrante. Música somente própria ou autorizada.

| Tempo | Imagem/corte planejado | Texto e narração sugeridos |
| --- | --- | --- |
| 00-04s | Integrante em cena e título | “Pedido recebido. E agora, quem entrega?” |
| 04-10s | Painel real no celular | “Com o RotaCerta, o pequeno negócio acompanha a operação em um só lugar.” |
| 10-17s | Cadastro e resumo da atribuição | “Cadastre o pedido e distribua conforme a capacidade dos entregadores.” |
| 17-25s | Paradas no mapa e lista | “Organize as paradas com otimização de rotas.” |
| 25-32s | Entregador confirma o pedido | “Da saída à entrega, cada etapa fica registrada.” |
| 32-38s | Comparação CPU identificada | “Também comparamos processamento sequencial e paralelo.” |
| 38-45s | Integrantes, nome e chamada | “RotaCerta. Projeto acadêmico do Grupo 04. Conheça o projeto no GitHub.” |

Texto final em tela e na legenda: **@pryscillabgoncalves @antenorparnaiba**.
Os dois perfis devem ser marcados pela equipe no Instagram, após conferência
no aplicativo. Não houve publicação ou mensagem a terceiros nesta execução.

Legenda pronta para revisão: “Do pedido à entrega: conheça o RotaCerta, projeto
acadêmico do Grupo 04 da UNINASSAU. Gestão de entregas, roteirização e comparação
de processamento em uma aplicação web. @pryscillabgoncalves @antenorparnaiba
#RotaCerta #FabricaDeSoftware #CienciaDaComputacao #UNINASSAU”.

A captura `assets/ensaio_09_vertical.png` possui proporção 9:16 (450 x 800) e
serve para revisar o enquadramento. Ela não substitui um vídeo. Gravar a interface
com viewport vertical, mantendo campos e botões legíveis; evitar apenas recortar
a captura horizontal. Manter legendas longe das áreas cobertas pelos controles
do Instagram e verificar o resultado em um celular.

## 4 Produção, revisão e arquivos

| Etapa | Execução prevista | Situação desta entrega |
| --- | --- | --- |
| Roteiro e divisão | Conferir textos, sequência, vozes e dados de demonstração | Planejamento completo; divisão proposta |
| Pré-produção | Reservar local silencioso, microfone, capturador e máquina final | Depende da equipe |
| Teste técnico | Executar cadastro até entrega e benchmark no ambiente separado | Executado; registro do ensaio técnico |
| Ensaio falado | Todos os integrantes, cronômetro e transições | Pendente de participação humana |
| Captura | Sistema executado, horizontal e vertical, sem credenciais na edição | A realizar pela equipe |
| Edição | Cortes, legendas, títulos, níveis de áudio e créditos | A realizar pela equipe |
| Aprovação | Assistir integralmente; conferir falas, legibilidade e duração | A realizar pela equipe |
| Exportação/publicação | Conferir formatos e marcações | A realizar; nenhuma publicação feita |

Nomes propostos para produção: `Grupo_04_RotaCerta_Apresentacao_16x9.mp4` e
`Grupo_04_RotaCerta_Divulgacao_9x16.mp4`. São nomes planejados, não arquivos
entregues. Guardar gravações brutas fora do Git; incorporar os links finais apenas
após existirem e serem revisados. Somente o PDF cumulativo é o anexo desta Sprint.

Se a gravação horizontal superar 10 minutos, reduzir introduções e pausas,
sem remover o fluxo de entrega ou a explicação da otimização. O roteiro reserva
9min30s; se as ações técnicas demorarem, reduzir falas de contexto e repetir a
gravação completa. Não acelerar a tela a ponto de esconder uma falha.
