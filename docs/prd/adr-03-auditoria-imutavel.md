# ADR-03: Auditoria imutável e conflito evitado

**Status:** Proposta

## Contexto

O histórico precisa registrar criação, alteração, aprovação, rejeição, bloqueio, cancelamento e tentativas recusadas por conflito. Isso está presente em RN08, FR-11, FR-12 e FR-13, além de NFR-09.

## Decisão

Persistir registros em tabela de auditoria append-only e registrar `CONFLITO_EVITADO` para tentativas recusadas por conflito, com recurso, intervalo e motivo.

## Alternativas consideradas

- gravar somente sucesso de operações
- gravar auditoria em log textual sem estrutura
- permitir UPDATE/DELETE em registros históricos

## Consequências

- aumenta confiabilidade e conformidade
- melhora relatórios e análise de conflitos
- exige disciplina de escrita e proteção de integridade no banco

## Requisitos derivados da matriz

- FR: FR-11, FR-12, FR-13
- RN: RN08
- NFR: NFR-01, NFR-02, NFR-05, NFR-09, NFR-11
- Diagramas: [modelagem-estatica.md](./modelagem-estatica.md), [modelagem-dinamica.md](./modelagem-dinamica.md)
