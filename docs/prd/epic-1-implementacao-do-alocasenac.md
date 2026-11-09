# EPIC-1: Implementação do AlocaSenac

**Status:** Planning
**Owner:** Não definido nas fontes fornecidas
**Created:** 2026-11-09

---

## Objective

Migrar e evoluir o AlocaSenac conforme os requisitos funcionais documentados, preservando as garantias de autorização, disponibilidade, concorrência e histórico, com a migração para Java 21, Spring Boot 3 e Maven motivada pelo domínio de conhecimento da equipe.

## Business Value

Permitir que a equipe mantenha e evolua o sistema na stack compatível com seu domínio de conhecimento e apoiar a consulta e solicitação de recursos acadêmicos, a avaliação de solicitações pelos Responsáveis e a manutenção de cadastros pelos Administradores, com disponibilidade e histórico confiáveis.

## Context and Sources

- `docs/prd/requisitos-funcionais-sistema-academico.md` está identificado como rascunho para validação; os requisitos listados neste Epic são referências documentais, não uma declaração de validação institucional.
- `docs/prd/arquitetura.md` está identificado como proposta; serve como referência de arquitetura e não é tratado aqui como decisão aprovada.
- `docs/prd/modelagem-dados-sistema-academico.dbml` registra o modelo de dados e garantias a completar na migração PostgreSQL.
- `docs/qualidade/casos-de-teste.md` lista CT-01 a CT-40 com resultado inicial “Não executado”. Nenhum CT é declarado aprovado por este Epic.
- O motivo da migração Python para Java 21, Spring Boot 3 e Maven é o domínio da equipe, conforme confirmado pelo usuário e registrado na story 1.1.

## Scope

### In Scope

- Migrar a aplicação existente de Python para Java 21, Spring Boot 3 e Maven segundo os critérios da story 1.1.
- Entregar os comportamentos funcionais FR-01 a FR-16 por meio das stories listadas, respeitando os mapeamentos registrados e os critérios das fontes.
- Preservar autorização por perfil e escopo, disponibilidade e concorrência de recursos, histórico auditável e movimentações de materiais, conforme os requisitos funcionais e o modelo documentado.
- Validar os comportamentos com os casos de teste existentes; registrar resultados somente após execução e evidência.

### Out of Scope

- Criar ou alterar requisitos, regras de negócio, critérios de teste ou decisões arquiteturais não presentes nas fontes autorizadas.
- Declarar CTs aprovados sem execução e evidência correspondente.
- Implementar as stories 1.2 a 1.7 nesta etapa; elas permanecem em Draft para etapas posteriores.
- Tratar a arquitetura em `docs/prd/arquitetura.md` como aprovada sem validação própria.

## Stories

| ID | Title | Requirements | Status | Location |
|----|-------|--------------|--------|----------|
| 1.1 | [Migração do AlocaSenac para Java 21](../stories/1.1.migracao-java-21.md) | Critérios de migração registrados na story | Ready | `docs/stories/1.1.migracao-java-21.md` |
| 1.2 | [Autenticação, perfis e escopo do Responsável](../stories/1.2.autenticacao-perfis-escopo-responsavel.md) | FR-01, RN09 | Draft | `docs/stories/1.2.autenticacao-perfis-escopo-responsavel.md` |
| 1.3 | [Alteração, cancelamento e bloqueios](../stories/1.3.alteracao-cancelamento-bloqueios.md) | FR-05, FR-09 | Draft | `docs/stories/1.3.alteracao-cancelamento-bloqueios.md` |
| 1.4 | [Aprovação e validação de docentes](../stories/1.4.aprovacao-validacao-docentes.md) | FR-08, FR-16 | Draft | `docs/stories/1.4.aprovacao-validacao-docentes.md` |
| 1.5 | [Retirada e devolução](../stories/1.5.retirada-devolucao.md) | FR-10 | Draft | `docs/stories/1.5.retirada-devolucao.md` |
| 1.6 | [Auditoria, conflitos evitados e relatórios](../stories/1.6.auditoria-conflitos-relatorios.md) | FR-11, FR-13 | Draft | `docs/stories/1.6.auditoria-conflitos-relatorios.md` |
| 1.7 | [Cadastros, pesquisa, notificações e interface](../stories/1.7.cadastros-pesquisa-notificacoes-interface.md) | FR-02, FR-03, FR-12, FR-14 | Draft | `docs/stories/1.7.cadastros-pesquisa-notificacoes-interface.md` |

## Success Criteria

- Cada story do Epic atende aos próprios critérios de aceite e permanece rastreável aos requisitos e fontes documentadas.
- Os requisitos de autorização, escopo, disponibilidade, concorrência, auditoria, movimentação de materiais, notificações, relatórios e interface previstos nas stories são implementados sem enfraquecer os critérios documentados.
- Os CTs pertinentes são executados e seus resultados e evidências são registrados; este Epic não antecipa resultados.
- A aplicação migrada atende aos critérios técnicos e de verificação especificados na story 1.1.

## Technical Requirements

- A migração alvo é Java 21, Spring Boot 3 e Maven, conforme a solicitação e a story 1.1.
- O DBML identifica PostgreSQL como banco alvo e descreve integridade de reservas, concorrência, escopo do Responsável, auditoria append-only e movimentações de materiais; detalhes e garantias de migração estão especificados na story 1.1.
- O documento de arquitetura permanece uma proposta e deve ser considerado com esse estado nas stories subsequentes.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| A migração pode enfraquecer garantias de disponibilidade, concorrência ou auditoria existentes. | High | Usar os requisitos, DBML e CTs indicados como fontes e verificar os comportamentos conforme os critérios da story 1.1. |
| Requisitos funcionais e arquitetura têm estados documentais de rascunho/proposta. | Medium | Preservar esses estados e não inferir aprovação institucional ou arquitetural neste Epic. |
| A validação brownfield recomenda 1–3 stories, enquanto este plano contém sete (1.1–1.7). | Medium | Registrar que a recomendação é do task brownfield genérico; a solicitação explícita do usuário prevalece para este plano, portanto não é bloqueio. |

## Dependencies and Handoff

- A story 1.1 já existe, está vinculada acima e está Ready.
- As stories 1.2 a 1.7 já existem e estão em Draft. Sua implementação fica para etapas posteriores.
- Não são declaradas dependências adicionais entre stories sem respaldo nas fontes fornecidas.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-11-09 | 1.0 | Criação local do Epic 1 em Planning, com stories 1.1–1.7 e rastreabilidade às fontes autorizadas. | Morgan (@pm) |