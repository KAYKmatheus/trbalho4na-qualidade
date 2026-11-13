# Relatório de cobertura

- Data: 2026-11-12
- Commit-base: `76803453f9cd7fa3beaeb3e577e4e96c17fbd3ff` (medição feita na árvore de trabalho atual).
- Comando: `py -m pytest -o addopts="" --cov=app --cov-branch --cov-report=term-missing --cov-report=json:coverage.json`
- Linhas: 91.36% (1121/1227); meta: 80% — atingida.
- Ramos: 75.18% (212/282); meta: 70% — atingida.
- Testes pytest: 84
- Testes com cenário: 55
- Testes sem cenário: 29

## Cobertura por módulo

| Módulo | Linhas cobertas | Ramos cobertos |
|---|---:|---:|
| `app/__init__.py` | 0/0 (100.00%) | 0/0 (100.00%) |
| `app/api/__init__.py` | 0/0 (100.00%) | 0/0 (100.00%) |
| `app/api/deps.py` | 32/32 (100.00%) | 4/4 (100.00%) |
| `app/api/schemas.py` | 138/141 (97.87%) | 5/8 (62.50%) |
| `app/api/v1.py` | 172/196 (87.76%) | 15/16 (93.75%) |
| `app/config.py` | 8/8 (100.00%) | 0/0 (100.00%) |
| `app/db.py` | 75/75 (100.00%) | 29/30 (96.67%) |
| `app/dominio/__init__.py` | 0/0 (100.00%) | 0/0 (100.00%) |
| `app/dominio/regras.py` | 40/46 (86.96%) | 8/12 (66.67%) |
| `app/erros.py` | 7/7 (100.00%) | 0/0 (100.00%) |
| `app/main.py` | 4/4 (100.00%) | 2/2 (100.00%) |
| `app/models.py` | 111/111 (100.00%) | 0/0 (100.00%) |
| `app/servicos/__init__.py` | 0/0 (100.00%) | 0/0 (100.00%) |
| `app/servicos/aprovacoes.py` | 62/73 (84.93%) | 20/30 (66.67%) |
| `app/servicos/auditoria.py` | 12/12 (100.00%) | 0/0 (100.00%) |
| `app/servicos/autenticacao.py` | 68/75 (90.67%) | 7/10 (70.00%) |
| `app/servicos/disponibilidade.py` | 41/44 (93.18%) | 19/24 (79.17%) |
| `app/servicos/manutencao.py` | 24/26 (92.31%) | 6/8 (75.00%) |
| `app/servicos/materiais.py` | 51/57 (89.47%) | 10/16 (62.50%) |
| `app/servicos/notificacoes.py` | 9/9 (100.00%) | 0/0 (100.00%) |
| `app/servicos/recursos.py` | 78/87 (89.66%) | 21/28 (75.00%) |
| `app/servicos/relatorios.py` | 37/43 (86.05%) | 9/16 (56.25%) |
| `app/servicos/reservas.py` | 152/181 (83.98%) | 57/78 (73.08%) |

## Lacunas conhecidas

- `app/api/schemas.py`: ramos 62.50% < 70%.
- `app/dominio/regras.py`: ramos 66.67% < 70%.
- `app/servicos/aprovacoes.py`: ramos 66.67% < 70%.
- `app/servicos/materiais.py`: ramos 62.50% < 70%.
- `app/servicos/relatorios.py`: ramos 56.25% < 70%.

## Cenários sem teste mapeado

- Nenhum cenário sem teste mapeado.

## Como reproduzir

Na raiz do repositório, gere os dados e o relatório:

```text
py -m pytest -o addopts="" --cov=app --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
py -m tests.bdd.gerar_relatorio
```
