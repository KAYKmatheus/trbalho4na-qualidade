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

## Como gerar estas evidências

Execute no PowerShell, na raiz do repositório, com PostgreSQL 16 de teste
acessível. Defina `DATABASE_URL` para esse banco ou deixe-a sem definir para
usar Testcontainers com Docker disponível. Não use banco de produção.

Os comandos abaixo gravam a saída completa de cada execução. A primeira linha
de cada arquivo registra a data e o hash do commit executado:

```powershell
$evidenceDate = Get-Date -Format "yyyy-MM-dd"
$commitHash = git rev-parse HEAD
$header = "Data: $evidenceDate | Commit: $commitHash"

$ruffFile = "docs/qualidade/evidencias/ruff-$evidenceDate.txt"
$header | Set-Content -Path $ruffFile -Encoding utf8
py -m ruff check . 2>&1 | Tee-Object -FilePath $ruffFile -Append
if ($LASTEXITCODE -ne 0) { throw "ruff check falhou; consulte $ruffFile" }

$fullTestFile = "docs/qualidade/evidencias/pytest-completo-$evidenceDate.txt"
$header | Set-Content -Path $fullTestFile -Encoding utf8
py -m pytest -o addopts="" -v 2>&1 | Tee-Object -FilePath $fullTestFile -Append
if ($LASTEXITCODE -ne 0) { throw "pytest completo falhou; consulte $fullTestFile" }

$integrationFile = "docs/qualidade/evidencias/pytest-integracao-postgres-$evidenceDate.txt"
$header | Set-Content -Path $integrationFile -Encoding utf8
py -m pytest -o addopts="" -m integration -v 2>&1 | Tee-Object -FilePath $integrationFile -Append
if ($LASTEXITCODE -ne 0) { throw "pytest de integração falhou; consulte $integrationFile" }
```

Em 2026-11-12, `DATABASE_URL` não estava definida e o Docker CLI não estava
instalado neste ambiente. Os testes PostgreSQL e as respectivas evidências
seguem pendentes de execução; nenhum resultado foi simulado.

Registro:

| Evidência | CT | Data | Executor | Resultado |
|---|---|---|---|---|
| | | | | |
