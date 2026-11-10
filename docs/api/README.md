# API RotaCerta

Versão candidata `0.10.0-rc.1`. Base local: `http://localhost:8000`.
Não há prefixo `/api`. No ambiente isolado da Sprint 10, a base é `http://127.0.0.1:8020`.

- [Catálogo completo de rotas, métodos, parâmetros, perfis e modelos de resposta](ENDPOINTS.md).
- [Contrato OpenAPI 3.1 versionado](openapi.json), com todos os modelos de entrada e saída.
- Swagger interativo, com a API ligada: <http://localhost:8000/docs>.
- ReDoc: <http://localhost:8000/redoc>. Contrato servido: <http://localhost:8000/openapi.json>.

## Autenticação e permissões

`POST /auth/login` recebe JSON com `email` e `password`. Retorna `access_token`,
`token_type` e `user`. Envie `Authorization: Bearer <access_token>` nas operações
protegidas. A duração padrão é 480 minutos, configurável por `ACCESS_TOKEN_MINUTES`.
No Swagger, faça login, copie somente o token e clique em **Authorize**.
Não existe endpoint de refresh ou logout: o frontend encerra a sessão removendo o token local.

ADMIN gerencia usuários, ponto de saída e desempenho; ADMIN e ATTENDANT operam
clientes, pedidos, atribuição, rotas, painel e consultas; COURIER consulta suas
entregas, altera a própria disponibilidade e executa sua rota. A autorização lê o
perfil e a ativação no banco a cada chamada. Consultas operacionais respeitam o
estabelecimento da conta; entregadores veem apenas os pedidos atribuídos a eles.
O início de rota também verifica a propriedade e a situação da rota.

São públicas: autenticação/cadastro, `/health`, documentação e o comparador
experimental `POST /optimizer/compare`. Este último calcula sobre coordenadas
fornecidas no corpo, sem consultar ou gravar pedidos; não confundir com
`POST /optimizer/benchmark`, restrito a ADMIN e persistido.

## Convenções de entrada e saída

Corpos de entrada e respostas usam JSON, exceto respostas 204, sem corpo.
`PUT` recebe o modelo completo de edição; não é atualização parcial.
IDs são inteiros positivos nas entradas em que o modelo exige essa restrição;
IDs da URL inexistentes ou de outro estabelecimento retornam 404.
Datas de período usam `AAAA-MM-DD`; janelas de entrega usam ISO 8601 com fuso,
por exemplo `2026-11-14T15:00:00-03:00`. Envie fuso explicitamente: datas sem
fuso são interpretadas como UTC. Uma nova janela precisa terminar no futuro e
depois do início. Campos monetários não existem; pesos são em kg, distâncias
em km e tempos de execução em ms. Listas não têm paginação; `/optimizer/runs`
aceita `limit` entre 1 e 500 (padrão 100).

Pedidos usam `PENDING`, `ASSIGNED`, `IN_ROUTE`, `DELIVERED`, `CANCELLED`.
Prioridade 1 = alta, 2 = normal e 3 = baixa. O peso deve ser maior que zero e
no máximo 500 kg. Coordenadas devem estar nos limites geográficos; o raio
operacional padrão é 30 km a partir do ponto de saída.

`GET /dashboard/report` retorna JSON. O CSV é produzido pelo frontend a partir
desse resultado; não existe endpoint que devolve CSV.
Os filtros `start`, `end`, `status`, `q`, `courier_id` e `priority` são combináveis
conforme o catálogo. O período padrão vai de seis dias antes até hoje, inclusive;
os limites das consultas são montados em UTC. O máximo é 366 dias por consulta.

## Exemplo completo com curl

Execute em Bash (macOS, Linux ou Git Bash), com API e banco ligados e os dados
de demonstração habilitados. Os identificadores são lidos das respostas.
`python` representa o Python do ambiente virtual ativado. No PowerShell use
`Invoke-RestMethod` ou os mesmos corpos pelo Swagger.

