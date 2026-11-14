# Tutorial completo — AlocaSenac

Guia de instalação, execução, demonstração e testes. **Todos os passos têm instruções para GitHub Codespaces (Bash/Linux) e para VS Code local no Windows (PowerShell).** Execute somente o bloco correspondente ao seu ambiente, sempre na raiz do repositório.

> **Versão de referência:** `v1.0.0-rc1`. Os comandos abaixo são instruções de reprodução; a instalação limpa deve ser validada pelo grupo. O desempenho com 100 usuários ainda possui ressalva documentada em [desempenho](./docs/qualidade/desempenho.md).

## Passo 0 — Pré-requisitos e clone

| Codespaces / Linux | VS Code local / Windows |
|---|---|
| Codespace criado no repositório; terminal **Bash** | Git, VS Code, Python 3.12 e Docker Desktop instalado e aberto |
| Docker CLI e daemon disponíveis no Codespace | Docker Desktop com contêineres Linux ativos |
| O repositório já costuma estar clonado | É necessário clonar e abrir a pasta |

**Codespaces — Bash:** abra um Codespace na branch `principal` e confira:

```bash
pwd
git branch --show-current
docker --version
docker compose version
docker info
python --version
```

**VS Code — PowerShell:** abra o terminal integrado (`Terminal > New Terminal`) e execute:

```powershell
git clone https://github.com/KAYKmatheus/trbalho4na-qualidade.git
cd trbalho4na-qualidade
git branch --show-current
docker --version
docker compose version
docker info
py -3.12 --version
```

**Resultado esperado:** repositório na `principal` e Docker respondendo sem erro de conexão com o daemon. Se `docker info` falhar, **pare aqui**: inicie o Docker Desktop (Windows) ou verifique a disponibilidade do Docker no Codespace. Não adianta iniciar a API sem PostgreSQL.

## Passo 1 — Criar ambiente Python e instalar dependências

**Codespaces — Bash:**

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python --version
```

**VS Code — PowerShell:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python --version
```

Caso a política do PowerShell bloqueie `Activate.ps1`, execute `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` **somente nesse terminal** e tente ativar novamente. Outra opção é chamar diretamente `.\.venv\Scripts\python.exe`.

**Resultado esperado:** dependências instaladas no ambiente virtual. Python 3.12 é a versão usada no CI; o projeto exige pelo menos Python 3.11.

## Passo 2 — Configurar variáveis, iniciar PostgreSQL e aplicar migrações

O arquivo `docker-compose.yml` cria um PostgreSQL de demonstração chamado `alocasenac_test`. Neste tutorial, a API é executada **fora** do contêiner, no terminal do VS Code/Codespaces; por isso a URL aponta para `localhost:5432`.

**Atenção à ordem:** o Compose exige `AUTH_SECRET_KEY` ao interpretar o arquivo, **mesmo quando o comando inicia somente o serviço `postgres`**. Portanto, configure essa variável *antes* de executar `docker compose up -d postgres`. Caso contrário, o banco não inicia e o Uvicorn apresenta `Connection refused`.

**Codespaces — Bash (terminal 1):**

```bash
# 1. Configurar as variáveis neste terminal
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
export AUTH_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export APP_ENV="development"

# 2. Iniciar o banco e aguardar ficar saudável
docker compose up -d --wait postgres
docker compose ps

# 3. Somente depois de o PostgreSQL estar healthy, iniciar a API
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**VS Code — PowerShell (terminal 1):**

```powershell
# 1. Configurar as variáveis neste terminal
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
$env:AUTH_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:APP_ENV = "development"

# 2. Iniciar o banco e aguardar ficar saudável
docker compose up -d --wait postgres
docker compose ps

# 3. Somente depois de o PostgreSQL estar healthy, iniciar a API
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Resultado esperado:** o comando `docker compose up -d --wait postgres` só retorna quando o PostgreSQL está saudável (`healthy`); depois, o Uvicorn deve exibir `Application startup complete.`. Se `--wait` não for reconhecido pela versão do Docker Compose, atualize o Docker Compose ou espere até `docker compose ps` indicar `healthy` antes de iniciar a API. A aplicação cria tabelas e aplica as migrações ao iniciar.

**Importante:** mantenha a API rodando nesse terminal. Cada terminal tem variáveis de ambiente próprias: no próximo passo, configure a URL novamente no segundo terminal.

**Se aparecer `Connection refused` na porta 5432:** o PostgreSQL não iniciou ou não está acessível. Verifique `docker compose ps` e `docker compose logs postgres`. Não tente resolver alterando a API.

