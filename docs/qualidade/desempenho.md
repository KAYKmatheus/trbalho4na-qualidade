# Desempenho

**Base:** NFR-04 em [requisitos não funcionais](../prd/requisitos-nao-funcionais-sistema-academico.md). As metas abaixo são **propostas** e devem ser validadas.

## Metas

| Operação | Meta | Carga |
|---|---|---|
| Pesquisa de recursos e disponibilidade | p95 até 2 s | 100 usuários simultâneos |
| Criação e decisão de reserva | p95 até 3 s | 100 usuários simultâneos |

Erros e timeouts entram na medição e não podem ser excluídos.

## Método

1. Popular o banco com volume representativo (por exemplo 200 salas, 500 professores, 1.000 materiais e 50.000 reservas históricas), documentando o seed.
2. Executar o teste de carga (k6, JMeter ou equivalente) com rampa de subida, patamar e descida.
3. Medir p50, p95, p99, vazão e taxa de erro por operação.
4. Repetir o teste com os índices de `reserva_itens` do DBML e comparar com `EXPLAIN ANALYZE` das consultas de disponibilidade.
5. Arquivar scripts e relatórios em `evidencias/`.

## Registro de resultados

| Data | Cenário | Usuários | p50 | p95 | p99 | Erros | Meta atingida |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
