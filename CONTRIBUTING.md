# Guia de contribuição

O desenvolvimento deve partir da `master` atualizada. Alterações entram por pull request após revisão de pelo menos outro integrante.

## Branches

- `sprint/NN-descricao` para organizar a entrega de uma Sprint;
- `feature/descricao` para novas funcionalidades;
- `fix/descricao` para correções;
- `docs/descricao` para documentação.
- `codex/descricao` para alterações preparadas no ambiente Codex, como as entregas das Sprints 10 e 11.

As branches `dev/alvaro`, `dev/arthur` e `dev/vinicius` identificam os ambientes pessoais da equipe. O trabalho cotidiano deve preferir branches curtas por tarefa, criadas a partir da Sprint ou da `master`.

## Commits

Use mensagens objetivas, por exemplo:

- `feat: adiciona cadastro de pedidos`
- `fix: corrige cálculo da distância total`
- `docs: atualiza arquitetura da Sprint 02`
- `test: cobre transições de status do pedido`

## Fluxo de revisão

1. Atualize a branch base.
2. Crie uma branch por tarefa.
3. Faça commits pequenos e relacionados.
4. Abra um pull request com objetivo e evidências de validação.
5. Solicite revisão de outro integrante.
6. Faça merge somente com a verificação concluída.

## Documentação e arquivos da entrega

O índice `docs/README.md` identifica os documentos vigentes. Atualize o Manual
do Usuário quando mudar a operação e o Manual Técnico/contrato quando mudar
configuração ou API. A documentação final deve refletir requisitos e regras
implementados, separando limites de escopo de defeitos.

Guarde evidências novas na Sprint correspondente; não sobrescreva resultados
históricos. Manuais em Markdown, diagramas, capturas selecionadas e PDFs
cumulativos de entrega são artefatos intencionais do repositório. Caches,
ambientes virtuais, bases locais, builds e arquivos de QA ficam fora do Git.

Não adicione credenciais reais, tokens, `.env` ou backups. Use `.env.example`
somente para modelos e valores públicos de demonstração. A verificação local
de padrões e links pode ser repetida com `python tools/documentation/audit_repository.py`.
Ela não substitui a revisão humana de conteúdo e do histórico.