**Se a porta 5432 estiver ocupada:** identifique a outra instância de PostgreSQL antes de alterar portas. Não exclua volumes nem bancos sem conferir seu conteúdo.

## Passo 3 — Conferir API e abrir a interface

Abra **outro terminal** e mantenha o terminal 1 com o Uvicorn ativo.

**Codespaces — Bash (terminal 2):**

```bash
curl -i http://127.0.0.1:8000/v1/health
```

**VS Code — PowerShell (terminal 2):**

```powershell
curl.exe -i http://127.0.0.1:8000/v1/health
```

**Resultado esperado:** HTTP 200 com `{"status":"ok","service":"alocasenac"}`.

- Interface: `http://localhost:8000/app/index.html`
- Documentação da API: `http://localhost:8000/docs`
- No Codespaces, abra a porta **8000** pela aba **Ports** (use o endereço encaminhado pelo Codespaces). Não exponha uma instância com contas de teste publicamente.

## Passo 4 — Criar contas e recurso para demonstração

O clone novo não traz usuários prontos. O script `scripts/preparar_demo.py` cria os perfis **ADMIN**, **RESPONSAVEL** e **SOLICITANTE**, uma sala restrita e seu vínculo com o Responsável. Só funciona com banco PostgreSQL cujo nome contenha `test`.

**Codespaces — Bash (terminal 2, na raiz e com venv ativo):**

```bash
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
python -m scripts.preparar_demo
```