```bash
BASE=http://localhost:8000
TOKEN=$(curl --fail-with-body -s "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@rotacerta.com.br","password":"rotacerta123"}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl --fail-with-body -s "$BASE/auth/me" -H "Authorization: Bearer $TOKEN"

CLIENTE=$(curl --fail-with-body -s "$BASE/customers" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"full_name":"Cliente Demonstração RC","phone":"81999990010"}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["id"])')

curl --fail-with-body -s "$BASE/orders" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"customer_id\":$CLIENTE,\"delivery_address\":\"Rua do Bom Jesus, 197 - Recife\",\"latitude\":-8.0617,\"longitude\":-34.8709,\"weight_kg\":2,\"priority\":1}"

curl --fail-with-body -s -X POST "$BASE/orders/auto-assign" -H "Authorization: Bearer $TOKEN"
curl --fail-with-body -s "$BASE/routes/generate" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"mode":"SEQUENTIAL","workers":1}'

curl --fail-with-body -s "$BASE/orders?status=ASSIGNED" -H "Authorization: Bearer $TOKEN"
curl --fail-with-body -s "$BASE/dashboard/report?priority=1" -H "Authorization: Bearer $TOKEN"
```

Cadastro de cliente e pedido retorna 201. A atribuição retorna 200 com
`{"assigned":[{"order_id":15,"courier_id":1,"courier_name":"Carla Entregadora"}],"skipped":[]}`
(IDs e nome ilustrativos). Em caso de falta de capacidade, `skipped` traz
`order_id` e `reason`, com HTTP 200; isso não representa falha de transação.
É necessário ter ponto de saída e entregadores ativos, disponíveis e com capacidade.
Repetir o cadastro do mesmo cliente/telefone gera 409; reutilize o ID existente.

Com o token do entregador responsável, consulte `GET /routes/me`, leia `route.id`
e envie `PATCH /routes/{route_id}/start` sem corpo. Para cada pedido próprio,
envie `PATCH /orders/{order_id}/status` com `{"status":"DELIVERED"}` depois da
saída para entrega. A confirmação atualiza paradas, rota e histórico.
Administrador/atendente podem cancelar pedido aberto com
`{"status":"CANCELLED","note":"Cliente solicitou cancelamento"}`.

## Erros esperados

| HTTP | Significado e exemplo |
| --- | --- |
| 401 | Sem token, token inválido/expirado ou conta desativada; login incorreto também retorna 401. |
| 403 | Perfil sem permissão; login de usuário desativado retorna 403. |
| 404 | Registro inexistente ou não visível para a conta. |
| 409 | E-mail/cliente duplicado, transição inválida, capacidade insuficiente na atribuição manual, edição de pedido encerrado, troca do ponto de saída durante rota ou GPU solicitada sem suporte. |
| 422 | Campos inválidos, texto vazio, peso fora do limite, janela inválida, cliente/entregador de outro estabelecimento ou ID além do formato do banco. |
| 503 | `/health` com banco indisponível; `/geocode` com serviço externo indisponível. |

Erros de negócio usam `{"detail":"Mensagem em português."}`. Validação do
modelo usa `{"detail":[{"loc":["body","weight_kg"],"msg":"...","type":"..."}]}`.
A UI pode adaptar mensagens de validação; a API preserva o contrato de erro do FastAPI.
A busca de endereço indisponível permite marcar a posição diretamente no mapa.

## Atualizar o contrato

Na raiz, após alterar rotas ou modelos:

```bash
python tools/documentation/export_api_docs.py
```

O exportador importa `app.main:app`, sem inicializar o banco, e gera `openapi.json`
e `ENDPOINTS.md`. O contrato exportado deve coincidir com `GET /openapi.json`.
O guia deve ser revisado quando mudar uma regra de negócio ou autorização.
