# Evidência JMeter — 13/11/2026

- Branch: `feature/ajustes-projeto`
- Commit executado informado: `99a6b5a`
- Usuários virtuais configurados: 100
- Ramp-up: 30 segundos
- Duração configurada: 300 segundos
- Amostras: 956
- Erros: 294 (30.75%)

## Resultados por operação

| Operação | Amostras | Erros | p95 (ms) |
|---|---:|---:|---:|
| Preparar intervalo unico | 195 | 0 | 21 |
| Login solicitante | 195 | 31 | 85261 |
| Pesquisar disponibilidade | 171 | 67 | 92727 |
| Criar reserva restrita | 146 | 72 | 92033 |
| Login responsavel | 135 | 42 | 88718 |
| Aprovar reserva | 114 | 82 | 119984 |

## Códigos de erro

- HTTP/código `401`: 90 ocorrências
- HTTP/código `404`: 16 ocorrências
- HTTP/código `500`: 188 ocorrências

## Conclusão

As metas de desempenho não foram atendidas.
Os logs da API identificaram esgotamento do pool SQLAlchemy.
Consulte `docs/qualidade/desempenho.md` e o defeito DEF-07.

Este resumo foi gerado a partir do JTL da execução.
Não inclui credenciais ou dados de autenticação.
