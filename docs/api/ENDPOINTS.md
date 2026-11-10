# Catálogo dos endpoints

Contrato da versão `1.0.0`, gerado por `tools/documentation/export_api_docs.py`.

Consulte [o guia e exemplos](README.md) e [o contrato OpenAPI completo](openapi.json). Os modelos do contrato detalham todos os campos, tipos, limites, valores padrão e obrigatoriedade.

ADMIN = administrador; ATTENDANT = atendente; COURIER = entregador. O perfil não substitui as regras sobre estabelecimento e propriedade do registro.

## POST /auth/login

**Acesso:** Público.

**Corpo JSON:** `LoginIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | TokenOut |
| 422 | HTTPValidationError |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /auth/register

**Acesso:** Público.

Cadastra um novo estabelecimento e o seu primeiro administrador.

**Corpo JSON:** `RegisterIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 201 | TokenOut |
| 422 | HTTPValidationError |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /auth/me

**Acesso:** Usuário autenticado.

| HTTP | Resposta |
| --- | --- |
| 200 | UserOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /users

**Acesso:** ADMIN.

| HTTP | Resposta |
| --- | --- |
| 200 | lista de UserOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /users

**Acesso:** ADMIN.

**Corpo JSON:** `UserCreate` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 201 | UserOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /users/{user_id}

**Acesso:** ADMIN.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `user_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 200 | UserOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PUT /users/{user_id}

**Acesso:** ADMIN.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `user_id` | path | Sim | `{"type": "integer"}` |

**Corpo JSON:** `UserUpdate` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | UserOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## DELETE /users/{user_id}

**Acesso:** ADMIN.

Desativa o usuário; o registro é preservado por causa do histórico.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `user_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 204 | Sem corpo |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /couriers

**Acesso:** ADMIN, ATTENDANT.

| HTTP | Resposta |
| --- | --- |
| 200 | lista de CourierOption |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PATCH /couriers/me/availability

**Acesso:** COURIER.

O entregador informa se está disponível para receber pedidos.

