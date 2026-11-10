# Como rodar o RotaCerta localmente

Este guia mostra como subir o banco, a API e o frontend na sua máquina. Cada comando vem seguido de um comentário (`#` no terminal, `--` no SQL) explicando o que ele faz. Os comentários podem ser copiados junto com o comando.

Os manuais completos da Sprint 11 estão em
[Manual do Usuário](docs/manuais/MANUAL_DO_USUARIO.md) e
[Manual Técnico](docs/manuais/MANUAL_TECNICO.md). A referência atual de
arquitetura, requisitos, casos de uso e regras está em
[Documentação final](docs/final/DOCUMENTACAO_FINAL.md).

## Antes de começar: qual terminal você está usando?

Os comandos de terminal aparecem em duas versões, porque a sintaxe muda de um para o outro:

| Terminal | Como reconhecer |
| --- | --- |
| **PowerShell** | A linha começa com `PS C:\...` |
| **Git Bash** | A linha mostra `MINGW64` |

No Linux ou no macOS, use a versão do Git Bash e troque `.venv/Scripts/activate` por `.venv/bin/activate`.

## Pré-requisitos

### Demonstração rápida sem Docker ou PostgreSQL

Com Python e Node.js instalados e as dependências do backend e frontend preparadas,
execute na raiz do projeto:

```powershell
.\backend\.venv\Scripts\python.exe tools/run_local_demo.py
```

Abra http://localhost:5173 e entre com `admin@rotacerta.com.br`, senha `rotacerta123`.
O banco SQLite de demonstração é salvo em `backend/rotacerta-demo.db`. Ctrl+C encerra
os dois servidores sem apagar dados. Esse modo serve para demonstração local; a
instalação PostgreSQL completa continua descrita abaixo. Não é necessário recriar
o ambiente `.venv` se ele já existir.

| Ferramenta | Versão | Observação |
| --- | --- | --- |
| Python | 3.12 ou superior | Para a API |
| Node.js | 20.19+ ou 22.12+ | Para o frontend |
| PostgreSQL | 16 ou superior | Instale junto com o pgAdmin 4 e anote a senha do usuário `postgres` |
| Docker Desktop | Qualquer versão recente | Só se for usar a Opção 1 |
| GPU NVIDIA com driver atualizado | Opcional | Usada pelo modo GPU (CUDA) do otimizador. O sistema funciona sem GPU |

Para conferir se a sua máquina tem GPU NVIDIA:

```bash
nvidia-smi                         # mostra o modelo da GPU e a versão do CUDA suportada pelo driver; se der "command not found", a máquina não tem GPU NVIDIA ou o driver não está instalado
```

## Opção 1: com Docker

Os comandos são iguais no PowerShell e no Git Bash.

```bash
cp .env.example .env               # cria o arquivo de configuração a partir do modelo (só na primeira vez)
docker compose up --build          # constrói as imagens e sobe o banco, a API e o frontend juntos
```

Se já existir um PostgreSQL instalado na sua máquina usando a porta 5432, abra o `.env` e troque `POSTGRES_PORT` para `5433` antes de subir.

Para parar ou recomeçar:

```bash
docker compose down                # para e remove os containers, mantendo os dados do banco
docker compose down -v             # para tudo e apaga também os dados do banco (recomeça do zero na próxima subida)
```

O modo CUDA não fica disponível dentro do Docker sem configuração extra da GPU. Para usá-lo, prefira a Opção 2.

## Opção 2: sem Docker (passo a passo)

### Passo 1. Criar o usuário e o banco no PostgreSQL

Faça isso **só na primeira vez**. O sistema se conecta com o usuário `rotacerta` e a senha `rotacerta_dev`, no banco `rotacerta`. As tabelas não precisam ser criadas à mão, porque a API cria tudo no passo 2.

**Opção A, pelo pgAdmin 4:**

1. Abra o pgAdmin e conecte em *Servers → PostgreSQL* com a senha do usuário `postgres`.
2. Clique com o botão direito em *Databases → postgres* e abra o *Query Tool*.
3. Cole os comandos abaixo, **selecione uma linha por vez** e execute com **F5**. Se executar os dois juntos, aparece o erro `CREATE DATABASE cannot run inside a transaction block` e nada é criado.

   ```sql
   CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';  -- cria o usuário que a API usa para se conectar
   CREATE DATABASE rotacerta OWNER rotacerta;             -- cria o banco do sistema, com esse usuário como dono
   ```

4. Clique com o botão direito em *Databases* e escolha *Refresh*. O banco `rotacerta` deve aparecer na lista.

