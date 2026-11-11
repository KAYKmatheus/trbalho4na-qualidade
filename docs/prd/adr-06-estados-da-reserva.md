# ADR-06: Estados da reserva

## Contexto

O fluxo descrito no enunciado inclui `SOLICITADA`, `APROVADA`, `EM_USO` e
`CONCLUIDA`, além de `REJEITADA`, `CANCELADA` e `NAO_COMPARECEU`. O sistema
também usa `PENDENTE` enquanto aguarda aprovação e `CONFIRMADA` para reservas
que já podem ocupar a disponibilidade, inclusive reservas sem aprovação.

## Opções

1. Manter `CONFIRMADA` como estado distinto entre `APROVADA` e `EM_USO` e como
   estado das reservas que não exigem aprovação.
2. Remover `CONFIRMADA` e representar esses casos com outro estado do fluxo do
   enunciado.

## Decisão

O grupo decidiu manter `CONFIRMADA`. `PENDENTE` permanece para itens que
aguardam aprovação. A lista de estados ativos e a restrição de sobreposição
devem continuar coerentes entre si; materiais são tratados pelo controle de
estoque, enquanto salas e professores permanecem protegidos pela restrição.
