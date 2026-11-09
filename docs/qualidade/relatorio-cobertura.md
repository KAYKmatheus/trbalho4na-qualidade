# Relatório de cobertura BDD

Gerado por `python scripts/generate_coverage_report.py` a partir de
`docs/qualidade/casos-de-teste.md` e dos arquivos `features/*.feature`.

## Resumo

- Casos documentados: **40**
- Cenários Gherkin: **40**
- CTs documentados mapeados: **40 de 40 (100.0%)**

## Cobertura por módulo

| Módulo (arquivo feature) | Cenários/CTs mapeados |
|---|---:|
| `aprovacoes.feature` | 3 |
| `auditoria.feature` | 3 |
| `autenticacao_autorizacao.feature` | 5 |
| `conflitos_concorrencia.feature` | 6 |
| `escopo_responsavel.feature` | 2 |
| `interface_api.feature` | 3 |
| `manutencao.feature` | 1 |
| `materiais.feature` | 3 |
| `notificacoes.feature` | 1 |
| `pesquisa_disponibilidade.feature` | 2 |
| `recursos.feature` | 2 |
| `relatorios.feature` | 2 |
| `reservas.feature` | 5 |
| `validacao_docente.feature` | 2 |

## Lacunas declaradas

- Nenhuma lacuna de rastreabilidade entre os CTs e os cenários.
- A cobertura acima é estrutural: verifica a correspondência entre IDs, não a execução funcional dos passos Gherkin nem cobertura de linhas de código.
- CT-19 e CT-20 têm testes PostgreSQL em Testcontainers; a execução de referência será registrada pelo workflow em `docs/qualidade/evidencias/`.

## Como reproduzir

```bash
pip install -r requirements-dev.txt
python scripts/generate_coverage_report.py
pytest -q tests/bdd/test_gherkin_coverage.py
```