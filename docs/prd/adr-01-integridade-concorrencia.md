# ADR-01: Integridade e concorrência em reservas

**Status:** Proposta

## Contexto

O sistema precisa impedir sobreposição de reservas em salas, professores e materiais, mesmo com múltiplas solicitações concorrentes. O comportamento esperado está definido em RN01 a RN04, RN06 e RN07, e em FR-04, FR-06, FR-07, FR-09 e FR-10.

## Decisão

Usar transações de banco e validação de disponibilidade antes da confirmação final, com regra de exclusão e checagens de estoque para material.

## Alternativas consideradas

- validar somente no frontend
- confirmar sem transação e depender de race condition
- usar apenas aplicação em memória sem persistência transacional

## Consequências

- reduz sobreposição indevida
- aumenta consistência em reservas concorrentes
- exige mais complexidade de código e testes de concorrência

## Requisitos derivados da matriz

- FR: FR-04, FR-06, FR-07, FR-09, FR-10
- RN: RN01, RN02, RN03, RN04, RN06, RN07
- NFR: NFR-03, NFR-04, NFR-05, NFR-09, NFR-11
- Diagramas: [modelagem-estatica.md](./modelagem-estatica.md), [modelagem-dinamica.md](./modelagem-dinamica.md)
