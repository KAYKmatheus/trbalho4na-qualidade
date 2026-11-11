# Relatório de cobertura e execução — Parte 2

## Resultado local

Execução em Python 3.14.8 (o alvo do CI é Python 3.12):

```text
py -m pytest -m "not integration" --cov=app --cov-branch --cov-report=term-missing
58 passed, 3 deselected
Linhas: 90,10% (meta CI: 80%)
Ramos: 71,22% (meta CI: 70%)
```

O cálculo de linhas considera `covered_lines / num_statements`; o de ramos
considera `covered_branches / num_branches`. O workflow aplica os dois limites
separadamente. Os três testes marcados como integração/concorrência foram
excluídos desta execução local; precisam rodar no job com PostgreSQL.

## Rastreabilidade de testes da Parte 2

| Tarefa | Casos automatizados | Evidência local | Observações |
|---|---|---|---|
| 23 — Autenticação e papéis | CT-01 a CT-05 | Passou | Inclui credenciais inválidas/expiradas, perfil administrativo, propriedade da reserva e autovalidação |
| 24 — Recursos e escopo | CT-06, CT-07, CT-40 | Passou | CRUD, desativação histórica, atribuição/remoção e auditoria |
| 25 — Disponibilidade | CT-08, CT-09 | Passou | Filtros e exclusão de ocupados/bloqueados |
| 26 — Alterar e cancelar | CT-13, CT-14 | Passou | Conflito mantém dados originais e cancelamento libera recurso; transições cobertas pelas regras de domínio |
| 27 — Aprovação e docente | CT-21 a CT-23, CT-36, CT-37, CT-39 | Passou | Rechecagem de conflito, escopo, justificativa e item docente pendente |
| 28 — Manutenção | CT-24 | Passou | Reserva em intervalo bloqueado retorna conflito |
| 29 — Materiais | CT-25 a CT-27 | Passou | Saldo, rejeição de devolução excedente e estoque pendente |
| 30 — Notificações | CT-30 | Passou | Registros simulados de envio, aprovação, rejeição e cancelamento |
| 31 — Relatórios/conflitos | CT-31, CT-32, CT-38 | Passou | Métricas do período e eventos de conflito evitado |
| 32 — Interface/OpenAPI | CT-33 a CT-35 | Passou | Erros, baseline responsivo/acessível e paridade de rotas |
| 33 — Contêiner/CI | NFR | Parcialmente validado | Ruff, testes de configuração e cobertura passaram; Docker e execução no GitHub Actions não disponíveis neste ambiente |
| 34 — Desempenho | NFR-04 | Plano preparado | JMX bem-formado; JMeter, banco populado e medição p50/p95/p99 ainda pendentes |

Os testes de concorrência e de garantias PostgreSQL não foram executados
localmente: Docker/JMeter não estão instalados e não há serviço PostgreSQL
disponível. O CI configura PostgreSQL 16 e inicializa as migrations antes dos
testes de integração. O cenário de carga permanece pendente de validação; nenhuma
meta de latência é declarada como atingida.

## Configuração da qualidade

- Ruff roda em todo Pull Request e em push para `principal`.
- O CI exige pelo menos 80% de linhas e 70% de ramos, avaliados separadamente.
- O scan SonarCloud é habilitado quando o segredo `SONAR_TOKEN` estiver
  cadastrado em GitHub Actions. A chave não é armazenada no repositório.
