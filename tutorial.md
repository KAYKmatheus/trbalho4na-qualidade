# Tutorial — AlocaSenac: construção do PRD do zero

Este tutorial documenta como o PRD do sistema de alocação de salas, professores e materiais foi construído a partir do método do CineSenac, com foco em evidências de qualidade.

## O que o sistema é

Sistema que aloca salas, professores e materiais sem conflitos de horário, com três perfis:

- **Administrador:** gerencia recursos, usuários, bloqueios e manutenções.
- **Responsável:** aprova solicitações restritas, valida docentes e acompanha retiradas e devoluções.
- **Solicitante:** consulta disponibilidade e cria, altera ou cancela as próprias reservas.

## Estrutura final

```
├── AGENTS.md
├── README.md
├── tutorial.md
├── docs/
│   ├── prd/
│   │   ├── personas/
│   │   ├── personas-sistema-academico.md
│   │   ├── requisitos-funcionais-sistema-academico.md
│   │   ├── requisitos-nao-funcionais-sistema-academico.md
│   │   ├── modelagem-dados-sistema-academico.dbml
│   │   ├── fluxos-sequencia.md
│   │   └── matriz-rastreabilidade.md
│   └── qualidade/
│       ├── plano-de-testes.md
│       ├── casos-de-teste.md
│       ├── seguranca.md
│       ├── desempenho.md
│       └── evidencias/
└── .aiox-core/development/skills/
    ├── analyze-docs/SKILL.md
    └── update-tutorial/SKILL.md
```

## Passo 1 — Personas

**Prompt:** _(cole aqui o prompt literal usado)_

**Resultado:** `docs/prd/personas/administrador.md`, `responsavel.md` e `solicitante.md` com objetivos e responsabilidades.

**Aprendizado:** o vocabulário comum vem antes de qualquer requisito.

## Passo 2 — Requisitos funcionais e regras de negócio

**Prompt:** _(cole aqui o prompt literal usado)_

**Resultado:** `docs/prd/requisitos-funcionais-sistema-academico.md` com RN01 a RN08 e FR-01 a FR-15, cada FR com critérios de aceite.

**Aprendizado:** critérios de aceite escritos junto com o requisito viram casos de teste quase diretos.

## Passo 3 — Requisitos não funcionais

**Prompt:** _(cole aqui o prompt literal usado)_

**Resultado:** `docs/prd/requisitos-nao-funcionais-sistema-academico.md` com NFR-01 a NFR-10 e metas marcadas como proposta.

**Aprendizado:** metas numéricas ainda não aprovadas devem ser identificadas como propostas.

## Passo 4 — Modelagem de dados

**Prompt:** _(cole aqui o prompt literal usado)_

**Resultado:** `docs/prd/modelagem-dados-sistema-academico.dbml` (PostgreSQL) com comentários sobre as garantias que o DBML não expressa: restrição de exclusão por intervalo, bloqueio de linha para material e auditoria append-only.

**Aprendizado:** a proteção contra dupla reserva precisa estar no banco, não só na aplicação.

## Passo 5 — Jornadas, fluxos, rastreabilidade e plano de qualidade

**Prompt:** "Complete as personas com jornadas, crie os fluxos de sequência em Mermaid, a matriz de rastreabilidade e a pasta qualidade com plano de testes, casos de teste, segurança e desempenho."

**Resultado:** jornadas nas três personas, `docs/prd/fluxos-sequencia.md` (10 diagramas), `docs/prd/matriz-rastreabilidade.md` (com lacunas encontradas) e `docs/qualidade/` (36 casos de teste, CT-01 a CT-36).

**Aprendizado:** a matriz de rastreabilidade revela lacunas entre documentos, como o indicador de conflitos evitados sem local de registro.

## Passo 6 — Skills e AGENTS.md

**Prompt:** "Crie as habilidades analyze-docs e update-tutorial e o AGENTS.md."

**Resultado:** `.aiox-core/development/skills/analyze-docs/SKILL.md`, `update-tutorial/SKILL.md` e `AGENTS.md`.

**Aprendizado:** tarefas que se repetem a cada passo viram skills para que a documentação não fique para trás.

## Próximos passos

1. Decidir as lacunas listadas na matriz de rastreabilidade.
2. Definir a pilha tecnológica.
3. Wireframes responsivos.
4. Especificação OpenAPI (FR-15).
5. Implementação e execução dos testes, arquivando as evidências.
