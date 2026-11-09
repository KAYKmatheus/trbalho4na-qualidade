# ADR-05: API e separação de camadas

**Status:** Proposta

## Contexto

O sistema deve separar interface, aplicação e dados para não misturar regra de negócio com apresentação, além de documentar os fluxos públicos. Isso aparece em FR-14 e FR-15, e em NFR-06, NFR-07, NFR-08 e NFR-10.

## Decisão

Organizar a solução em camadas explícitas com API como fronteira de entrada e regras de negócio centralizadas em camada de aplicação.

## Alternativas consideradas

- regra de negócio integrada ao frontend
- lógica espalhada em scripts e templates
- API sem documentação mínima

## Consequências

- facilita manutenção e evolução
- reduz acoplamento de regras a telas
- exige disciplina de contratos e documentação

## Requisitos derivados da matriz

- FR: FR-14, FR-15
- RN: RN08, RN09, RN10
- NFR: NFR-06, NFR-07, NFR-08, NFR-10, NFR-12
- Diagramas: [modelagem-estatica.md](./modelagem-estatica.md), [modelagem-dinamica.md](./modelagem-dinamica.md)
