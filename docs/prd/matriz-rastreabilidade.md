# Matriz de rastreabilidade

Liga cada requisito obrigatório do projeto a regras, requisitos, fluxos, tabelas e testes.

Documentos-base: [FR e RN](./requisitos-funcionais-sistema-academico.md), [NFR](./requisitos-nao-funcionais-sistema-academico.md), [DBML](./modelagem-dados-sistema-academico.dbml), [fluxos](./fluxos-sequencia.md), [casos de teste](../qualidade/casos-de-teste.md).

## Requisitos obrigatórios do projeto

| # | Requisito obrigatório | RN | FR | NFR | Fluxo | Tabelas | Casos de teste |
|---|---|---|---|---|---|---|---|
| 1 | Autenticação e autorização por perfil | | FR-01 | NFR-01, NFR-02 | 1 | usuarios | CT-01 a CT-05 |
| 2 | Cadastro e consulta de recursos | RN09 | FR-02 | NFR-02 | 2 | salas, professores, materiais, competencias, recursos_tecnicos, escopos_responsavel | CT-06, CT-07, CT-40 |
| 3 | Pesquisa por tipo, capacidade, localização, competência e disponibilidade | RN02, RN06 | FR-03 | NFR-04 | 3 | salas, professor_competencias, reserva_itens, bloqueios | CT-08, CT-09 |
| 4 | Criação, alteração e cancelamento | RN01 | FR-04, FR-05 | NFR-06 | 4, 9 | reservas, reserva_itens | CT-10 a CT-14 |
| 5 | Detecção de sobreposição, inclusive do professor | RN02, RN03 | FR-06 | NFR-03 | 4 | reserva_itens | CT-15 a CT-18 |
| 6 | Proteção contra dupla reserva simultânea | RN04 | FR-07 | NFR-03, NFR-04 | 5 | reserva_itens | CT-19, CT-20 |
| 7 | Aprovação para recursos restritos e validação de docentes | RN05, RN09, RN10 | FR-08, FR-16 | NFR-01 | 6 | aprovacoes, escopos_responsavel | CT-21 a CT-23, CT-36, CT-37, CT-39 |
| 8 | Bloqueio em manutenção | RN06 | FR-09 | | 7 | bloqueios | CT-24 |
| 9 | Retirada e devolução | RN07 | FR-10 | | 8 | retiradas_devolucoes | CT-25 a CT-27 |
| 10 | Histórico auditável | RN08 | FR-11 | NFR-09 | 2, 9 | auditoria | CT-28, CT-29, CT-38 |
| 11 | Notificação simulada | | FR-12 | | 9 | notificacoes | CT-30 |
| 12 | Relatórios | RN08 | FR-13 | NFR-04 | 10 | auditoria, reserva_itens | CT-31, CT-32, CT-38 |
| 13 | Interface responsiva e mensagens compreensíveis | | FR-14 | NFR-06, NFR-07, NFR-08 | todos | | CT-33, CT-34 |
| 14 | Documentação da API ou dos fluxos | | FR-15 | NFR-10 | todos | | CT-35 |

## Regras de negócio

| RN | Descrição curta | FR | Casos de teste |
|---|---|---|---|
| RN01 | Reserva válida | FR-04 | CT-10, CT-11 |
| RN02 | Sem sobreposição de recurso | FR-06 | CT-15, CT-17, CT-18 |
| RN03 | Agenda do professor | FR-06 | CT-16 |
| RN04 | Dupla reserva simultânea | FR-07 | CT-19, CT-20 |
| RN05 | Recurso restrito | FR-08 | CT-21, CT-22, CT-23 |
| RN06 | Manutenção e bloqueio | FR-09 | CT-09, CT-24 |
| RN07 | Material controlado | FR-10 | CT-25, CT-26, CT-27 |
| RN08 | Auditoria (inclui conflitos evitados) | FR-11, FR-13 | CT-28, CT-29, CT-38 |
| RN09 | Escopo do Responsável | FR-01, FR-02, FR-08, FR-16 | CT-03, CT-37, CT-40 |
| RN10 | Validação de docente | FR-16 | CT-36, CT-39 |

## Decisões sobre as lacunas

| # | Lacuna | Decisão | Onde |
|---|---|---|---|
| 1 | Conflitos evitados sem registro | Ação `CONFLITO_EVITADO` na `auditoria`, com o recurso disputado, e o FR-13 conta esses eventos | FR-11, FR-13, CT-38 |
| 2 | Validação de docentes sem requisito | Novo FR-16 e RN10, registrado em `aprovacoes` com tipo `VALIDACAO_DOCENTE` | FR-16, CT-36, CT-39 |
| 3 | Disponibilidade do professor | Calculada por agenda, bloqueios e situação ativa, sem tabela de janelas | FR-02, FR-03 |
| 4 | Faixa de RN no NFR-03 | Mantida, com justificativa por escrito. RN08 é coberta pelo NFR-09 | NFR-03 |
| 5 | Escopo do Responsável | Tabela `escopos_responsavel` e RN09 | FR-01, FR-02, FR-08, CT-37, CT-40 |

## Pendências em aberto

1. **Quais recursos são restritos** é decisão institucional: defina a lista real (por exemplo laboratórios e projetores).
2. **Bloqueio sobre reserva já aprovada** precisa de política: cancelar, notificar ou recusar o bloqueio. O fluxo 7 assume aviso ao Administrador.
3. **Reserva com itens decididos de forma diferente** (um item aprovado e outro rejeitado): definir se a reserva fica parcialmente confirmada ou é cancelada por inteiro.
