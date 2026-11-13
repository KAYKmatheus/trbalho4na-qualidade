# Defeitos e correções confirmados no histórico

Os registros abaixo foram conferidos com `git log --oneline` e `git show`.
Foram encontrados seis defeitos/correções com uma alteração identificável no
histórico. A ausência de evidência de execução PostgreSQL é indicada quando
aplicável.

| ID | Data | Onde | Descrição | Causa | Correção (commit) | Teste que prova | Severidade |
|---|---|---|---|---|---|---|---|
| DEF-01 | 2026-11-12 | `app/servicos/reservas.py`, `app/api/v1.py` | Transições inválidas a partir de `EM_USO` não eram traduzidas consistentemente para HTTP 409. | A regra de transição lançava `ValidationError`, e a rota retornava 422 sem converter a exceção para conflito. | `9c8b7a6` — o serviço converte a falha em `ConflictError` e a rota mapeia para 409. | [test_reservation_em_uso.py](../../tests/test_reservation_em_uso.py): `test_cannot_cancel_reservation_in_use_over_http`, `test_in_use_reservation_rejects_all_transitions_except_completion_over_http`, `test_in_use_reservation_can_be_completed_over_http` | Alta |
| DEF-02 | 2026-11-11 | `app/db.py`, inicialização para testes PostgreSQL | `init_db()` não aceitava o engine de integração fornecido pelo fixture. | A inicialização usava exclusivamente o engine global, diferente do engine criado para a sessão PostgreSQL de teste. | `25cd586` — `init_db(engine)` usa o engine recebido e aplica as migrações nele. | [test_database.py](../../tests/bdd/test_database.py): `test_init_db_uses_supplied_engine` | Alta |
| DEF-03 | 2026-11-11 | `migrations/002_exclusao_sobreposicao.sql` | A restrição de exclusão também impedia reservas sobrepostas do mesmo material, mesmo quando havia estoque. | `reservation_items_no_overlap` não excluía materiais, cujo controle correto soma quantidades. | `d9ecee0` — acrescenta `resource_type <> 'material'` ao predicado da restrição. | [test_concorrencia.py](../../tests/test_concorrencia.py): `test_overlapping_material_reservations_respect_available_stock`; execução PostgreSQL pendente conforme [registro de evidências](./evidencias/README.md) | Alta |
| DEF-04 | 2026-11-11 | `app/erros.py` | A exceção customizada `PermissionError` sombreava a exceção nativa do Python. | Um alias com o nome da exceção built-in tornava ambígua a captura de erros de permissão. | `6911c38` — remove o alias e mantém `PermissaoNegadaError`. | [test_regras_dominio.py](../../tests/test_regras_dominio.py): `test_permission_denied_exception_does_not_shadow_builtin` | Média |
| DEF-05 | 2026-11-12 | `tests/bdd/test_cobertura_bdd.py` | O teste AST do contexto Docker não tinha cenário Gherkin nem justificativa de exceção. | O novo teste não havia sido incluído no dicionário `SEM_CENARIO`. | `73d934d` — inclui o node ID em `SEM_CENARIO` com justificativa. | [test_cobertura_bdd.py](../../tests/bdd/test_cobertura_bdd.py): `test_every_pytest_test_has_scenario_or_explicit_reason`, `test_every_scenario_test_reference_exists` | Baixa |
| DEF-06 | 2026-11-09 | `models.py` legado | Os modelos chamavam `SessionLocal.query_property()` durante a definição das classes. | `SessionLocal` era uma fábrica `sessionmaker`, não uma sessão global `scoped_session`; o atributo de consulta acoplava os modelos à inicialização do banco. | `048281b` — remove o `query_property` legado na conversão da persistência para sessões explícitas. | [test_main.py](../../tests/bdd/test_main.py): `test_import_does_not_start_uvicorn`; a [evidência local](./evidencias/validacao-limpeza-2026-11-11.txt) também registra `py -c "import app.main"` com código de saída 0. | Média |

O exemplo de `payload` dict gerando `TypeError` não foi incluído: a inspeção do
histórico disponível não identificou uma correção e um teste associados que
permitissem confirmá-lo sem inferência.
