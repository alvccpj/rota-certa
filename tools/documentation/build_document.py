"""Gera o documento técnico cumulativo das Sprints 01 a 03.

O mesmo conteúdo é renderizado em HTML, PDF (Chrome headless via Playwright) e
DOCX (python-docx). As evidências da Sprint 03 são produzidas antes por
capture_sprint03_evidence.py com o sistema em execução.

    python tools/documentation/build_document.py
"""

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Inches, Pt

from build_sprint02_document import (
    GRAY,
    add_body,
    add_bullets,
    add_heading,
    add_numbered,
    add_table,
    set_cell_margins,
    set_cell_shading,
    set_font,
    set_table_borders,
    setup_document,
)

ROOT = Path(__file__).resolve().parents[2]
SPRINT02 = ROOT / "docs" / "sprint-02" / "assets"
SPRINT03 = ROOT / "docs" / "sprint-03" / "assets"
EVIDENCE = ROOT / "docs" / "sprint-03" / "evidencias"
NAME = "Grupo_04_RotaCerta_Sprints_01_a_03"
TITLE = "Documento Técnico Cumulativo das Sprints 01 a 03"
REPOSITORY = "https://github.com/alvccpj/rota-certa"
TEAM = (
    ("Álvaro Jordão", "01748200"),
    ("Arthur Sales", "01593811"),
    ("Vinícius Trigueiro", "01794959"),
    ("William Coelho de Morais", "01263977"),
)


# Blocos de conteúdo

@dataclass
class H:
    text: str
    level: int = 2


@dataclass
class P:
    text: str
    lead: str | None = None


@dataclass
class Bullets:
    items: list[str]


@dataclass
class Numbered:
    items: list[str]


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]
    widths: list[float]
    font_size: float = 8.5


@dataclass
class Figure:
    paths: list[Path]
    caption: str
    width: float = 100  # porcentagem da largura útil, por imagem


@dataclass
class Code:
    text: str
    caption: str


@dataclass
class PageBreak:
    pass


@dataclass
class Document:
    blocks: list = field(default_factory=list)

    def add(self, *blocks) -> None:
        self.blocks.extend(blocks)


def evidence(name: str) -> str:
    return (EVIDENCE / name).read_text(encoding="utf-8").rstrip()


def s2(name: str) -> Path:
    return SPRINT02 / name


def s3(name: str) -> Path:
    return SPRINT03 / name


# Conteúdo

PRESENTATION = [
    "Este documento reúne as entregas das Sprints 01, 02 e 03 do projeto RotaCerta. A Parte I registra o problema, os objetivos, os requisitos e o planejamento inicial. A Parte II apresenta a arquitetura, os modelos de software e de dados, os protótipos e a estrutura inicial do banco. A Parte III demonstra a estrutura funcionando: banco conectado, login, cadastro de usuários, controle de perfis e o CRUD de pedidos, com evidências capturadas do sistema em execução.",
    "As Partes I e II mantêm o conteúdo entregue anteriormente, incluindo as revisões feitas após as orientações da Sprint 01. Os ajustes de planejamento decorrentes da Sprint 03 estão registrados e justificados na seção 22.",
]

TOC = [
    "Parte I  Sprint 01 Planejamento do projeto",
    "1  Identificação da equipe",
    "2  Tema, problema, objetivos e público alvo",
    "3  Requisitos funcionais e não funcionais",
    "4  Casos de uso e Product Backlog",
    "5  Cronograma semanal revisado",
    "Parte II  Sprint 02 Arquitetura e modelagem",
    "6  Arquitetura do sistema",
    "7  Diagrama de classes",
    "8  Modelo Entidade Relacionamento",
    "9  Modelo relacional",
    "10  Protótipos das telas",
    "11  Banco de dados e projeto no GitHub",
    "12  Avaliação sequencial e paralela",
    "13  Aderência às orientações da disciplina",
    "Parte III  Sprint 03 Estrutura inicial funcionando",
    "14  Estrutura implementada",
    "15  Banco de dados conectado",
    "16  Login funcional",
    "17  Cadastro de usuários",
    "18  Controle de perfis",
    "19  CRUD principal: pedidos",
    "20  Execução local",
    "21  Testes automatizados",
    "22  Ajustes no planejamento e na modelagem",
    "23  Repositório GitHub",
    "24  Dificuldades encontradas e próximos passos",
]