**VS Code — PowerShell (terminal 2, na raiz e com venv ativo):**

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
python -m scripts.preparar_demo
```

O script apresenta os e-mails e **senhas geradas** para as contas novas. Guarde-as somente no ambiente local de testes; **não publique senhas no GitHub nem em capturas de tela**. Em execuções futuras, as contas já existentes mantêm suas senhas e o script não as mostra novamente.

**Observação:** o contêiner da aplicação (`docker compose up --build`) não inclui o diretório `scripts/` no `Dockerfile` atual. Para preparar dados de demonstração, use este procedimento com Python no host.

## Passo 5 — Testar os três perfis pela interface

Acesse a URL da interface e use as credenciais exibidas no passo anterior.

1. **Solicitante:** faça login, pesquise recursos e tente criar uma reserva; confira a lista de reservas.
2. **Responsável:** faça login com outra conta e consulte as solicitações pendentes; se houver solicitação elegível, aprove/rejeite com justificativa.
3. **Administrador:** faça login e confira cadastro de usuários, cadastro de recursos e vínculo de Responsável com recurso.

As telas são separadas por perfil; uma conta não deve conseguir acessar o painel de outro perfil. Para testar um novo perfil, faça logout da sessão anterior.

Se a página abrir mas o login não funcionar, confira a conta criada no **Passo 4** e o terminal da API antes de modificar o código.

## Passo 6 — Conferir as tabelas e a arquitetura

**Codespaces — Bash:**

```bash
python -c "from app.models import Base; print(sorted(Base.metadata.tables))"
ls app/servicos
```

**VS Code — PowerShell:**

```powershell
python -c "from app.models import Base; print(sorted(Base.metadata.tables))"
Get-ChildItem app\servicos -File
```

**Resultado esperado:** tabelas como `users`, `resources`, `reservations`, `reservation_items`, `approvals` e `audit_entries`. A API fica em `app/api/v1.py`, as regras em `app/dominio/`, os serviços em `app/servicos/` e os modelos em `app/models.py`.

Referências: [arquitetura](./docs/prd/arquitetura.md), [modelagem de dados](./docs/prd/modelagem-dados-sistema-academico.dbml) e [RTM](./docs/qualidade/RTM.md).

## Passo 7 — Testar regras de domínio

**Codespaces — Bash:**

```bash
python -m pytest tests/test_regras_dominio.py
```

**VS Code — PowerShell:**

```powershell
python -m pytest tests\test_regras_dominio.py
```

Esses testes exercitam regras de intervalos, disponibilidade e transições de estados. Não dependem da interface do navegador.

## Passo 8 — Executar testes Python e BDD

**Codespaces — Bash:**

```bash
python -m pytest
python -m pytest tests/bdd -o addopts=""
python -m pytest tests/bdd/test_cobertura_bdd.py -o addopts=""
```

**VS Code — PowerShell:**

```powershell
python -m pytest
python -m pytest tests\bdd -o addopts=""
python -m pytest tests\bdd\test_cobertura_bdd.py -o addopts=""
```

O `pytest` padrão exclui testes marcados `integration`. O segundo comando com `-o addopts=""` pode incluir testes que exigem PostgreSQL; certifique-se de ter `DATABASE_URL` definido para o banco de teste nesse terminal. Os cenários Gherkin estão em `tests/bdd/features/`.

## Passo 9 — Testes de integração, concorrência e E2E

Execute apenas com um PostgreSQL de teste acessível e variáveis de ambiente do **Passo 2** configuradas no terminal atual.

**Codespaces — Bash:**

```bash
python -m pytest -o addopts="" -m integration
python -m pytest tests/e2e/test_fluxo_completo.py -o addopts=""
python -m pytest -o addopts="" -m "integration and concorrencia" tests/bdd/test_cenarios_executaveis.py -v
```

**VS Code — PowerShell:**

```powershell
python -m pytest -o addopts="" -m integration
python -m pytest tests\e2e\test_fluxo_completo.py -o addopts=""
python -m pytest -o addopts="" -m "integration and concorrencia" tests\bdd\test_cenarios_executaveis.py -v
```

O teste de concorrência CT-19 procura garantir que requisições simultâneas para a mesma sala não criem reservas conflitantes. Consulte [evidências](./docs/qualidade/evidencias/README.md) para distinguir resultados já comprovados de testes apenas implementados.

## Passo 10 — Verificar estilo, cobertura Python e JavaScript

**Codespaces — Bash:**

```bash
python -m ruff check .
python -m pytest --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing --cov-report=xml:coverage.xml
npm ci --ignore-scripts
npm run test:coverage
```

**VS Code — PowerShell:**

```powershell
python -m ruff check .
python -m pytest --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing --cov-report=xml:coverage.xml
npm ci --ignore-scripts
npm run test:coverage
```

Para os testes JavaScript, instale **Node.js 22**. O `npm run test:coverage` cobre `app.js` e `perfis.js` e aplica limites de 80% de linhas e 70% de branches no conjunto. O arquivo `coverage-js/lcov.info` é consumido pelo SonarCloud.

## Passo 11 — Verificar CI e SonarCloud

Os comandos são iguais nos dois ambientes: não há instalação local obrigatória de SonarCloud para demonstrar o sistema.

- [GitHub Actions — CI](https://github.com/KAYKmatheus/trbalho4na-qualidade/actions/workflows/ci.yml)
- [Pull Request #1](https://github.com/KAYKmatheus/trbalho4na-qualidade/pull/1)
- [Evidências finais do CI](./docs/evidencias/validacao-final-ci.md)

O CI da `principal` foi aprovado para a versão `v1.0.0-rc1`; o Quality Gate do SonarCloud foi aprovado no PR #1. Os segredos `SONAR_TOKEN` e `CI_POSTGRES_PASSWORD` são exclusivos do repositório/CI e **não precisam ser obtidos pelo professor para rodar a aplicação local**.

## Passo 12 — Executar JMeter (opcional, teste de carga)

**Não é necessário executar JMeter para usar ou demonstrar o AlocaSenac.** Em execução anterior com 100 usuários, foram registrados 30,75% de erros; as metas de desempenho não foram atingidas.

Execute a partir da **raiz do repositório**, com PostgreSQL de teste disponível e o Uvicorn rodando na porta 8000 em outro terminal. O Apache JMeter não faz parte da instalação Python e **não vem necessariamente instalado no Codespaces**.

### Codespaces — Bash

**1. Verificar Java e instalar JMeter 5.6.3:**

```bash
java -version
curl -fL https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz -o /tmp/apache-jmeter-5.6.3.tgz
tar -xzf /tmp/apache-jmeter-5.6.3.tgz -C /tmp
/tmp/apache-jmeter-5.6.3/bin/jmeter --version
```

Se `java -version` falhar, instale Java 17 antes de continuar. Para uma instalação verificada, confira também o checksum SHA-512 do pacote na [distribuição oficial do JMeter](https://jmeter.apache.org/download_jmeter.cgi) antes de extrair.

**2. Preparar os dados de teste (uma vez):**

```bash
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
python -m tests.desempenho.preparar_dados
```

Essa execução deve gerar `tests/desempenho/reservas.csv`. **Se a preparação já informou que criou 100 solicitantes, 100 responsáveis, 100 salas e o CSV, não repita essa etapa**: avance para o teste.

**3. Executar o teste com o JMeter instalado:**

```bash
/tmp/apache-jmeter-5.6.3/bin/jmeter -n \
  -t tests/desempenho/reservas.jmx \
  -Jhost=localhost -Jport=8000 \
  -Jthreads=100 -Jrampup=30 -Jduration=300 \
  -JdataFile=tests/desempenho/reservas.csv \
  -l tests/desempenho/resultados.jtl \
  -e -o tests/desempenho/relatorio-jmeter