**Opção B, pelo terminal.** Troque `18` pela versão do seu PostgreSQL. A senha pedida é a do usuário `postgres`.

PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -c "CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';" -c "CREATE DATABASE rotacerta OWNER rotacerta;"   # conecta como postgres e executa os dois comandos separadamente, criando o usuário e o banco
```

Git Bash:

```bash
winpty "/c/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -h localhost -c "CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';" -c "CREATE DATABASE rotacerta OWNER rotacerta;"   # o winpty permite que o psql peça a senha dentro do Git Bash; o restante cria o usuário e o banco
```

A saída esperada é `CREATE ROLE` seguido de `CREATE DATABASE`. Se aparecer `role "rotacerta" already exists`, o usuário já foi criado antes e você pode seguir.

### Passo 2. Subir a API (terminal 1)

PowerShell:

```powershell
cd backend                         # entra na pasta da API
python -m venv .venv               # cria o ambiente virtual do Python (só na primeira vez)
.venv\Scripts\Activate.ps1         # ativa o ambiente virtual; aparece (.venv) no início da linha
pip install -r requirements.txt    # instala as dependências da API (na primeira vez e sempre que o arquivo mudar)
uvicorn app.main:app --reload      # sobe a API em http://localhost:8000 e reinicia sozinha quando o código muda
```

Git Bash:

```bash
cd backend                         # entra na pasta da API
python -m venv .venv               # cria o ambiente virtual do Python (só na primeira vez)
source .venv/Scripts/activate      # ativa o ambiente virtual; aparece (.venv) no início da linha
pip install -r requirements.txt    # instala as dependências da API (na primeira vez e sempre que o arquivo mudar)
uvicorn app.main:app --reload      # sobe a API em http://localhost:8000 e reinicia sozinha quando o código muda
```

Na primeira execução, a API cria as tabelas a partir de `database/schema.sql` e cadastra os dados de demonstração. Deixe esse terminal aberto enquanto estiver usando o sistema.

Se o seu PostgreSQL usar outra porta, outro usuário ou outra senha, crie o arquivo `backend/.env` e ajuste a variável `DATABASE_URL`:

```bash
cp .env.example .env               # dentro de backend: cria o backend/.env a partir do modelo; depois edite o DATABASE_URL
```

#### Modo GPU (opcional, só com GPU NVIDIA)

Com o ambiente virtual ativado, dentro de `backend` (igual no PowerShell e no Git Bash):

```bash
pip install -r requirements-gpu.txt                                  # instala o CuPy e as bibliotecas do CUDA pelo pip (não precisa instalar o CUDA Toolkit)
python -c "from app.optimizer import gpu; print(gpu.status())"       # confere se a GPU foi encontrada e se o kernel CUDA compilou
```

A segunda linha deve mostrar `available=True` e o nome da GPU. Depois disso, reinicie a API: o modo **GPU (CUDA)** fica disponível nas telas Rotas e Desempenho. Sem GPU, o comando mostra o motivo e o sistema continua com os modos de CPU.

### Passo 3. Subir o frontend (terminal 2)

Abra outro terminal na raiz do repositório. Os comandos são iguais no PowerShell e no Git Bash:

```bash
cd frontend                        # entra na pasta do frontend
npm install                        # instala as dependências do frontend (na primeira vez e sempre que o package.json mudar)
npm run dev                        # sobe o sistema em http://localhost:5173
```

### Passo 4. Acessar o sistema

Com a API e o frontend rodando:

| Serviço | Endereço |
| --- | --- |
| Sistema | http://localhost:5173 |
| Rotas do dia no mapa (administrador e atendente) | http://localhost:5173/rotas |
| Comparação de desempenho do otimizador (administrador) | http://localhost:5173/desempenho |
| Documentação interativa da API | http://localhost:8000/docs |
| Situação da API e do banco | http://localhost:8000/health (deve mostrar `"database": "connected"`) |

As contas de demonstração usam a senha `rotacerta123`:

| Perfil | E-mail |
| --- | --- |
| Administrador | admin@rotacerta.com.br |
| Atendente | atendente@rotacerta.com.br |
| Entregador | entregador@rotacerta.com.br |

Para parar a API ou o frontend, aperte `Ctrl+C` no terminal correspondente.

### Passo 5. Consultar os dados no PostgreSQL

**Pelo pgAdmin 4:** vá em *Servers → PostgreSQL → Databases → rotacerta → Schemas → public → Tables*. Clique com o botão direito numa tabela e escolha *View/Edit Data → All Rows*.

**Pelo terminal.** A senha pedida é `rotacerta_dev`.

PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U rotacerta -h localhost -d rotacerta   # abre o psql conectado ao banco do sistema
```

