# Evidências

Convenção de nome: `CT-xx-descricao-AAAA-MM-DD.ext`.

Evidências esperadas:

- Relatório de cobertura de testes.
- Log do teste de concorrência (CT-19, CT-20).
- Relatório de carga (k6, JMeter ou equivalente) com p50, p95, p99 e erros.
- Relatório de análise estática e de dependências.
- Prints das telas em 360 px e 1920 px (CT-34).
- Saída da tentativa de UPDATE e DELETE em `auditoria` (CT-29).
- Especificação OpenAPI validada (CT-35).

Registro:

| Evidência | CT | Data | Executor | Resultado |
|---|---|---|---|---|
| | | | | |

## Artefatos de CI

O workflow `.github/workflows/quality.yml` gera e publica como artefatos desta pasta:

- `coverage.xml` e `coverage.json`: cobertura de código com portão de 85%.
- `pytest.xml`: resultado da suíte completa, incluindo os testes PostgreSQL.
- `testcontainers.xml`: resultado isolado dos testes de integração.
- `bdd.xml`: resultado da validação estrutural de cobertura Gherkin.
- `bandit.json`: análise estática de segurança.
- `pip-audit.json`: auditoria de dependências.

Os arquivos são produzidos durante o workflow e baixados pela seção **Artifacts** da execução do GitHub Actions. A cobertura Gherkin atual está em [../relatorio-cobertura.md](../relatorio-cobertura.md).