```

Use novos caminhos para o arquivo JTL e a pasta HTML ao repetir o teste: o diretório de relatório do JMeter deve estar vazio ou não existir.

### VS Code local — Windows PowerShell

**1.** Instale Java 17 e o [JMeter 5.6.3](https://jmeter.apache.org/download_jmeter.cgi). Extraia o ZIP, por exemplo, em `C:\ferramentas\apache-jmeter-5.6.3` (ajuste o caminho conforme seu computador). Confira a integridade do download e execute:

```powershell
java -version
$jmeter = 'C:\ferramentas\apache-jmeter-5.6.3\bin\jmeter.bat'
& $jmeter --version
```

**2.** Prepare os dados de teste se ainda não tiver gerado o CSV:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test'
python -m tests.desempenho.preparar_dados
```

**3.** Execute o teste:

```powershell
& $jmeter -n -t tests\desempenho\reservas.jmx -Jhost=localhost -Jport=8000 -Jthreads=100 -Jrampup=30 -Jduration=300 -JdataFile=tests\desempenho\reservas.csv -l tests\desempenho\resultados.jtl -e -o tests\desempenho\relatorio-jmeter
```

**Erros comuns:** `ModuleNotFoundError: No module named 'app'` → executar `python -m tests.desempenho.preparar_dados` na raiz do projeto; `jmeter: command not found` → instalar JMeter e utilizar o caminho completo até o executável; pasta de relatório preenchida → escolher outro diretório de saída.

**Segurança:** nunca executar carga em produção. O CSV contém credenciais de teste e não deve ser versionado ou compartilhado. Consulte [plano e resultados](./docs/qualidade/desempenho.md).

## Passo 13 — Encerrar o ambiente de demonstração

No terminal da API, pressione `Ctrl+C`. Em outro terminal, na raiz do projeto:

**Codespaces — Bash:**

```bash
docker compose stop postgres
```

**VS Code — PowerShell:**

```powershell
docker compose stop postgres
```

**Não use `docker compose down -v` sem necessidade:** o `-v` remove volumes e pode apagar os dados da demonstração.

## Dúvidas frequentes

| Sintoma | Causa provável / ação |
|---|---|
| `Connection refused` ou `server closed the connection unexpectedly` na porta 5432 | PostgreSQL ainda não estava pronto: configure `AUTH_SECRET_KEY`, execute `docker compose up -d --wait postgres` e confirme `healthy` em `docker compose ps` antes do Uvicorn |
| `AUTH_SECRET_KEY is missing a value` | Configure `AUTH_SECRET_KEY` **antes** de qualquer comando `docker compose` neste terminal |
| `Cannot connect to the Docker daemon` | Docker Desktop parado ou daemon indisponível no Codespace |
| Porta 5432 já em uso | Outra instalação usa a porta; confira antes de alterar o Compose |
| PowerShell bloqueia `Activate.ps1` | Usar política `Process` temporária ou chamar Python do venv diretamente |
| `uvicorn: command not found` | Ambiente virtual não ativo ou dependências não instaladas; use `python -m uvicorn ...` |
| Login sem usuários | Execute `python -m scripts.preparar_demo` com `DATABASE_URL` do banco de teste |
| Rodou script de demonstração novamente, mas não apareceu senha | Usuários já existiam; o script preserva as credenciais anteriores |
| A página não abre no Codespaces | Verifique a aba `Ports` e abra a URL encaminhada da porta 8000 |
| Erro ao chamar a API em outro terminal | Repita as variáveis de ambiente do banco nesse terminal |

## Fontes internas e escopo

- [README](./README.md)
- [Requisitos funcionais](./docs/prd/requisitos-funcionais-sistema-academico.md)
- [Arquitetura](./docs/prd/arquitetura.md)
- [Casos de teste](./docs/qualidade/casos-de-teste.md)
- [Relatório final](./docs/relatorio-final.md)
- [Limitações de desempenho](./docs/qualidade/desempenho.md)

**Nota:** este guia separa reprodução da aplicação de testes avançados. A instalação limpa e os comandos específicos dos dois ambientes devem ser testados na prática antes de afirmar compatibilidade integral.
