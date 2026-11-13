# Desempenho

**Base:** NFR-04 em [requisitos não funcionais](../prd/requisitos-nao-funcionais-sistema-academico.md). As metas abaixo são **propostas** e devem ser validadas.

## Metas

| Operação | Meta | Carga |
|---|---|---|
| Pesquisa de recursos e disponibilidade | p95 até 2 s | 100 usuários simultâneos |
| Criação e decisão de reserva | p95 até 3 s | 100 usuários simultâneos |

Erros e timeouts entram na medição e não podem ser excluídos.

## Cenário JMeter

O plano [reservas.jmx](../../tests/desempenho/reservas.jmx) executa um fluxo
autenticado de pesquisa de disponibilidade, criação de reserva restrita e
aprovação. Por padrão usa 100 usuários, rampa de 30 segundos e duração de 5
minutos. Cada thread recebe datas futuras sem sobreposição; a iteração registra
falhas HTTP e assertions no relatório.

### Preparação

1. Use uma instância descartável de PostgreSQL, inicializada com as migrations,
   configure `AUTH_SECRET_KEY` no ambiente e inicie a API
   (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
2. Popule o banco com volume representativo (por exemplo 200 salas, 500
   professores, 1.000 materiais e 50.000 reservas históricas). Para criar os
   dados específicos do cenário JMeter, defina `DATABASE_URL` para o banco
   PostgreSQL de teste (o nome do banco precisa conter `test`) e rode:

   ```powershell
   python tests/desempenho/preparar_dados.py
   ```

   O script cria 100 contas SOLICITANTE, 100 contas RESPONSAVEL, 100 salas
   restritas distintas e um escopo de aprovação por sala. Ele escreve as
   credenciais geradas em `tests/desempenho/reservas.csv`; o arquivo é ignorado
   pelo Git e não deve ser compartilhado nem usado com dados de produção.

### Execução

Com o Apache JMeter 5.6.3+ instalado, na raiz do repositório:

```powershell
jmeter -n -t tests/desempenho/reservas.jmx `
  -Jhost=localhost -Jport=8000 `
  -Jthreads=100 -Jrampup=30 -Jduration=300 `
  -JdataFile=tests/desempenho/reservas.csv `
  -l tests/desempenho/resultados.jtl `
  -e -o tests/desempenho/relatorio-jmeter
```

Para inspecionar o plano pela interface gráfica, execute
`jmeter -t tests/desempenho/reservas.jmx`. As propriedades `threads`, `rampup`,
`duration`, `host`, `port`, `protocol`, `dataFile` e `resultsFile` podem ser
sobrescritas com `-J`. Não execute carga na produção.

## Método e evidências

1. Registre versão da API, PostgreSQL, JMeter, configuração de seed e hardware.
2. Meça p50, p95, p99, vazão e taxa de erro por sampler; erros e timeouts não
   podem ser excluídos. As metas são atingidas somente se pesquisa tiver p95
   até 2 s e criação/decisão p95 até 3 s, com os 100 usuários configurados.
3. Repita com os índices de `reserva_itens` do DBML e compare com
   `EXPLAIN ANALYZE` das consultas de disponibilidade.
4. Arquive o JTL e o relatório HTML em `docs/qualidade/evidencias/`, usando a
   convenção definida no README de evidências. Não versionar o CSV de contas,
   resultados JTL ou relatórios HTML.

## Registro de resultados

| Data | Cenário | Usuários | p50 | p95 | p99 | Erros | Meta atingida |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

**Status atualizado:** execução realizada em 13/11/2026. As metas de desempenho não foram atendidas. Consulte os resultados detalhados abaixo.

## Execução realizada em 13/11/2026

**Ambiente:** GitHub Codespaces, API FastAPI/Uvicorn,
PostgreSQL 16 e Apache JMeter 5.6.3 com Java 17.

**Branch:** `feature/ajustes-projeto`
**Commit:** `99a6b5a`

### Configuração

- Usuários virtuais: 100.
- Ramp-up: 30 segundos.
- Duração configurada: 300 segundos.
- Cenário: autenticação, pesquisa, criação e aprovação de reservas.
- Ambiente: banco PostgreSQL exclusivo para testes.

### Resultado geral

| Indicador | Resultado |
|---|---|
| Total de amostras | 956 |
| Amostras com erro | 294 |
| Taxa de erro | 30,75% |
| Tempo médio | 32.633 ms |
| Tempo máximo | 122.066 ms |
| Usuários iniciados | 100 |
| Usuários finalizados | 100 |

### Resultado por operação

| Operação | Amostras | Erros | p95 |
|---|---:|---:|---:|
| Preparar intervalo (processamento local) | 195 | 0 | 21 ms |
| Login solicitante | 195 | 31 | 85.261 ms |
| Pesquisar disponibilidade | 171 | 67 | 92.727 ms |
| Criar reserva restrita | 146 | 72 | 92.033 ms |
| Login responsável | 135 | 42 | 88.718 ms |
| Aprovar reserva | 114 | 82 | 119.984 ms |

### Análise dos erros

Os logs da API registraram repetidamente:

`sqlalchemy.exc.TimeoutError: QueuePool limit of size 5
overflow 10 reached, connection timed out, timeout 30.00`

Isso confirma esgotamento do pool de conexões SQLAlchemy
durante o teste, provocando erros HTTP 500.

Também foram observadas respostas HTTP 401 e 404 em
operações posteriores, possivelmente relacionadas a
falhas nas etapas anteriores do fluxo.

### Conclusão

**Resultado: REPROVADO quanto às metas de desempenho.**

Os valores de p95 excederam os limites definidos
para pesquisa (2 segundos), criação e aprovação
(3 segundos).

A execução demonstrou que, nas condições avaliadas,
a aplicação não sustentou adequadamente a carga
configurada de 100 usuários.

Recomenda-se investigar gerenciamento de sessões,
transações e dimensionamento do pool antes de
executar um novo teste.

### Evidências

- JTL local: `/tmp/alocasenac-jmeter-java17/resultados.jtl`
- Relatório HTML local:
  `/tmp/alocasenac-jmeter-java17/relatorio/`
- Logs da API: erro de esgotamento do QueuePool.
- Índice: [evidências da entrega](../evidencias/README.md).

Os artefatos locais ainda precisam ser preservados
fora do ambiente temporário. Não publicar credenciais
contidas no arquivo `tests/desempenho/reservas.csv`.