def sprint01(doc: Document) -> None:
    doc.add(
        PageBreak(),
        H("Parte I  Sprint 01 Planejamento do projeto", 1),
        H("1  Identificação da equipe"),
        Table(
            ["Integrante", "Matrícula", "Responsabilidade inicial"],
            [
                ["Álvaro Jordão", "01748200", "Scrum Master e Product Owner; organização, requisitos e priorização"],
                ["Arthur Sales", "01593811", "Backend e núcleo de otimização e paralelização"],
                ["Vinícius Trigueiro", "01794959", "Frontend, banco de dados e documentação"],
                ["William Coelho de Morais", "01263977", "Desenvolvimento e testes"],
            ],
            [4.2, 2.8, 10.2],
            9,
        ),
        P("Projeto RotaCerta. Turma 8NA. As responsabilidades organizam o trabalho, mas todos os integrantes participam das decisões, implementação, testes e documentação."),
        H("2  Tema, problema, objetivos e público alvo"),
        P("Tema. Logística e otimização de processos para pequenos negócios com operação própria de entrega.", "Tema."),
        P("Problema. Farmácias, mercados, restaurantes e pequenas distribuidoras frequentemente planejam entregas de forma manual. Essa prática aumenta a distância percorrida, o consumo de combustível e a possibilidade de atraso quando o volume de pedidos cresce.", "Problema."),
        P("Objetivo geral. Desenvolver um sistema web que distribua pedidos entre entregadores e determine uma sequência de paradas que reduza a distância e o tempo total das rotas.", "Objetivo geral."),
        P("Resultados esperados. Centralizar pedidos e entregadores, reduzir distância e tempo em relação à alocação manual, calcular rotas para vários entregadores e disponibilizar uma interface responsiva para a operação diária.", "Resultados esperados."),
        P("Público alvo. Administradores, atendentes e entregadores de pequenos negócios locais. Os clientes finais são beneficiados por entregas mais previsíveis.", "Público alvo."),
        H("3  Requisitos funcionais e não funcionais"),
        H("Requisitos funcionais", 3),
        Table(
            ["ID", "Descrição"],
            [
                ["RF01", "Cadastrar e autenticar usuários com perfis de administrador, atendente e entregador."],
                ["RF02", "Cadastrar pedidos com cliente, endereço, prioridade e horário desejado."],
                ["RF03", "Cadastrar entregadores com disponibilidade e capacidade de carga."],
                ["RF04", "Gerar automaticamente uma rota otimizada para cada entregador."],
                ["RF05", "Atribuir pedidos a entregadores de forma manual ou automática."],
                ["RF06", "Exibir a rota como lista ordenada de paradas e mapa."],
                ["RF07", "Atualizar o status do pedido entre pendente, atribuído, em rota e entregue."],
                ["RF08", "Manter o histórico de entregas realizadas."],
                ["RF09", "Gerar relatório com tempo, distância e comparação da otimização."],
                ["RF10", "Disponibilizar painel administrativo da operação do dia."],
            ],
            [2.0, 15.2],
            9,
        ),
        H("Requisitos não funcionais", 3),
        Table(
            ["ID", "Categoria", "Descrição"],
            [
                ["RNF01", "Desempenho", "Executar o cálculo em tempo aceitável para vários entregadores e permitir processamento paralelo."],
                ["RNF02", "Segurança", "Autenticar usuários, autorizar por perfil e armazenar senhas com hash seguro."],
                ["RNF03", "Usabilidade", "Manter a interface simples para usuários com diferentes níveis de letramento técnico."],
                ["RNF04", "Portabilidade", "Funcionar em navegadores e adaptar o layout para celulares."],
                ["RNF05", "Escalabilidade", "Suportar o crescimento de pedidos e entregadores sem degradação significativa."],
                ["RNF06", "Confiabilidade", "Preservar pedidos, rotas e histórico com integridade referencial."],
                ["RNF07", "Manutenibilidade", "Manter código organizado, documentado, testável e versionado."],
            ],
            [1.8, 3.2, 12.2],
        ),
        H("4  Casos de uso e Product Backlog"),
        Table(
            ["ID", "Ator", "Caso de uso"],
            [
                ["UC01", "Atendente ou administrador", "Cadastrar pedido"],
                ["UC02", "Administrador", "Cadastrar entregador"],
                ["UC03", "Administrador", "Gerar rotas para os pedidos do dia"],
                ["UC04", "Entregador", "Visualizar a rota atribuída"],
                ["UC05", "Entregador", "Atualizar o status da entrega"],
                ["UC06", "Administrador", "Consultar métricas das rotas"],
                ["UC07", "Todos os perfis", "Autenticar-se no sistema"],
            ],
            [2.0, 5.5, 9.7],
            9,
        ),
        H("Product Backlog inicial", 3),
        P("Alta prioridade. Autenticação e perfis, CRUD de pedidos, CRUD de entregadores, banco de dados e motor sequencial com vizinho mais próximo e 2-opt.", "Alta prioridade."),
        P("Média prioridade. Visualização das rotas, atualização de status e paralelização para múltiplos entregadores.", "Média prioridade."),
        P("Evolução. Relatórios, painel consolidado, notificações e avaliação futura de C++ com OpenMP ou CUDA.", "Evolução."),
        PageBreak(),
        H("5  Cronograma semanal revisado"),
        P("O cronograma abaixo substituiu, na Sprint 02, a periodicidade quinzenal apresentada inicialmente. A Sprint 02 manteve o prazo excepcional de 19 de setembro comunicado pela professora; as etapas seguintes usam ciclos semanais. A versão vigente, ajustada na Sprint 03, está na seção 22."),
        Table(
            ["Sprint", "Período", "Entrega principal"],
            [
                ["1", "03/09 a 05/09", "Planejamento, requisitos e backlog"],
                ["2", "06/09 a 19/09", "Arquitetura, modelos, protótipos, banco e estrutura do projeto"],
                ["3", "20/09 a 26/09", "Ambiente executável e contrato inicial da API"],
                ["4", "27/09 a 03/10", "Autenticação e autorização por perfil"],
                ["5", "04/10 a 10/10", "CRUD de clientes e pedidos"],
                ["6", "11/10 a 17/10", "CRUD de entregadores e disponibilidade"],
                ["7", "18/10 a 24/10", "Atribuição de pedidos e visualização de rotas"],
                ["8", "25/10 a 31/10", "Vizinho mais próximo em modo sequencial"],
                ["9", "01/11 a 07/11", "2-opt e linha de base de desempenho"],
                ["10", "08/11 a 14/11", "Paralelização para múltiplos entregadores"],
                ["11", "15/11 a 21/11", "Experimentos sequencial versus paralelo"],
                ["12", "22/11 a 28/11", "Relatórios, testes e documentação"],
                ["Final", "29/11 a 05/12", "Correções, vídeos e preparação para a banca"],
            ],
            [2.0, 3.5, 11.7],
        ),
    )


