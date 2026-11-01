# Checklist de revisão da Sprint 08

Revisão em 01/11/2026. Grupo 04 - RotaCerta.

- [x] RF01 a RF10 mapeados à implementação e limites de escopo explicitados no README desta sprint.
- [x] Atribuição automática integrada a pedidos, entregadores, histórico e planejamento de rotas.
- [x] Esperas e atrasos previstos por janela demonstrados nas paradas; datas normalizadas em UTC.
- [x] Permissões verificadas por perfil e isolamento de dados por estabelecimento/entregador.
- [x] Regras de carga, início de rota e preservação de histórico revisadas.
- [x] Melhorias de confirmação, navegação, estado vazio e uso no celular implementadas.
- [x] Fluxo real de cadastro, atribuição, rota, entrega, painel, histórico e CSV executado.
- [x] Backend: 138 testes aprovados; um ignorado por ausência de CUDA.
- [x] Frontend: 15 testes aprovados; build de produção concluído.
- [x] Auditoria npm: zero vulnerabilidades reportadas na data da revisão.
- [x] PDF cumulativo das Sprints 01 a 08 gerado com identificação da equipe, explicações e evidências.
- [x] Execução local sem Docker documentada com SQLite persistido; configuração PostgreSQL mantida.

## Limites e etapas seguintes

- Testes desta máquina usam SQLite. Concorrência e migração em instância PostgreSQL real não foram demonstradas nesta revisão.
- O teste com GPU real exige equipamento CUDA; o resultado não foi simulado.
- Distâncias são geográficas, sem matriz viária ou trânsito; janelas são previsões e não garantias. OSRM, notificações externas e exportações XLSX/PDF operacionais estão fora do escopo consolidado, com justificativas no documento.
- A aprovação/merge da branch e o envio acadêmico pelo Scrum Master são etapas distintas do push.
- A equipe deve executar o roteiro de demonstração e revisar o documento antes da entrega no Teams.

As evidências reproduzíveis estão em `evidencias/` e `assets/`. O status atual do push é verificado pelo SHA remoto na conclusão da tarefa, sem gravar no próprio commit um identificador circular.
