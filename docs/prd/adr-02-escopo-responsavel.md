# ADR-02: Escopo do Responsável

**Status:** Proposta

## Contexto

A aprovação e a validação de recursos restritos e de docentes dependem de um responsável autorizado para o recurso envolvido. Isso é formalizado em RN05, RN09 e RN10, além de FR-01, FR-08, FR-16 e FR-11.

## Decisão

Modelar o escopo como tabela de associação entre `responsavel_id` e `recurso` e validar a decisão no servidor antes de aceitar a aprovação.

## Alternativas consideradas

- escopo embutido em perfil de usuário
- regra ad hoc por tela
- aprovação global para qualquer responsável

## Consequências

- reduz decisões fora do escopo
- exige manutenção da tabela de alocação
- aumentará rastreabilidade e auditoria

## Requisitos derivados da matriz

- FR: FR-01, FR-08, FR-11, FR-16
- RN: RN05, RN09, RN10
- NFR: NFR-01, NFR-02, NFR-06, NFR-09, NFR-11
- Diagramas: [modelagem-estatica.md](./modelagem-estatica.md), [modelagem-dinamica.md](./modelagem-dinamica.md)