def sprint02(doc: Document) -> None:
    doc.add(
        PageBreak(),
        H("Parte II  Sprint 02 Arquitetura e modelagem", 1),
        P("A Sprint 02 transforma os requisitos em uma base técnica verificável. A solução adota uma arquitetura web modular, um modelo de dados relacional e um componente de otimização isolado, permitindo implementar e medir versões sequencial e paralela sem duplicar regras de negócio."),
        H("6  Arquitetura do sistema"),
        Table(
            ["Camada", "Tecnologia", "Responsabilidade"],
            [
                ["Interface", "React, TypeScript e Vite", "Aplicação responsiva para administração e operação móvel"],
                ["API", "FastAPI e Python 3.12", "Endpoints REST, validação, OpenAPI e integração com o otimizador"],
                ["Persistência", "PostgreSQL 16", "Integridade, índices, histórico e métricas de execução"],
                ["Mapa", "Leaflet, OpenStreetMap e adaptador OSRM", "Exibição de rotas e matriz de distâncias sem prender o domínio a um provedor"],
                ["Otimização", "Python, 2-opt e processos independentes", "Linha de base sequencial e cálculo paralelo por entregador"],
                ["Ambiente", "Docker Compose", "Inicialização reproduzível de frontend, API e banco"],
            ],
            [3.0, 4.5, 9.7],
        ),
        Figure([s2("arquitetura.png")], "Arquitetura lógica e comunicação entre os componentes"),
        P("O navegador envia requisições HTTPS em JSON para a API. A API executa regras de negócio, persiste dados no PostgreSQL e aciona o motor de otimização. O motor recebe pedidos, entregadores e uma matriz de distâncias por meio de uma interface estável. A mesma interface atende aos modos sequencial e paralelo, o que permite comparar desempenho sem alterar os dados de entrada."),
        P("A escolha de Python não pressupõe o uso de inteligência artificial. As orientações da disciplina aceitam inteligência artificial e/ou otimização de processamento, paralelização e alto desempenho. No RotaCerta, o componente avançado é a otimização de rotas integrada ao fluxo principal. React e TypeScript permanecem restritos à interface, enquanto Python executa o núcleo computacional."),
        H("7  Diagrama de classes"),
        Figure([s2("diagrama_classes.png")], "Classes de domínio e serviço previstas"),
        P("Estabelecimento delimita os dados de cada negócio. Usuario representa autenticação e perfil; Entregador complementa um usuário operacional com capacidade e disponibilidade. Pedido registra destino, prioridade, janela de horário e status. Rota agrega paradas ordenadas. OtimizadorRotas executa o mesmo algoritmo nos modos sequencial e paralelo e registra cada ExecucaoOtimizacao."),
        H("8  Modelo Entidade Relacionamento"),
        Figure([s2("modelo_entidade_relacionamento.png")], "Modelo conceitual com chaves e cardinalidades"),
        P("O modelo mantém o estabelecimento como limite organizacional. Um usuário pode possuir um cadastro de entregador. Cada pedido pertence a um cliente e pode ser atribuído a um entregador. Uma rota contém paradas ordenadas; cada parada referencia um pedido. As execuções de otimização registram quantidade de pedidos, entregadores, workers, tempo e distância total."),
        H("9  Modelo relacional"),
        Table(
            ["Tabela", "PK", "FK", "Finalidade"],
            [
                ["establishments", "id", "-", "Negócio, endereço e coordenadas do depósito"],
                ["users", "id", "establishment_id", "Credenciais, perfil e situação do usuário"],
                ["couriers", "id", "establishment_id, user_id", "Capacidade e disponibilidade do entregador"],
                ["customers", "id", "establishment_id", "Cliente associado ao estabelecimento"],
                ["orders", "id", "establishment_id, customer_id, assigned_courier_id", "Destino, peso, prioridade, janela e status"],
                ["routes", "id", "establishment_id, courier_id", "Rota diária, algoritmo, modo e totais"],
                ["route_stops", "id", "route_id, order_id", "Sequência e acompanhamento de cada parada"],
                ["optimization_runs", "id", "establishment_id", "Métricas de execuções sequenciais e paralelas"],
            ],
            [3.3, 1.6, 5.2, 7.1],
            8,
        ),
        P("As restrições CHECK limitam perfis, estados e modos de execução. As chaves estrangeiras preservam a integridade entre usuários, pedidos, entregadores e rotas. Índices cobrem as consultas mais frequentes por estabelecimento, status, entregador, data e modo de execução."),
        H("10  Protótipos das telas principais"),
        P("Os wireframes priorizam navegação direta e leitura em dispositivos móveis. A primeira sequência cobre autenticação, painel diário e cadastro de pedido. A segunda cobre geração de rotas, consulta da rota pelo entregador e atualização de status."),
        Figure([s2("prototipos_administracao.png")], "Acesso, painel administrativo e cadastro de pedido"),
        Figure([s2("prototipos_rotas.png")], "Planejamento de rotas e fluxo móvel do entregador"),
        Table(
            ["Tela", "Requisito", "Objetivo"],
            [
                ["Acesso", "UC07", "Login e identificação do perfil"],
                ["Painel do dia", "RF10", "Pedidos, situação operacional e atalhos"],
                ["Novo pedido", "UC01 / RF02", "Cliente, destino, carga, prioridade e janela"],
                ["Planejamento", "UC03 / RF04", "Mapa, totais e comando de otimização"],
                ["Minha rota", "UC04 / RF06", "Sequência, mapa e próxima parada"],
                ["Atualizar entrega", "UC05 / RF07", "Transição de status e observação"],
            ],
            [4.0, 3.2, 10.0],
        ),
        PageBreak(),
        H("11  Banco de dados e projeto no GitHub"),
        H("Banco de dados criado", 3),
        P("A estrutura inicial está implementada no arquivo database/schema.sql para PostgreSQL 16. O serviço db do arquivo compose.yaml executa o esquema automaticamente na primeira inicialização do volume. O modelo inclui oito tabelas, restrições de integridade e cinco índices iniciais."),
        H("Estrutura do repositório na Sprint 02", 3),
        Table(
            ["Caminho", "Conteúdo"],
            [
                ["backend/", "API FastAPI e limite do módulo de otimização"],
                ["backend/app/optimizer/", "Vizinho mais próximo, 2-opt e execução sequencial ou paralela"],
                ["backend/tests/", "Testes automatizados do núcleo de roteirização"],
                ["frontend/", "Aplicação React e TypeScript"],
                ["database/", "DDL, instruções e inicialização do PostgreSQL"],
                ["docs/sprint-02/assets/", "Diagramas e protótipos incorporados ao documento"],
                ["tools/documentation/", "Geração reproduzível dos materiais técnicos"],
                ["compose.yaml", "Orquestração local dos três serviços"],
                ["CONTRIBUTING.md", "Padrões de branch, commit e revisão"],
            ],
            [6.0, 11.2],
            9,
        ),
        P("O fluxo recomendado usa branches curtas por tarefa, pull request e revisão de outro integrante. As branches pessoais dev/alvaro, dev/arthur e dev/vinicius identificam ambientes acadêmicos, mas não substituem branches de feature, correção ou documentação."),
        H("12  Avaliação sequencial e paralela"),
        P("A orientação da Sprint 01 exige manter a comparação entre as versões sequencial e paralela. A primeira implementação já executa vizinho mais próximo e refinamento 2-opt nos dois modos. As versões usam os mesmos pedidos, entregadores e coordenadas; a única variável controlada é o modo de execução."),
        Table(
            ["Métrica", "Cálculo ou unidade", "Critério"],
            [
                ["Tempo de execução", "Milissegundos", "Média, mediana e percentil 95 de dez repetições"],
                ["Distância total", "Quilômetros", "Confirma que a paralelização não altera a qualidade da rota"],
                ["Speedup", "Tseq / Tpar", "Ganho obtido com a execução paralela"],
                ["Eficiência", "Speedup / workers", "Uso relativo dos processos disponíveis"],
                ["Escala", "Pedidos e entregadores", "Cenários de 50, 100, 250 e 500 pedidos com 2, 4 e 8 entregadores"],
            ],
            [4.0, 4.0, 9.2],
        ),
        P("Cada cenário terá uma execução de aquecimento e dez repetições válidas. O relatório registrará processador, memória, sistema operacional, versão do código, número de workers e semente dos dados. A tabela optimization_runs armazenará cada medição para permitir auditoria e reprodução."),
        P("Evidência prática. O arquivo backend/app/optimizer/routing.py contém a heurística determinística, o cálculo de distância geodésica, o refinamento 2-opt e a execução com processos independentes. O endpoint POST /optimizer/compare retorna rotas, distâncias, tempos, workers, speedup e a confirmação de equivalência entre os modos. Cinco testes automatizados validam rota vazia, preservação das paradas, melhoria do 2-opt, resultado da otimização e equivalência sequencial/paralela.", "Evidência prática."),
        H("13  Aderência às orientações da disciplina"),
        Table(
            ["Orientação", "Situação na Sprint 02", "Evidência"],
            [
                ["Projeto integrado", "Atendido", "Um único sistema reúne interface, API, banco e otimização"],
                ["Componente avançado", "Atendido", "Otimização e paralelização fazem parte da geração de rotas"],
                ["Tecnologia prioritária", "Atendido", "Python no núcleo; JavaScript e TypeScript apenas na interface"],
                ["Integração não superficial", "Atendido", "O endpoint compara os modos sobre os mesmos dados"],
                ["Evolução prática", "Atendido", "Código executável e cinco testes automatizados no repositório"],
                ["GitHub atualizado", "Atendido", "Branch da Sprint 02 e Pull Request número 1"],
                ["Participação da equipe", "Contínuo", "Cada integrante deve registrar contribuições próprias nas próximas tarefas"],
            ],
            [4.1, 3.2, 9.9],
        ),
    )


