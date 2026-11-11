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
   e inicie a API (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
2. Popule o banco com volume representativo (por exemplo 200 salas, 500
   professores, 1.000 materiais e 50.000 reservas históricas). Para o cenário
   JMeter, prepare também 100 contas SOLICITANTE, 100 salas restritas distintas
   e contas RESPONSAVEL com escopo de aprovação para cada sala.
3. Crie localmente `tests/desempenho/reservas.csv` com cabeçalho e ao menos
   100 linhas de dados (o JMeter ignora a primeira linha), no formato:

   ```csv
   requester_email,requester_password,responsible_email,responsible_password,resource_id
   solicitante-001@example.test,senha-local,responsavel-001@example.test,senha-local,id-recurso-001
   ```

   Inclua ao menos 100 linhas de dados. Use credenciais e identificadores
   exclusivos do ambiente de teste; o CSV é ignorado pelo Git e não deve conter
   dados de produção.

### Execução

Com o Apache JMeter 5.6.3+ instalado, na raiz do repositório:

```powershell
jmeter -n -t tests/desempenho/reservas.jmx `
  -Jhost=localhost -Jport=8000 `
  -Jthreads=100 -Jrampup=30 -Jduration=300 `
  -JdataFile=tests/desempenho/reservas.csv `
  -l tests/desempenho/resultados.jtl `
  -e -o tests/desempenho/relatorio-html
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

**Status atual:** plano JMeter preparado; execução e metas de desempenho
pendentes de validação em PostgreSQL com os dados de carga descritos acima.
