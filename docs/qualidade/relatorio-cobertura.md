# Relatório de cobertura e execução — Parte 2

## Resultado local

Execução em Python 3.14.8 (o alvo do CI é Python 3.12):

```text
py -m pytest -m "not integration" --cov=app --cov-branch --cov-report=term-missing
60 passed, 3 deselected
Linhas: 90,09% (1091/1211; meta CI: 80%)
Ramos: 71,22% (198/278; meta CI: 70%)
```

O cálculo de linhas considera `covered_lines / num_statements`; o de ramos
considera `covered_branches / num_branches`. O workflow aplica os dois limites
separadamente. Os três testes marcados como integração/concorrência foram
excluídos desta execução local; precisam rodar no job com PostgreSQL.

## Estado da validação dos CTs

| Resultado | CTs | Observações |
|---|---|---|---|
| Aprovado nos testes locais | CT-01 a CT-10, CT-13, CT-14, CT-21 a CT-27, CT-30 a CT-32, CT-35 a CT-37, CT-39, CT-40 | Evidência de execução ligada na tabela de [casos de teste](./casos-de-teste.md) |
| Parcial | CT-11, CT-15, CT-18, CT-20, CT-28, CT-33, CT-34, CT-38 | Limites do teste executado estão descritos no registro por CT |
| Não executado | CT-12, CT-16, CT-17, CT-19, CT-29 | CT-19 exige disputa concorrente PostgreSQL; CT-29 exige validar triggers PostgreSQL |
| Validação ambiental pendente | NFR de contêiner/CI e CT-34 em navegador real; tarefa 34 | Docker, GitHub Actions, JMeter e PostgreSQL real não foram executados localmente |

Os três testes com marcador `integration` foram excluídos pela configuração
local. Docker, JMeter e ferramentas/serviço PostgreSQL não estão disponíveis
neste ambiente. O cenário de carga e as migrations ainda precisam de validação
em PostgreSQL; nenhuma meta de latência é declarada como atingida.

A saída detalhada de lint, importação, duas execuções da suíte e cobertura está
em [evidência local](./evidencias/validacao-limpeza-2026-11-11.txt).

## Configuração da qualidade

- Ruff roda em todo Pull Request e em push para `principal`.
- O CI exige pelo menos 80% de linhas e 70% de ramos, avaliados separadamente.
- O scan SonarCloud é habilitado quando o segredo `SONAR_TOKEN` estiver
  cadastrado em GitHub Actions. A chave não é armazenada no repositório.