def sprint03(doc: Document) -> None:
    doc.add(
        PageBreak(),
        H("Parte III  Sprint 03 Estrutura inicial funcionando", 1),
        P("A Sprint 03 transforma a arquitetura e o modelo de dados da Sprint 02 em um sistema executável. Frontend, API e PostgreSQL passaram a funcionar integrados: o usuário faz login, recebe permissões de acordo com o seu perfil e cadastra, consulta, edita e exclui pedidos gravados no banco. Todas as telas e respostas mostradas nesta parte foram capturadas com o sistema em execução local."),
        H("14  Estrutura implementada"),
        P("A aplicação mantém as três camadas definidas na Sprint 02. O frontend React consome a API REST com requisições JSON autenticadas por token. A API valida os dados, aplica as regras de cada perfil e grava as informações no PostgreSQL por meio do SQLAlchemy."),
        Table(
            ["Componente", "Arquivo", "Responsabilidade"],
            [
                ["Configuração", "backend/app/config.py", "Lê a URL do banco, a chave do token, as origens permitidas e as opções de inicialização"],
                ["Conexão", "backend/app/database.py", "Cria o pool de conexões, verifica o banco e aplica o esquema quando necessário"],
                ["Modelos", "backend/app/models.py", "Mapeia as tabelas do schema.sql para classes Python"],
                ["Segurança", "backend/app/security.py", "Hash Argon2, emissão e validação do JWT e verificação de perfil"],
                ["Autenticação", "backend/app/routers/auth.py", "Login, cadastro de estabelecimento e dados do usuário logado"],
                ["Usuários", "backend/app/routers/users.py", "Cadastro, edição e desativação de usuários; lista de entregadores"],
                ["Pedidos", "backend/app/routers/orders.py", "CRUD de pedidos e mudança de situação"],
                ["Dados iniciais", "backend/app/seed.py", "Estabelecimento, usuários e pedidos de demonstração"],
                ["Interface", "frontend/src/pages/", "Login, pedidos, entregas do entregador e usuários"],
                ["Testes", "backend/tests/", "16 testes da API e 5 do otimizador"],
            ],
            [3.0, 5.2, 9.0],
        ),
        H("Fluxo de uma requisição autenticada", 3),
        Numbered([
            "O usuário informa e-mail e senha na tela de login.",
            "A API compara a senha com o hash Argon2 gravado em users.password_hash e devolve um token JWT válido por oito horas.",
            "O frontend envia o token no cabeçalho Authorization de cada requisição.",
            "A API valida o token, carrega o usuário do banco e confere se o perfil tem permissão para a rota.",
            "As consultas são sempre filtradas pelo estabelecimento do usuário; entregadores recebem apenas os pedidos atribuídos a eles.",
        ]),
        H("15  Banco de dados conectado"),
        P("A API se conecta ao PostgreSQL pela URL da variável DATABASE_URL, usando o driver psycopg 3 e o SQLAlchemy 2. O pool de conexões testa a conexão antes de cada uso. Na execução com Docker, o PostgreSQL aplica database/schema.sql na primeira inicialização; na execução sem Docker, a própria API aplica o mesmo arquivo quando encontra o banco vazio. Nos dois casos a estrutura é exatamente a modelada na Sprint 02."),
        P("O endpoint GET /health executa uma consulta no banco e informa o tipo e a versão do servidor. Se o banco estiver indisponível, a resposta passa a ser HTTP 503 com database igual a unavailable."),
        Figure([s3("s03_01_health.png")], "Endpoint de verificação confirmando a conexão da API com o PostgreSQL", 75),
        Code(evidence("sql_tabelas.txt"), "Consulta às oito tabelas do banco rotacerta com a quantidade de registros"),
        Figure([s3("s03_02_swagger.png")], "Documentação interativa da API gerada pelo FastAPI, com as rotas de autenticação, usuários e pedidos"),
        H("16  Login funcional"),
        P("A tela de login autentica os usuários cadastrados no banco. O e-mail é comparado sem diferenciar maiúsculas de minúsculas e a senha é verificada contra o hash Argon2; a senha em texto nunca é gravada. Credenciais incorretas retornam HTTP 401 com a mensagem E-mail ou senha inválidos. Usuários desativados recebem HTTP 403. A sessão fica salva no navegador e é validada novamente na API sempre que a página é aberta."),
        Figure([s3("s03_03_login.png")], "Tela de login com atalhos para as contas de demonstração"),
        Figure([s3("s03_04_login_erro.png")], "Tentativa de login com senha incorreta"),
        Code(evidence("sql_usuarios.txt"), "Usuários gravados no banco: apenas o hash da senha é armazenado"),
        H("17  Cadastro de usuários"),
        P("O cadastro acontece de duas formas. Um novo negócio cria a própria conta pela opção Cadastrar meu negócio, que grava o estabelecimento e o seu primeiro administrador. A partir daí, o administrador cadastra atendentes e entregadores na tela Usuários. Para entregadores, o sistema exige a capacidade de carga e cria também o registro na tabela couriers."),
        Bullets([
            "O e-mail é único em todo o sistema; uma duplicidade retorna HTTP 409.",
            "A senha tem no mínimo oito caracteres e é gravada com hash Argon2.",
            "Usuários não são apagados: a desativação bloqueia o login e preserva o histórico de pedidos.",
            "O administrador não pode desativar a si mesmo nem remover o próprio perfil de administrador.",
            "Cada estabelecimento enxerga apenas os próprios usuários e pedidos.",
        ]),
        Figure([s3("s03_05_cadastro_negocio.png")], "Cadastro de um novo estabelecimento com o seu administrador"),
        Figure([s3("s03_06_negocio_novo_vazio.png")], "Estabelecimento recém-criado: os pedidos de outros negócios não aparecem"),
        Figure([s3("s03_13_usuarios.png")], "Tela de usuários do administrador, com o resumo das permissões de cada perfil"),
        Figure([s3("s03_14_novo_usuario.png")], "Cadastro de um entregador com capacidade de carga"),
        Figure([s3("s03_15_usuario_cadastrado.png")], "Entregador cadastrado e listado com disponibilidade e capacidade"),
        H("18  Controle de perfis"),
        P("Os três perfis previstos no RF01 foram implementados. A verificação acontece na API, em cada rota, e não apenas na interface: mesmo que alguém chame a API diretamente, a ação é negada para perfis sem permissão. O perfil é lido do banco a cada requisição, então uma alteração feita pelo administrador vale imediatamente."),
        Table(
            ["Ação", "Administrador", "Atendente", "Entregador"],
            [
                ["Entrar no sistema", "Sim", "Sim", "Sim"],
                ["Cadastrar, editar e desativar usuários", "Sim", "Não", "Não"],
                ["Consultar pedidos", "Todos do estabelecimento", "Todos do estabelecimento", "Só os atribuídos a ele"],
                ["Cadastrar e editar pedidos", "Sim", "Sim", "Não"],
                ["Atribuir entregador ao pedido", "Sim", "Sim", "Não"],
                ["Excluir pedidos", "Sim", "Não", "Não"],
                ["Atualizar a situação", "Qualquer situação", "Qualquer situação", "De Atribuído para Em rota e de Em rota para Entregue"],
            ],
            [5.0, 3.6, 3.6, 5.0],
        ),
        Figure([s3("s03_16_atendente.png")], "Visão do atendente: sem a aba Usuários e sem o botão Excluir"),
        Figure(
            [s3("s03_17_entregador_celular.png"), s3("s03_18_entregador_status.png")],
            "Visão do entregador no celular: apenas os próprios pedidos e o botão para avançar a entrega",
            36,
        ),
        Code(evidence("api_controle_acesso.txt"), "Respostas da API para cada perfil, obtidas com chamadas diretas"),
        H("19  CRUD principal: pedidos"),
        P("O pedido é a entidade principal do RotaCerta porque concentra o que será roteirizado: cliente, destino, carga, prioridade, janela de horário, entregador e situação. O CRUD usa as tabelas orders e customers do modelo da Sprint 02. O cliente é informado no próprio formulário do pedido; a API reaproveita o cadastro quando o mesmo nome e telefone já existem e cria um registro em customers quando não existem. O local de entrega é marcado com um clique no mapa, que preenche latitude e longitude."),
        Table(
            ["Operação", "Rota da API", "Regra de negócio"],
            [
                ["Cadastrar", "POST /orders", "Coordenadas obrigatórias, fim da janela posterior ao início; com entregador o pedido já nasce Atribuído"],
                ["Consultar", "GET /orders e GET /orders/{id}", "Lista com filtro por situação; o entregador vê só os próprios pedidos"],
                ["Atualizar", "PUT /orders/{id} e PATCH /orders/{id}/status", "Pedidos entregues ou cancelados não podem ser editados; Em rota exige entregador"],
                ["Excluir", "DELETE /orders/{id}", "Somente administrador; pedido que já faz parte de uma rota é protegido pela chave estrangeira"],
            ],
            [2.6, 5.4, 9.2],
        ),
        Figure([s3("s03_07_pedidos_admin.png")], "Lista de pedidos do administrador com filtros por situação"),
        Figure([s3("s03_08_novo_pedido.png")], "Cadastro de pedido com cliente, local no mapa, prioridade, janela e entregador"),
        Figure([s3("s03_09_pedido_cadastrado.png")], "Pedido cadastrado aparecendo no topo da lista"),
        Figure([s3("s03_10_editar_pedido.png")], "Edição do pedido: prioridade, horário e entregador alterados"),
        Code(evidence("sql_pedido_editado.txt"), "Pedido gravado no banco com os valores da edição"),
        Figure([s3("s03_12_pedido_excluido.png")], "Pedido excluído pelo administrador"),
        Code(evidence("sql_pedido_excluido.txt"), "O pedido excluído não existe mais no banco"),
        H("20  Execução local"),
        H("Com Docker", 3),
        Numbered([
            "Instalar o Docker Desktop.",
            "Na raiz do repositório, copiar .env.example para .env.",
            "Executar docker compose up --build.",
            "Se já existir um PostgreSQL usando a porta 5432, alterar POSTGRES_PORT no .env para 5433.",
        ]),
        H("Sem Docker", 3),
        Numbered([
            "Instalar Python 3.12 ou superior, Node.js 20 ou superior e PostgreSQL 16 ou superior.",
            "No PostgreSQL, criar o usuário e o banco: CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev'; CREATE DATABASE rotacerta OWNER rotacerta;",
            "Na pasta backend, criar o ambiente virtual, instalar requirements.txt e executar uvicorn app.main:app --reload. Na primeira execução a API cria as tabelas e os dados de demonstração.",
            "Na pasta frontend, executar npm install e npm run dev.",
            "Para outra porta, usuário ou senha do banco, copiar backend/.env.example para backend/.env e ajustar DATABASE_URL.",
        ]),
        Table(
            ["Serviço", "Endereço"],
            [
                ["Sistema", "http://localhost:5173"],
                ["Documentação interativa da API", "http://localhost:8000/docs"],
                ["Verificação da API e do banco", "http://localhost:8000/health"],
            ],
            [7.0, 10.2],
            9,
        ),
        Table(
            ["Perfil", "E-mail", "Senha"],
            [
                ["Administrador", "admin@rotacerta.com.br", "rotacerta123"],
                ["Atendente", "atendente@rotacerta.com.br", "rotacerta123"],
                ["Entregador", "entregador@rotacerta.com.br", "rotacerta123"],
            ],
            [4.0, 8.2, 5.0],
            9,
        ),
        P("As contas acima são criadas automaticamente apenas quando o banco não possui nenhum estabelecimento, para facilitar a demonstração. O passo a passo completo também está no README do repositório."),
        H("21  Testes automatizados"),
        P("Os testes da API usam um banco SQLite em memória, recriado a cada teste, e cobrem login, sessão, hash de senha, cadastro de usuários, isolamento entre estabelecimentos, permissões de cada perfil, CRUD de pedidos e regras de situação. Os testes do otimizador continuam validando os modos sequencial e paralelo."),
        Code(evidence("testes.txt"), "Execução da suíte de testes"),
        H("22  Ajustes no planejamento e na modelagem"),
        H("Modelagem", 3),
        P("Nenhuma tabela, coluna ou restrição do modelo relacional da Sprint 02 precisou ser alterada. A implementação tomou três decisões que não mudam o modelo:"),
        Bullets([
            "O cliente é cadastrado a partir do formulário do pedido, sem uma tela própria nesta etapa, reaproveitando a tabela customers.",
            "Usuários são desativados em vez de excluídos, porque pedidos e rotas referenciam entregadores por chave estrangeira.",
            "As coordenadas do pedido são obtidas com um clique no mapa Leaflet; a busca automática pelo endereço fica para a próxima etapa.",
        ]),
        H("Planejamento", 3),
        P("A Sprint 03 da disciplina exigiu login, perfis, cadastro de usuários e o CRUD principal, que no cronograma da Sprint 02 estavam previstos para as Sprints 04 e 05. Esses itens foram antecipados. As etapas seguintes foram reorganizadas para manter a otimização sequencial e paralela e os experimentos antes do período de relatórios e da banca."),
        Table(
            ["Sprint", "Período", "Entrega principal", "Situação"],
            [
                ["1", "03/09 a 05/09", "Planejamento, requisitos e backlog", "Concluída"],
                ["2", "06/09 a 19/09", "Arquitetura, modelos, protótipos, banco e estrutura", "Concluída"],
                ["3", "20/09 a 26/09", "Banco conectado, login, perfis, usuários e CRUD de pedidos", "Concluída"],
                ["4", "27/09 a 03/10", "Entregadores, disponibilidade, clientes e busca de endereço", "Planejada"],
                ["5", "04/10 a 10/10", "Atribuição de pedidos e visualização das rotas no mapa", "Planejada"],
                ["6", "11/10 a 17/10", "Vizinho mais próximo integrado aos pedidos do dia", "Planejada"],
                ["7", "18/10 a 24/10", "2-opt, persistência das rotas e linha de base", "Planejada"],
                ["8", "25/10 a 31/10", "Paralelização para múltiplos entregadores", "Planejada"],
                ["9", "01/11 a 07/11", "Experimentos sequencial versus paralelo", "Planejada"],
                ["10", "08/11 a 14/11", "Histórico, relatórios e painel do dia", "Planejada"],
                ["11", "15/11 a 21/11", "Testes, usabilidade e segurança", "Planejada"],
                ["12", "22/11 a 28/11", "Documentação e ajustes", "Planejada"],
                ["Final", "29/11 a 05/12", "Correções, vídeos e preparação para a banca", "Planejada"],
            ],
            [1.6, 3.0, 9.6, 3.0],
        ),
        H("23  Repositório GitHub"),
        P(f"Repositório oficial. {REPOSITORY}", "Repositório oficial."),
        Table(
            ["Branch", "Finalidade"],
            [
                ["master", "Versão estável e entregas aprovadas"],
                ["sprint/02-arquitetura-modelagem", "Integração da Sprint 02"],
                ["sprint/03-estrutura-funcional", "Integração da Sprint 03"],
                ["dev/alvaro, dev/arthur, dev/vinicius", "Ambientes pessoais dos integrantes"],
            ],
            [7.0, 10.2],
            9,
        ),
        Table(
            ["Caminho", "Novidade da Sprint 03"],
            [
                ["backend/app/routers/", "Rotas de autenticação, usuários e pedidos"],
                ["backend/app/models.py e database.py", "Conexão e mapeamento do PostgreSQL"],
                ["backend/tests/test_api.py", "Testes da API"],
                ["frontend/src/pages/", "Telas de login, pedidos e usuários"],
                ["docs/sprint-03/", "Capturas de tela e saídas usadas como evidência"],
                ["tools/documentation/", "Captura das evidências e geração deste documento"],
            ],
            [6.5, 10.7],
            9,
        ),
        H("24  Dificuldades encontradas e próximos passos"),
        H("Dificuldades", 3),
        Table(
            ["Dificuldade", "Como foi tratada"],
            [
                ["Docker indisponível em máquina de desenvolvimento", "Execução sem Docker documentada; a API cria as tabelas a partir do schema.sql quando o banco está vazio"],
                ["PostgreSQL já instalado ocupando a porta 5432", "Porta do banco no Compose passou a ser configurável por POSTGRES_PORT"],
                ["psycopg 3.2.9 sem pacote para o Python 3.14", "Atualização para psycopg 3.3.6, compatível com Python 3.12 a 3.14"],
                ["Pedidos exigem latitude e longitude", "Mapa no formulário para marcar o ponto; busca automática pelo endereço planejada"],
                ["Paralelização mais lenta que a versão sequencial em entradas pequenas", "Criar processos custa mais que o cálculo com poucos pedidos; os experimentos usarão cenários de 50 a 500 pedidos"],
            ],
            [6.2, 11.0],
        ),
        H("Próximos passos", 3),
        Bullets([
            "Gerenciar entregadores e disponibilidade em tela própria e buscar coordenadas a partir do endereço.",
            "Integrar o otimizador aos pedidos do dia e gravar rotas em routes e route_stops.",
            "Registrar as execuções sequenciais e paralelas em optimization_runs.",
            "Distribuir as tarefas entre os integrantes com pull requests revisados, registrando a contribuição de cada um no GitHub.",
        ]),
        H("Situação da Sprint 03", 2),
        Table(
            ["Entrega obrigatória", "Situação", "Evidência"],
            [
                ["Banco de dados conectado", "Concluído", "Seção 15: /health, consulta às tabelas e documentação da API"],
                ["Login funcional", "Concluído", "Seção 16: tela de login, erro de senha e hash no banco"],
                ["Cadastro de usuários", "Concluído", "Seção 17: cadastro de estabelecimento e de usuários"],
                ["Controle de perfis", "Concluído", "Seção 18: matriz de permissões, telas por perfil e respostas 401 e 403"],
                ["CRUD principal", "Concluído", "Seção 19: cadastro, consulta, edição e exclusão de pedidos no banco"],
                ["Deploy local", "Concluído", "Seção 20: Docker Compose ou execução manual"],
                ["Repositório atualizado", "Concluído", "Seção 23: branch da Sprint 03"],
            ],
            [4.2, 2.6, 10.4],
        ),
    )


