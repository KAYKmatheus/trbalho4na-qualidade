# Tutorial — AlocaSenac: construção do PRD do zero

Este tutorial documenta como o PRD do sistema de alocação de salas, professores e materiais foi construído a partir do método do CineSenac, com foco em evidências de qualidade.

## O que o sistema é

Sistema que aloca salas, professores e materiais sem conflitos de horário, com três perfis:

- **Administrador:** gerencia recursos, usuários, bloqueios e manutenções.
- **Responsável:** aprova solicitações restritas, valida docentes e acompanha retiradas e devoluções.
- **Solicitante:** consulta disponibilidade e cria, altera ou cancela as próprias reservas.

## Estrutura final

```
├── app/
│   ├── api/
│   │   └── v1.py
│   ├── dominio/
│   │   └── regras.py
│   ├── servicos/
│   │   └── reservas.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   └── models.py
├── migrations/
│   └── 001_initial_schema.sql
├── tests/
│   ├── test_concorrencia.py
│   ├── test_regras_dominio.py
│   └── test_reservas.py
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

1. Implementar migrações e garantias de concorrência no PostgreSQL.
2. Completar e validar os modelos, serviços e API.
3. Executar os testes com PostgreSQL e arquivar as evidências.

## Passo 7 — Base da aplicação

**Prompt:**

> ## Bloco A: base do projeto (tarefas 1 a 4)
>
> 1. **Arquivos de configuração.** Em `.gitignore`, acrescente as entradas de Python (`__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `reports/`) e remova do índice do git qualquer arquivo gerado. Reescreva `.env.example` com as variáveis reais do projeto (URL do banco, ambiente) no lugar do conteúdo genérico do AIOX. Substitua `AGENTS.md` pelo conteúdo de `AGENTS.proposta.md` e apague o `.proposta`.
> 2. **Reorganização.** Aplique a tabela "Estrutura-alvo" com `git mv`, ajuste todos os imports e confirme que `python -c "import app.main"` funciona antes de seguir.
> 3. **Configuração e banco únicos.** Hoje `ReservationService.__init__` chama `configure_database` a cada instância e `api_v1.py` cria `ReservationService(AppSettings())` dentro da rota. Crie `app/db.py` com engine e `sessionmaker` criados uma vez (com `expire_on_commit=False`), uma função `init_db()` e uma dependência FastAPI que entrega a sessão. Alinhe o nome do banco: o padrão de `app_config.py` é `alocasenac` e o `docker-compose.yml` cria `alocasenac_test`. Escolha um padrão claro (`alocasenac` para desenvolvimento, `alocasenac_test` só nos testes) e registre no README. Remova `execute_sql`, que não é usada.
> 4. **Dependências e marcadores.** Em `pyproject.toml`, registre os marcadores `integration` e `concorrencia` e a configuração do `pytest` e do `ruff`. Em `requirements.txt`, remova `alembic` e `jinja2` se não forem usados (ou use-os de verdade) e acrescente `pytest-cov`, `pytest-bdd` e `testcontainers[postgres]`. Mantenha uma só fonte de dependências.
>
> Critério de pronto do bloco: `ruff check .` limpo e a aplicação importando sem erro.

**Resultado:** reorganização dos módulos em `app/`, configuração única da engine e sessão em `app/db.py`, dependências centralizadas em `pyproject.toml`, e configuração do ambiente documentada em `.env.example` e neste README.

**Aprendizado:** separar a criação da engine da lógica dos serviços torna a sessão compartilhável e testável por dependência.
