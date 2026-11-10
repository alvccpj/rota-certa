# Code Freeze da versão final

Grupo 04 - RotaCerta | Versão 1.0.0 | Tag de entrega: **v1.0.0**.
Registro preparado em 10/11/2026, antes do prazo de 28/11/2026 às 23h59.

## 1 Escopo e identificação

O congelamento encerra a inclusão de funcionalidades para esta entrega. A versão
final mantém autenticação e perfis, clientes/usuários, pedidos, atribuição,
rotas, entregas, painel, relatórios/CSV, histórico e comparação de processamento.
O banco permanece com nove tabelas; o contrato possui 37 operações HTTP.

Repositório: https://github.com/alvccpj/rota-certa

Código congelado: https://github.com/alvccpj/rota-certa/tree/v1.0.0

Referência Git verificável: `refs/tags/v1.0.0`. A tag anotada identifica o commit
publicado da entrega. Seu SHA é obtido por `git rev-parse v1.0.0^{commit}`;
este documento não fixa o hash de um commit que inclui o próprio PDF, evitando
uma referência circular. O manifesto `evidencias/code_freeze.json` registra os
SHA-256 dos arquivos executáveis, dependências, configurações e OpenAPI listados.
O manifesto não substitui a tag e não pretende cobrir todo o repositório.

## 2 Critérios de congelamento

| Critério | Evidência de liberação |
| --- | --- |
| Fluxos e regras principais | Suítes backend PostgreSQL/SQLite, frontend e casos de navegador |
| Persistência e contrato | Nove tabelas e 14 FKs conferidas; nova sessão API comparada ao SQL; OpenAPI idêntico |
| Correções conhecidas | BUG-01 a BUG-12 cobertos pelo histórico e regressões; BUG-13 reproduzido e corrigido nesta Sprint |
| Interface | Capturas atuais, mobile 320/390/768 px e navegação entre mapas |
| Preparação técnica | Build, configuração Compose e backup/restauração exercitados |
| Apresentação | Ensaio técnico e roteiros dos dois formatos preparados |
| Reprodutibilidade | Versões alinhadas em backend/frontend/OpenAPI e manifesto conferido |

A liberação se refere ao escopo e aos cenários executados. Não representa ausência
matemática de qualquer defeito. Aceitação externa, ensaio com falas e gravação
são atividades humanas pendentes e estão registradas separadamente.

## 3 Reprodução da versão congelada

```bash
git fetch origin --tags
git switch --detach v1.0.0
git rev-parse 'v1.0.0^{commit}'
python tools/documentation/verify_code_freeze.py
```

Usar o Python do ambiente com as dependências instaladas. Em seguida, seguir o
README e o Manual Técnico para configurar PostgreSQL, variáveis locais, API e
frontend. A tag não inclui .env privado, banco local, dependências instaladas
ou dados operacionais. A semente é somente de demonstração.

O verificador compara conteúdo e conjunto dos arquivos cobertos pelo manifesto;
qualquer inclusão/remoção no escopo ou alteração de conteúdo falha. Durante a
preparação da versão, `--write` cria o manifesto; após publicar v1.0.0, não o
recriar para esconder divergências. Conferir o checkout correto e o diff.

## 4 Regras após o congelamento

Nenhum recurso novo entra em v1.0.0. A tag publicada não deve ser movida ou
sobrescrita. Correções indispensáveis devem ter defeito reproduzível, impacto,
justificativa, revisão e validação dos fluxos afetados. Dúvidas de apresentação,
novas telas e melhorias opcionais ficam fora da versão congelada.

Procedimento de correção crítica: criar branch `codex/hotfix-1.0.1` a partir da
versão final; registrar a reprodução; aplicar a correção mínima; repetir a
regressão e os testes pertinentes; revisar com a equipe; atualizar versão,
manifesto, documentação e gerar uma nova tag de correção, sem substituir v1.0.0.
O gerador do manifesto atual fixa 1.0.0 e precisa ser ajustado explicitamente
para uma nova versão, mantendo o registro anterior. O Scrum Master coordena a
revisão; a equipe deve confirmar o resultado na máquina de apresentação.

Caso a nova versão falhe no ensaio, retornar ao checkout da tag estável conhecida
e usar uma base descartável ou backup compatível. Não usar reset destrutivo ou
restaurar dados de produção sem procedimento próprio. Não há implantação de
produção realizada por esta Sprint.

## 5 Limites aceitos e justificativa

CUDA está implementado, mas depende de NVIDIA/CUDA, ausentes neste macOS ARM64.
CPU sequencial e paralela permanecem funcionais; não é necessário simular GPU
para demonstrar a otimização. A validação CUDA da Sprint 09 é histórica.

Roteirização usa distância Haversine e heurística, sem trânsito, GPS ou garantia
de ótimo/janela. Esses limites correspondem ao produto implementado e aparecem
na interface e nos manuais. Serviços de mapa/geocodificação dependem de rede;
coordenadas podem ser informadas manualmente. Carga alta, combinações amplas de
escritas concorrentes e infraestrutura de produção não foram homologadas.