Git Bash:

```bash
winpty "/c/Program Files/PostgreSQL/18/bin/psql.exe" -U rotacerta -h localhost -d rotacerta   # abre o psql conectado ao banco do sistema
```

Dentro do psql:

```sql
\dt                                  -- lista as tabelas do banco
SELECT * FROM orders;                -- mostra os pedidos cadastrados
SELECT * FROM order_status_history;  -- mostra o histórico de mudanças de situação dos pedidos
SELECT * FROM optimization_runs;     -- mostra as execuções registradas do otimizador
\q                                   -- sai do psql
```

Tabelas do sistema: `establishments`, `users`, `couriers`, `customers`, `orders`, `order_status_history`, `routes`, `route_stops` e `optimization_runs`.

## Nas próximas vezes

O banco já existe e as dependências já estão instaladas, então basta subir a API e o frontend.

Terminal 1 (API), no PowerShell:

```powershell
cd backend                         # entra na pasta da API
.venv\Scripts\Activate.ps1         # ativa o ambiente virtual
uvicorn app.main:app --reload      # sobe a API
```

Terminal 1 (API), no Git Bash:

```bash
cd backend                         # entra na pasta da API
source .venv/Scripts/activate      # ativa o ambiente virtual
uvicorn app.main:app --reload      # sobe a API
```

Terminal 2 (frontend), igual nos dois:

```bash
cd frontend                        # entra na pasta do frontend
npm run dev                        # sobe o frontend
```

Depois de um `git pull` que altere `requirements.txt` ou `package.json`, rode de novo o `pip install -r requirements.txt` ou o `npm install`.

## Testes automatizados

Os testes do backend usam, por padrão, um banco SQLite em memória, então não precisam do PostgreSQL rodando. Execute a partir da **raiz do repositório**.

PowerShell:

```powershell
backend\.venv\Scripts\Activate.ps1               # ativa o ambiente virtual da API
pip install -r backend/requirements-dev.txt      # instala as dependências de teste (só na primeira vez)
python -m unittest discover backend/tests -v     # roda todos os testes e mostra o resultado de cada um
```

Git Bash:

```bash
source backend/.venv/Scripts/activate            # ativa o ambiente virtual da API
pip install -r backend/requirements-dev.txt      # instala as dependências de teste (só na primeira vez)
python -m unittest discover backend/tests -v     # roda todos os testes e mostra o resultado de cada um
```

### Mesma suíte no PostgreSQL

Com `TEST_DATABASE_URL` definida, os mesmos testes rodam no PostgreSQL real. Cada teste apaga e recria o schema `rotacerta_testes_automatizados` aplicando `database/schema.sql`; o schema `public`, com os dados de desenvolvimento, não é alterado.

