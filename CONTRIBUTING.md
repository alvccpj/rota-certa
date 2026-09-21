# Guia de contribuição

O desenvolvimento deve partir da `master` atualizada. Alterações entram por pull request após revisão de pelo menos outro integrante.

## Branches

- `sprint/NN-descricao` para organizar a entrega de uma Sprint;
- `feature/descricao` para novas funcionalidades;
- `fix/descricao` para correções;
- `docs/descricao` para documentação.

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
