# Defeitos encontrados

| ID | Data | Descrição | Causa | Correção | Teste que prova |
|---|---|---|---|---|---|
| DEF-01 | 2026-11-12 | Transições proibidas a partir de `EM_USO` retornavam HTTP 422 em vez de 409. | O serviço propagava `ValidationError` da regra de estados e a rota tratava toda transição inválida como erro de validação. | A camada de serviço converte a transição de estado inválida em `ConflictError`, e a rota traduz esse conflito para HTTP 409. | `tests/test_reservation_em_uso.py` |