PowerShell:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta"   # aponta os testes para o PostgreSQL
python -m unittest discover backend/tests -v                                                        # roda a suíte no PostgreSQL (leva cerca de 2 minutos)
Remove-Item Env:TEST_DATABASE_URL                                                                   # volta ao SQLite em memória
```

Git Bash:

```bash
TEST_DATABASE_URL="postgresql+psycopg://rotacerta:rotacerta_dev@localhost:5432/rotacerta" python -m unittest discover backend/tests -v   # roda a suíte no PostgreSQL só neste comando
```

### Testes do frontend

```bash
cd frontend                                                  # entra na pasta do frontend
node --test src/sprint08.test.mjs src/sprint09.test.mjs      # testa CSV, navegação, destino após login, erros da API e validações
npm run build                                                # confere os tipos e gera a versão de produção
```

### Casos de teste na aplicação real (Sprint 09)

Os 61 casos funcionais, de validação e de navegação rodam no Chrome contra a aplicação ligada a um schema isolado do PostgreSQL. Terminal 1, na raiz:

```powershell
.\backend\.venv\Scripts\python.exe tools/run_test_environment.py                       # recria o schema sprint09_testes e sobe API (8019) e sistema (5189)
```

Terminal 2, na raiz:

```powershell
.\backend\.venv\Scripts\python.exe tools/documentation/capture_sprint09_evidence.py    # executa os casos e grava resultados e capturas em docs/sprint-09
```

Requer o Google Chrome instalado. O schema `public` não é alterado. Detalhes em [`docs/sprint-09/README.md`](docs/sprint-09/README.md).

### Release Candidate e evidências da Sprint 10

Com o ambiente virtual ativado, na raiz, instale as dependências opcionais e
inicie o ambiente isolado. `POSTGRES_URL` pode apontar para outro PostgreSQL;
sem essa variável, usa o banco local `rotacerta` da configuração de exemplo.

```bash
pip install -r backend/requirements-docs.txt
python tools/run_test_environment.py --schema sprint10_testes --api-port 8020 --web-port 5190
```

Esse comando **recria** somente o schema descartável `sprint10_testes`. Em outro
terminal, com o mesmo ambiente virtual ativado:

```bash
python tools/documentation/capture_sprint10_evidence.py
python tools/documentation/export_api_docs.py
```

O roteiro executa os casos e grava evidências novas em `docs/sprint-10`. Sem CUDA,
o caso de GPU fica como não executado e os modos de CPU continuam sendo
verificados. A suíte PostgreSQL inclui os dois testes de concorrência da Sprint 10.
Para inspecionar banco, contrato e persistência em nova conexão, configure
`DATABASE_URL` para o schema `sprint10_testes` e execute
`python tools/documentation/verify_release.py`. Exemplos para Bash/macOS/Linux
estão em [`docs/sprint-10/README.md`](docs/sprint-10/README.md).

O guia da API, com exemplos e catálogo de endpoints, está em
[`docs/api/README.md`](docs/api/README.md). Para reconstruir o PDF cumulativo,
use `python tools/documentation/build_sprint10_document.py` após gerar as evidências.

### Preparação da entrega e manuais da Sprint 11

Para os registros atuais, use um schema e portas próprios; isso preserva as
pastas de evidências históricas:

```bash
python tools/run_test_environment.py --schema sprint11_testes --api-port 8021 --web-port 5191
```

Em outro terminal, com o mesmo ambiente virtual ativado:

```bash
python tools/documentation/capture_sprint11_evidence.py
python tools/documentation/export_api_docs.py --evidence-dir docs/sprint-11/evidencias
```

O roteiro repete os fluxos principais e captura as telas usadas nos manuais.
Para a inspeção, configure `DATABASE_URL` para o schema `sprint11_testes` e
`API_URL=http://127.0.0.1:8021`, depois execute
`python tools/documentation/verify_release.py --evidence-dir docs/sprint-11/evidencias`.
O PDF completo é reconstruído com `python tools/documentation/build_sprint11_document.py`.
O [registro da Sprint 11](docs/sprint-11/README.md) descreve resultados e pendências.

## Recomeçar com o banco limpo

Pare a API com `Ctrl+C`. No pgAdmin, conectado como `postgres`, execute uma linha por vez:

```sql
DROP DATABASE rotacerta;                    -- apaga o banco do sistema com todos os dados
CREATE DATABASE rotacerta OWNER rotacerta;  -- cria o banco de novo, vazio
```

Na próxima vez que a API subir, ela recria as tabelas e os dados de demonstração.

## Problemas comuns

| Erro | Causa e solução |
| --- | --- |
| `CREATE DATABASE cannot run inside a transaction block` | Os dois comandos do passo 1 foram executados juntos no pgAdmin. Selecione e execute uma linha por vez. |
| `autenticação do tipo senha falhou para o usuário "rotacerta"` | O usuário `rotacerta` não foi criado ou está com outra senha. Refaça o passo 1. |
| `bash: .venvScriptsActivate.ps1: command not found` | Um comando do PowerShell foi usado no Git Bash. Use `source .venv/Scripts/activate`. |
| `Set-ExecutionPolicy: command not found` | Esse comando é só do PowerShell e não é necessário no Git Bash. |
| PowerShell diz que "a execução de scripts foi desabilitada" | Rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e ative o ambiente de novo. |
| `/health` mostra o banco desconectado | O PostgreSQL não está rodando ou o `DATABASE_URL` aponta para a porta errada. Confira o serviço do PostgreSQL e o `backend/.env`. |
| A porta 5432 já está em uso (Docker) | Já existe um PostgreSQL na máquina. Troque `POSTGRES_PORT` para `5433` no `.env`. |

## Verificação da versão final (Sprint 12)

Use a tag `v1.0.0` para reproduzir a entrega congelada. Com PostgreSQL
configurado e dependências instaladas conforme os passos anteriores:

```bash
python tools/documentation/verify_code_freeze.py
python tools/run_test_environment.py --schema sprint12_testes --api-port 8022 --web-port 5192
```

O segundo comando recria somente o schema descartável `sprint12_testes`. Em
outro terminal, execute `python tools/documentation/capture_sprint12_evidence.py`.
O ensaio usa outro schema, `sprint120_testes`, e portas 8023/5193; consulte
`docs/sprint-12/ENSAIO_APRESENTACAO.md` antes de executar seu roteiro.