def build_content() -> Document:
    doc = Document()
    sprint01(doc)
    sprint02(doc)
    sprint03(doc)
    return doc


# HTML e PDF

CSS = """
@page { size: A4; margin: 18mm 18mm 20mm 18mm; }
* { box-sizing: border-box; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #000; margin: 0; }
.cover { height: 250mm; display: flex; flex-direction: column; align-items: center; text-align: center; page-break-after: always; }
.cover .inst { font-weight: bold; font-size: 14pt; margin-top: 4mm; }
.cover .course { margin-top: 8mm; font-size: 11pt; }
.cover .title { margin-top: 42mm; font-size: 30pt; font-weight: bold; }
.cover .subtitle { margin-top: 5mm; font-size: 16pt; font-weight: bold; }
.cover .group { margin-top: 26mm; font-size: 14pt; font-weight: bold; }
.cover .team { margin-top: 8mm; line-height: 1.9; }
.cover .year { margin-top: auto; }
h1 { font-size: 16pt; margin: 0 0 4mm; break-after: avoid; }
h2 { font-size: 13pt; margin: 6mm 0 3mm; break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; break-after: avoid; }
p { margin: 0 0 2.6mm; text-align: justify; }
ul, ol { margin: 0 0 3mm; padding-left: 7mm; }
li { margin-bottom: 1.2mm; }
.toc p { margin: 0 0 1.4mm; text-align: left; }
.toc p.part { font-weight: bold; margin-top: 3mm; }
.page-break { break-after: page; }
table { width: 100%; border-collapse: collapse; margin: 1mm 0 4mm; font-size: 8.5pt; break-inside: auto; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { background: #173B67; color: #fff; padding: 1.6mm 2mm; text-align: center; border: 0.6pt solid #d9d9d9; }
td { padding: 1.5mm 2mm; border: 0.6pt solid #d9d9d9; vertical-align: middle; }
tbody tr:nth-child(even) td { background: #F5F7FA; }
figure { margin: 2mm 0 5mm; text-align: center; break-inside: avoid; }
figure .images { display: flex; justify-content: center; gap: 6mm; }
figure img { max-width: 100%; border: 0.6pt solid #d0d5dd; }
figcaption, .code-caption { font-size: 8.5pt; font-style: italic; color: #58606e; margin-top: 1.5mm; text-align: center; }
.code { break-inside: avoid; margin: 1mm 0 5mm; }
pre { margin: 0; padding: 3mm; background: #F5F7FA; border: 0.6pt solid #d9d9d9; font-family: Consolas, "Courier New", monospace; font-size: 7.2pt; line-height: 1.35; white-space: pre-wrap; word-break: break-word; }
"""


