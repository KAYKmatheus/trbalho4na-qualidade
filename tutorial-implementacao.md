# Tutorial de implementação — AlocaSenac

Este é o tutorial principal da implementação. Os comandos abaixo descrevem
como reproduzir as etapas; “resultado esperado” não significa que a etapa foi
executada neste ambiente. Para os resultados observados, consulte os arquivos
de evidência indicados em cada etapa e no [relatório final](./docs/relatorio-final.md).

## Passo 1 — Preparar o ambiente

**Comando (PowerShell, na raiz do repositório):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**Arquivos:** `pyproject.toml`, `requirements.txt`, `.env.example`.

**Resultado esperado:** ambiente virtual com as dependências do projeto. O
repositório requer Python 3.11 ou superior e o workflow configura Python 3.12;
uma execução do CI ainda aguarda Pull Request, conforme
[evidências](./docs/qualidade/evidencias/README.md).

## Passo 2 — Subir PostgreSQL e aplicar migrações

Configure `AUTH_SECRET_KEY` no ambiente local e inicie o banco:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
# Configure AUTH_SECRET_KEY com um valor local, fora do repositório.
docker compose up -d postgres
uvicorn app.main:app --reload
```

**Arquivos:** `docker-compose.yml`, `app/db.py`,
`migrations/001_initial_schema.sql`,
`migrations/002_exclusao_sobreposicao.sql`,
`migrations/003_auditoria_imutavel.sql`.

**Resultado esperado:** ao iniciar em PostgreSQL, a aplicação cria o esquema
SQLAlchemy e aplica os arquivos SQL em ordem. A execução real contra
PostgreSQL permanece pendente; veja o
[registro de evidências](./docs/qualidade/evidencias/README.md).

## Passo 3 — Conferir modelos persistidos

**Arquivo:** `app/models.py`.

**Comando:**

```powershell
python -c "from app.models import Base; print(sorted(Base.metadata.tables))"
```

**Resultado esperado:** listagem das tabelas da aplicação, incluindo
`users`, `resources`, `resource_scopes`, `resource_blocks`, `reservations`,
`reservation_items`, `approvals`, `material_movements`, `notifications` e
`audit_entries`. O [DBML](./docs/prd/modelagem-dados-sistema-academico.dbml)
representa esses nomes físicos.

## Passo 4 — Examinar regras de domínio

**Arquivos:** `app/dominio/regras.py`, `app/erros.py`.

**Comando:**

```powershell
python -m pytest tests/test_regras_dominio.py
```

**Resultado esperado:** verificações das regras puras de intervalo, estoque,
exceções de domínio e transições de estado. Resultados quantitativos devem ser
consultados somente em uma saída salva, como
[validacao-limpeza-2026-11-11.txt](./docs/qualidade/evidencias/validacao-limpeza-2026-11-11.txt).

## Passo 5 — Seguir a camada de serviços

**Arquivos:** `app/servicos/reservas.py`, `aprovacoes.py`, `disponibilidade.py`,
`materiais.py`, `auditoria.py`, `notificacoes.py`, `recursos.py`,
`manutencao.py` e `relatorios.py`.

**Comando de navegação:**

```powershell
Get-ChildItem app\servicos -File
```

**Resultado esperado:** cada caso de uso fica na classe de serviço
correspondente; as rotas delegam a operação e traduzem erros para respostas
HTTP. A [RTM](./docs/qualidade/RTM.md) relaciona cada requisito aos serviços e
testes concretos.

## Passo 6 — Iniciar e consultar a API

**Arquivos:** `app/api/v1.py`, `app/main.py`.

**Comandos:**

```powershell
uvicorn app.main:app --reload
curl.exe http://127.0.0.1:8000/v1/health
```

**Resultado esperado:** resposta de saúde da API e documentação OpenAPI em
`/docs`. Os endpoints reais estão declarados em `app/api/v1.py`.

## Passo 7 — Executar testes unitários e HTTP

**Arquivos:** `tests/test_regras_dominio.py`, `tests/test_reservas.py`,
`tests/bdd/test_api_errors.py` e demais `tests/bdd/test_*.py`.

**Comando:**

```powershell
python -m pytest
```

**Resultado esperado:** execução do conjunto padrão, que exclui o marker
`integration` conforme `pyproject.toml`. Use a saída de execução salva antes
de citar qualquer quantidade de testes; a
[evidência local existente](./docs/qualidade/evidencias/validacao-limpeza-2026-11-11.txt)
corresponde à execução registrada naquela data, não a uma execução atual.

## Passo 8 — Executar BDD e verificar mapeamentos

**Arquivos:** `tests/bdd/features/*.feature`,
`tests/bdd/test_cenarios_executaveis.py`,
`tests/bdd/test_cobertura_bdd.py`.

**Comandos:**

```powershell
python -m pytest tests/bdd -o addopts=""
python -m pytest tests/bdd/test_cobertura_bdd.py -o addopts=""
```

**Resultado esperado:** cenários Gherkin associados a node IDs pytest reais;
testes sem cenário devem constar em `SEM_CENARIO` com justificativa.

## Ciclo TDD do handler global

O caso do handler global de exceções foi desenvolvido teste primeiro:

- **Vermelho:** commit `7a2b651f597a4efdefeafe0f31699394ea92c4b3`; a
  [evidência](./docs/qualidade/evidencias/tdd-handler-vermelho.txt) registra
  a falha do teste porque a resposta tinha `text/plain` em vez de JSON.
- **Verde:** commit `f30349be6b99920e8842fa44338678797860cf1d`; o handler em
  `app/main.py` registra a exceção no log e responde com mensagem genérica. A
  [evidência](./docs/qualidade/evidencias/tdd-handler-verde.txt) registra um
  teste aprovado.
- **Refatoração:** não houve etapa separada; o handler permaneceu centralizado
  em `app/main.py`.

## Passo 9 — Validar concorrência em PostgreSQL

**Arquivos:** `migrations/002_exclusao_sobreposicao.sql`,
`app/servicos/reservas.py`, `tests/bdd/features/conflitos_concorrencia.feature`,
`tests/bdd/test_cenarios_executaveis.py`,
`tests/test_concorrencia.py`.

**Comando para o cenário CT-19:**

```powershell
python -m pytest -o addopts="" -m "integration and concorrencia" "tests/bdd/test_cenarios_executaveis.py::test_processar_requisições_simultâneas_pela_mesma_sala" -v
```

**Resultado esperado:** uma requisição de sala confirmada e as demais
recusadas com conflito. A configuração do cenário usa dez threads; a
execução PostgreSQL está pendente e não se deve declarar esse resultado sem
salvar a saída em `docs/qualidade/evidencias/`.

## Passo 10 — Executar o fluxo E2E por HTTP

**Arquivo:** `tests/e2e/test_fluxo_completo.py`.

**Comando:**

```powershell
python -m pytest tests/e2e/test_fluxo_completo.py -o addopts=""
```

**Resultado esperado:** fluxo de recurso, pesquisa, reserva, decisão,
movimentação de material, conclusão e relatório, além do caso de conflito de
sala. Os testes usam HTTP por `TestClient`; consulte a saída salva antes de
afirmar uma execução aprovada.

## Passo 11 — Verificar o workflow de CI

**Arquivo:** `.github/workflows/ci.yml`.

**Comando local correspondente à checagem de estilo e testes:**

```powershell
python -m ruff check .
python -m pytest -o addopts="" --cov=app --cov-branch --cov-report=term-missing
```

**Resultado esperado:** jobs de qualidade, integração PostgreSQL e contêiner
executados no GitHub Actions. O estado observado do workflow está registrado
como aguardando execução no Pull Request em
[evidências](./docs/qualidade/evidencias/README.md).

## Passo 12 — Configurar SonarCloud

**Arquivos:** `sonar-project.properties`, `.github/workflows/ci.yml`,
`README.md`.

**Procedimento:** crie um token de análise no SonarCloud e cadastre-o no
repositório GitHub como segredo `SONAR_TOKEN`. Não salve o token em arquivo,
argumento de comando ou commit.

**Resultado esperado:** o workflow executa o scan e aguarda o quality gate
somente quando o segredo existe. A execução SonarCloud continua pendente até
que o grupo configure o segredo e haja execução observada.

## Passo 13 — Preparar e executar desempenho

**Arquivos:** `tests/desempenho/preparar_dados.py`,
`tests/desempenho/reservas.jmx`, `.gitignore`,
`docs/qualidade/desempenho.md`.

**Comandos:**

```powershell
python tests/desempenho/preparar_dados.py
jmeter -n -t tests/desempenho/reservas.jmx `
  -Jhost=localhost -Jport=8000 `
  -Jthreads=100 -Jrampup=30 -Jduration=300 `
  -JdataFile=tests/desempenho/reservas.csv `
  -l tests/desempenho/resultados.jtl `
  -e -o tests/desempenho/relatorio-jmeter
```

O script exige `DATABASE_URL` apontando para um banco PostgreSQL de teste; o
CSV gerado contém credenciais e é ignorado pelo Git. **Resultado esperado:**
relatório JMeter com latências e erros por operação. Não há medição salva no
repositório; p95 e taxa de erro permanecem pendentes conforme
[desempenho.md](./docs/qualidade/desempenho.md).

## Passo 14 — Abrir a interface web

**Arquivos:** `app/web/static/index.html`, `buscar.html`, `reservar.html`,
`minhas.html`, `estilo.css`, `app.js`.

**Comando/URL:**

```text
http://localhost:8000/app/index.html
```

**Resultado esperado:** login, busca, envio de reserva e listagem/cancelamento
das próprias reservas usando as rotas existentes. A responsividade e o uso
somente por teclado ainda precisam da execução manual do
[checklist CT-34](./docs/qualidade/evidencias/ct-34-checklist.md).

## Referências

- [Requisitos funcionais e regras de negócio](./docs/prd/requisitos-funcionais-sistema-academico.md)
- [Requisitos não funcionais](./docs/prd/requisitos-nao-funcionais-sistema-academico.md)
- [Matriz de rastreabilidade RTM](./docs/qualidade/RTM.md)
- [Relatório final](./docs/relatorio-final.md)
- [Defeitos confirmados](./docs/qualidade/defeitos.md)
