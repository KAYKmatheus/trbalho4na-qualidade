# ADR-04: Controle de disponibilidade de materiais e recursos

**Status:** Proposta

## Contexto

Materiais e recursos precisam preservar disponibilidade real, incluindo quantidade livre, bloqueios, retirada pendente e devolução. Há suporte em RN06, RN07, FR-03, FR-06, FR-10 e FR-13.

## Decisão

Calcular disponibilidade por leitura de reservas ativas, bloqueios e movimentações de materiais, com regra de exclusão para estoque insuficiente e devolução pendente.

## Alternativas consideradas

- disponibilidade somente por presença de reserva
- ignorar devoluções pendentes
- tratar materiais como recursos exclusivos

## Consequências

- melhora precisão de disponibilidade real
- reduz alocações acima de estoque
- exige regras mais sofisticadas de leitura e transação

## Requisitos derivados da matriz

- FR: FR-03, FR-06, FR-10, FR-13
- RN: RN06, RN07
- NFR: NFR-03, NFR-04, NFR-05, NFR-06, NFR-11
- Diagramas: [modelagem-estatica.md](./modelagem-estatica.md), [modelagem-dinamica.md](./modelagem-dinamica.md)
