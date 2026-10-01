# RotaCerta

Sistema web de roteirização de entregas para pequenos negócios locais. Centraliza o cadastro de clientes, pedidos e entregadores e calcula rotas otimizadas (vizinho mais próximo + 2-opt) com execução sequencial e paralela.

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
- **Otimização:** módulo Python com execução sequencial e paralela

## Como rodar localmente

Há duas formas: com Docker (mais simples) ou instalando tudo na máquina.

### Opção 1: com Docker

Pré-requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env        # no PowerShell: copy .env.example .env
docker compose up --build
```

Se já houver um PostgreSQL usando a porta 5432, troque `POSTGRES_PORT` para `5433` no `.env`.

### Opção 2: sem Docker

Pré-requisitos: Python 3.12+, Node.js 20+ e PostgreSQL 16+.

**1. Criar o usuário e o banco** (só na primeira vez). Conectado como `postgres` no pgAdmin ou no `psql`, execute **um comando por vez** (o `CREATE DATABASE` não roda junto com outro comando):

```sql
CREATE ROLE rotacerta LOGIN PASSWORD 'rotacerta_dev';
CREATE DATABASE rotacerta OWNER rotacerta;
```

**2. Subir a API** (terminal 1):

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Git Bash: source .venv/Scripts/activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Na primeira execução a API cria as tabelas (`database/schema.sql`) e os dados de demonstração. Para usar outra porta, usuário ou senha do banco, copie `backend/.env.example` para `backend/.env` e ajuste `DATABASE_URL`.

> Se o PowerShell bloquear o `Activate.ps1`, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**3. Subir o frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev
```

### Acesso

| Serviço | Endereço |
| --- | --- |
| Sistema | http://localhost:5173 |
| Documentação da API | http://localhost:8000/docs |
| Status da API e do banco | http://localhost:8000/health |

Contas de demonstração (senha `rotacerta123`):

| Perfil | E-mail |
| --- | --- |
| Administrador | admin@rotacerta.com.br |
| Atendente | atendente@rotacerta.com.br |
| Entregador | entregador@rotacerta.com.br |

### Testes

```bash
pip install -r backend/requirements-dev.txt
python -m unittest discover backend/tests -v
```

## Documentação

- Documento cumulativo das Sprints: [`output/pdf/Grupo_04_RotaCerta_Sprints_01_a_04.pdf`](output/pdf/Grupo_04_RotaCerta_Sprints_01_a_04.pdf)
- Documento de abertura (Sprint 1): [`RotaCerta_Documento_Abertura_Sprint1.pdf`](RotaCerta_Documento_Abertura_Sprint1.pdf)
- Evidências por Sprint: [`docs/`](docs/)
- Banco de dados: [`database/README.md`](database/README.md)
- Guia de contribuição: [`CONTRIBUTING.md`](CONTRIBUTING.md)