def html_text(text: str) -> str:
    return escape(text)


def render_html(doc: Document) -> str:
    parts = [
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>",
        f"<title>RotaCerta {TITLE}</title><style>{CSS}</style></head><body>",
        "<section class='cover'>",
        "<div class='inst'>UNINASSAU</div>",
        "<div class='course'>Fábrica de Software e Tópicos Avançados em Ciência da Computação<br>Turma 8NA  |  Semestre 2026.2</div>",
        "<div class='title'>RotaCerta</div>",
        f"<div class='subtitle'>{TITLE}</div>",
        "<div class='group'>Grupo 04</div>",
        "<div class='team'>" + "<br>".join(f"{n}  |  {m}" for n, m in TEAM) + "</div>",
        "<div class='year'>2026</div></section>",
        "<h1>Apresentação</h1>",
        *(f"<p>{html_text(t)}</p>" for t in PRESENTATION),
        "<h1>Sumário</h1><div class='toc'>",
        *(f"<p class='{'part' if item.startswith('Parte') else ''}'>{html_text(item)}</p>" for item in TOC),
        "</div>",
    ]
    figure_number = 0
    for block in doc.blocks:
        if isinstance(block, PageBreak):
            parts.append("<div class='page-break'></div>")
        elif isinstance(block, H):
            parts.append(f"<h{block.level}>{html_text(block.text)}</h{block.level}>")
        elif isinstance(block, P):
            text = html_text(block.text)
            if block.lead and block.text.startswith(block.lead):
                text = f"<b>{html_text(block.lead)}</b>{html_text(block.text[len(block.lead):])}"
            parts.append(f"<p>{text}</p>")
        elif isinstance(block, Bullets):
            parts.append("<ul>" + "".join(f"<li>{html_text(i)}</li>" for i in block.items) + "</ul>")
        elif isinstance(block, Numbered):
            parts.append("<ol>" + "".join(f"<li>{html_text(i)}</li>" for i in block.items) + "</ol>")
        elif isinstance(block, Table):
            total = sum(block.widths)
            cols = "".join(f"<col style='width:{w / total * 100:.1f}%'>" for w in block.widths)
            head = "".join(f"<th>{html_text(h)}</th>" for h in block.headers)
            rows = "".join(
                "<tr>" + "".join(f"<td>{html_text(str(c))}</td>" for c in row) + "</tr>" for row in block.rows
            )
            parts.append(
                f"<table style='font-size:{block.font_size}pt'><colgroup>{cols}</colgroup>"
                f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"
            )
        elif isinstance(block, Figure):
            figure_number += 1
            images = "".join(f"<img src='{p.as_uri()}' style='width:{block.width}%'>" for p in block.paths)
            parts.append(
                f"<figure><div class='images'>{images}</div>"
                f"<figcaption>Figura {figure_number}  {html_text(block.caption)}</figcaption></figure>"
            )
        elif isinstance(block, Code):
            parts.append(
                f"<div class='code'><pre>{html_text(block.text)}</pre>"
                f"<div class='code-caption'>{html_text(block.caption)}</div></div>"
            )
    parts.append("</body></html>")
    return "".join(parts)


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    footer = (
        "<div style='width:100%;font-family:Arial;font-size:8px;color:#58606e;text-align:center'>"
        "RotaCerta  |  Grupo 04  |  Sprints 01 a 03  |  Página <span class='pageNumber'></span></div>"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=footer,
            margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"},
        )
        browser.close()