**Corpo JSON:** `AvailabilityIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | CourierOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /customers

**Acesso:** ADMIN, ATTENDANT.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `q` | query | Não | `{"anyOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de CustomerOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /customers

**Acesso:** ADMIN, ATTENDANT.

**Corpo JSON:** `CustomerIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 201 | CustomerOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /customers/{customer_id}

**Acesso:** ADMIN, ATTENDANT.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `customer_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 200 | CustomerOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PUT /customers/{customer_id}

**Acesso:** ADMIN, ATTENDANT.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `customer_id` | path | Sim | `{"type": "integer"}` |

**Corpo JSON:** `CustomerIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | CustomerOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## DELETE /customers/{customer_id}

**Acesso:** ADMIN.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `customer_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 204 | Sem corpo |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /orders/auto-assign

**Acesso:** ADMIN, ATTENDANT.

| HTTP | Resposta |
| --- | --- |
| 200 | AutoAssignOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /orders

**Acesso:** Usuário autenticado.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `status` | query | Não | `{"anyOf": [{"enum": ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"], "type": "string"}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de OrderOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /orders

**Acesso:** ADMIN, ATTENDANT.

**Corpo JSON:** `OrderIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 201 | OrderOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /orders/{order_id}

**Acesso:** Usuário autenticado.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `order_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 200 | OrderDetailOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PUT /orders/{order_id}

**Acesso:** ADMIN, ATTENDANT.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `order_id` | path | Sim | `{"type": "integer"}` |

**Corpo JSON:** `OrderIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | OrderOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## DELETE /orders/{order_id}

**Acesso:** ADMIN.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `order_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 204 | Sem corpo |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PATCH /orders/{order_id}/status

**Acesso:** Usuário autenticado.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `order_id` | path | Sim | `{"type": "integer"}` |

**Corpo JSON:** `StatusIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | OrderOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /geocode

**Acesso:** ADMIN, ATTENDANT.

Sugere coordenadas para um endereço digitado no cadastro do pedido.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `q` | query | Sim | `{"type": "string", "minLength": 5, "maxLength": 200}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de GeocodeResult |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /establishment/depot

**Acesso:** ADMIN, ATTENDANT.

| HTTP | Resposta |
| --- | --- |
| 200 | DepotOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PUT /establishment/depot

**Acesso:** ADMIN.

Define o endereço e a posição de onde saem e para onde voltam as rotas.

**Corpo JSON:** `DepotIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | DepotOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /routes

**Acesso:** ADMIN, ATTENDANT.

Rotas do dia (hoje, se a data não for informada) e as que ainda estão em andamento.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `date` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | RoutesOverviewOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /routes/generate

**Acesso:** ADMIN, ATTENDANT.

**Corpo JSON:** `RouteGenerateIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | RouteGenerationOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /routes/me

**Acesso:** COURIER.

| HTTP | Resposta |
| --- | --- |
| 200 | MyRouteOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## PATCH /routes/{route_id}/start

**Acesso:** Usuário autenticado.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `route_id` | path | Sim | `{"type": "integer"}` |

| HTTP | Resposta |
| --- | --- |
| 200 | RouteOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /optimizer/capabilities

**Acesso:** ADMIN, ATTENDANT.

Núcleos de CPU disponíveis e se o modo GPU pode ser usado nesta máquina.

| HTTP | Resposta |
| --- | --- |
| 200 | CapabilitiesOut |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /optimizer/benchmark

**Acesso:** ADMIN.

Executa os modos sobre a mesma entrada e registra tempo, speedup e eficiência.

**Corpo JSON:** `BenchmarkIn` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | BenchmarkOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /optimizer/runs

**Acesso:** ADMIN.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `limit` | query | Não | `{"type": "integer", "maximum": 500, "minimum": 1, "default": 100}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de OptimizationRunOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## POST /optimizer/compare

**Acesso:** Público.

Compara o mesmo algoritmo nos modos sequencial e paralelo (entrada livre, da Sprint 02).

**Corpo JSON:** `OptimizationRequest` (veja a definição completa em `components.schemas` no contrato).

| HTTP | Resposta |
| --- | --- |
| 200 | object |
| 422 | HTTPValidationError |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /dashboard/summary

**Acesso:** ADMIN, ATTENDANT.

Consolida pedidos, entregadores, rotas e desempenho no período.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `start` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |
| `end` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | DashboardSummaryOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /dashboard/report

**Acesso:** ADMIN, ATTENDANT.

Lista os dados operacionais usados na exportação CSV da interface.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `start` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |
| `end` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |
| `status` | query | Não | `{"anyOf": [{"enum": ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"], "type": "string"}, {"type": "null"}]}` |
| `q` | query | Não | `{"anyOf": [{"type": "string", "minLength": 1, "maxLength": 100}, {"type": "null"}]}` |
| `courier_id` | query | Não | `{"anyOf": [{"type": "integer", "exclusiveMinimum": 0}, {"type": "null"}]}` |
| `priority` | query | Não | `{"anyOf": [{"type": "integer", "maximum": 3, "minimum": 1}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de DashboardReportRowOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /dashboard/history

**Acesso:** ADMIN, ATTENDANT.

Exibe o histórico operacional integrado para auditoria e acompanhamento.

| Parâmetro | Local | Obrigatório | Tipo e limites |
| --- | --- | --- | --- |
| `start` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |
| `end` | query | Não | `{"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}` |
| `type` | query | Não | `{"anyOf": [{"enum": ["ORDER_STATUS", "OPTIMIZATION"], "type": "string"}, {"type": "null"}]}` |
| `status` | query | Não | `{"anyOf": [{"enum": ["PENDING", "ASSIGNED", "IN_ROUTE", "DELIVERED", "CANCELLED"], "type": "string"}, {"type": "null"}]}` |
| `q` | query | Não | `{"anyOf": [{"type": "string", "minLength": 1, "maxLength": 100}, {"type": "null"}]}` |

| HTTP | Resposta |
| --- | --- |
| 200 | lista de OperationalHistoryEventOut |
| 422 | HTTPValidationError |
| 401 | Sessão ausente, inválida, expirada ou usuário desativado |
| 403 | Perfil sem permissão |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.

## GET /health

**Acesso:** Público.

| HTTP | Resposta |
| --- | --- |
| 200 | Successful Response |

Conflitos de negócio (409), registro não visível (404) e indisponibilidade (503) dependem da operação; veja o guia de erros e as regras de negócio.