# DOCX

def add_code_docx(document, text: str, caption: str) -> None:
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    cell = table.rows[0].cells[0]
    cell.width = Cm(17.2)
    set_cell_shading(cell, "F5F7FA")
    set_cell_margins(cell)
    paragraph = cell.paragraphs[0]
    lines = text.splitlines()
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        set_font(run, name="Consolas", size=7)
        if index < len(lines) - 1:
            run.add_break()
    add_caption_docx(document, caption)


def add_caption_docx(document, caption: str) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    set_font(p.add_run(caption), size=9, italic=True, color=GRAY)


def render_docx(doc: Document, path: Path) -> None:
    document = setup_document()
    footer = document.sections[0].footer.paragraphs[0]
    footer.runs[0].text = "RotaCerta  |  Grupo 04  |  Sprints 01 a 03  |  Página "
    document.core_properties.title = f"RotaCerta {TITLE}"
    document.core_properties.keywords = "RotaCerta, Sprint 01, Sprint 02, Sprint 03"

    def centered(text, size, bold=False, before=0, after=6):
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        set_font(p.add_run(text), size=size, bold=bold)

    centered("UNINASSAU", 14, True, after=26)
    centered("Fábrica de Software e Tópicos Avançados em Ciência da Computação\nTurma 8NA  |  Semestre 2026.2", 11, after=68)
    centered("RotaCerta", 23, True, after=12)
    centered(TITLE, 17, True, after=64)
    centered("Grupo 04", 14, True, after=12)
    for name, number in TEAM:
        centered(f"{name}  |  {number}", 11, after=5)
    centered("2026", 11, before=70)

    document.add_page_break()
    add_heading(document, "Apresentação", 1)
    for text in PRESENTATION:
        add_body(document, text)
    add_heading(document, "Sumário", 1)
    for item in TOC:
        p = document.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.35)
        p.paragraph_format.space_after = Pt(3)
        set_font(p.add_run(item), bold=item.startswith("Parte"))

    figure_number = 0
    for block in doc.blocks:
        if isinstance(block, PageBreak):
            document.add_page_break()
        elif isinstance(block, H):
            add_heading(document, block.text, block.level)
        elif isinstance(block, P):
            add_body(document, block.text, block.lead)
        elif isinstance(block, Bullets):
            add_bullets(document, block.items)
        elif isinstance(block, Numbered):
            add_numbered(document, block.items)
        elif isinstance(block, Table):
            add_table(document, block.headers, block.rows, block.widths, block.font_size)
        elif isinstance(block, Figure):
            figure_number += 1
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            for index, image in enumerate(block.paths):
                if index:
                    p.add_run("   ")
                p.add_run().add_picture(str(image), width=Inches(6.75 * block.width / 100))
            add_caption_docx(document, f"Figura {figure_number}  {block.caption}")
        elif isinstance(block, Code):
            add_code_docx(document, block.text, block.caption)
    document.save(path)


def main() -> None:
    doc = build_content()
    html_dir = ROOT / "output" / "html"
    pdf_dir = ROOT / "output" / "pdf"
    docx_dir = ROOT / "output" / "docx"
    for directory in (html_dir, pdf_dir, docx_dir):
        directory.mkdir(parents=True, exist_ok=True)
    html_path = html_dir / f"{NAME}.html"
    html_path.write_text(render_html(doc), encoding="utf-8")
    render_pdf(html_path, pdf_dir / f"{NAME}.pdf")
    render_docx(doc, docx_dir / f"{NAME}.docx")
    for path in (html_path, pdf_dir / f"{NAME}.pdf", docx_dir / f"{NAME}.docx"):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
