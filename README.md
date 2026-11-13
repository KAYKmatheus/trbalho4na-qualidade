# AlocaSenac — Sistema acadêmico de alocação de recursos

[![CI](https://github.com/KAYKmatheus/trbalho4na-qualidade/actions/workflows/ci.yml/badge.svg?branch=principal)](https://github.com/KAYKmatheus/trbalho4na-qualidade/actions/workflows/ci.yml)

Sistema para consultar e alocar salas, professores e materiais sem conflitos de
horário.

## Perfis

- **Administrador:** gerencia salas, professores, materiais, usuários,
  bloqueios e manutenções.
- **Responsável:** aprova solicitações especiais, valida a alocação de docentes
  e acompanha retiradas e devoluções de materiais.
- **Solicitante:** professor ou coordenador que consulta disponibilidades e
  cria, altera ou cancela reservas.

## Documentação

- [Personas](./docs/prd/personas-sistema-academico.md)
- [Requisitos funcionais e regras de negócio](./docs/prd/requisitos-funcionais-sistema-academico.md)
- [Requisitos não funcionais](./docs/prd/requisitos-nao-funcionais-sistema-academico.md)
- [Modelagem de dados (DBML)](./docs/prd/modelagem-dados-sistema-academico.dbml)
- [Fluxos de sequência](./docs/prd/fluxos-sequencia.md)
- [Matriz de rastreabilidade](./docs/prd/matriz-rastreabilidade.md)
- [Plano e casos de teste](./docs/qualidade/plano-de-testes.md) e
  [casos de teste CT-01 a CT-40](./docs/qualidade/casos-de-teste.md)
- [Segurança](./docs/qualidade/seguranca.md), [desempenho](./docs/qualidade/desempenho.md)
  e [relatório de cobertura](./docs/qualidade/relatorio-cobertura.md)
- [Arquitetura](./docs/prd/arquitetura.md), [diagrama de contexto](./docs/prd/diagrama-contexto.md),
  [fluxos de sequência](./docs/prd/fluxos-sequencia.md), [modelagem estática](./docs/prd/modelagem-estatica.md)
  e [modelagem dinâmica](./docs/prd/modelagem-dinamica.md)
- [Ajustes e decisões sobre lacunas do PRD](./docs/prd/ajustes-decisoes-lacunas.md)
- ADRs: ADR-01 a ADR-06 estão listadas abaixo.
- [RTM — matriz de rastreabilidade](./docs/qualidade/RTM.md) e
  [matriz PRD](./docs/prd/matriz-rastreabilidade.md)
- [Defeitos confirmados](./docs/qualidade/defeitos.md) e
  [relatório final](./docs/relatorio-final.md)
- [Tutorial principal de implementação](./tutorial-implementacao.md) —
  [tutorial.md aponta para ele](./tutorial.md)
- [Roteiro de apresentação](./docs/apresentacao-roteiro.md)

### Decisões de arquitetura

- [ADR-01 — integridade e concorrência](./docs/prd/adr-01-integridade-concorrencia.md)
- [ADR-02 — escopo do Responsável](./docs/prd/adr-02-escopo-responsavel.md)
- [ADR-03 — auditoria imutável](./docs/prd/adr-03-auditoria-imutavel.md)
- [ADR-04 — disponibilidade de materiais](./docs/prd/adr-04-disponibilidade-material.md)
- [ADR-05 — API e separação de camadas](./docs/prd/adr-05-api-e-separacao-de-camadas.md)
- [ADR-06 — estados da reserva](./docs/prd/adr-06-estados-da-reserva.md)

## Desenvolvimento

- O banco padrão da aplicação em desenvolvimento é `alocasenac`. Defina
  `DATABASE_URL` e `APP_ENV` no ambiente ou use `.env.example` como referência.
- O banco `alocasenac_test` do `docker-compose.yml` é reservado aos testes de
  integração (`pytest -m integration`); configure `DATABASE_URL` para apontar
  para ele ao executar esses testes.
- Para desenvolvimento, instale as dependências com
  `python -m pip install -r requirements.txt`. O CI usa `requirements.lock`,
  gerado em Linux com Python 3.12 e pip-tools a partir desse arquivo, com
  versões e hashes fixados; regenere-o nesse ambiente após alterar dependências.
- Configure `AUTH_SECRET_KEY` com um segredo aleatório fora do repositório.
  O login é feito em `POST /v1/auth/login` com `email` e `password`; envie o
  token retornado como `Authorization: Bearer <token>`. Senhas são armazenadas
  com hash PBKDF2 e contas são provisionadas por Administradores em
  `POST /v1/admin/users`.
- Execute a API com `uvicorn app.main:app --reload`.
- Para executar a aplicação e o PostgreSQL em contêineres, configure
  `AUTH_SECRET_KEY` no ambiente (ou em um `.env` local, ignorado pelo Git) e
  rode `docker compose up --build`. A API fica em `http://localhost:8000` e o
  banco local de teste em `localhost:5432`.
- Rode os testes unitários com `python -m pytest`. Para executar também todos
  os testes de integração/concorrência contra PostgreSQL, use
  `python -m pytest -o addopts=""`; para somente os testes marcados
  `integration`, use `python -m pytest -m integration -o addopts=""`.
- Para gerar a cobertura e o relatório, execute:

  ```powershell
  python -m pytest --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=json:coverage.json
  python -m tests.bdd.gerar_relatorio
  ```

- A cobertura do JavaScript da interface usa Node.js 22. Instale as dependências
  bloqueadas e execute os testes reais de `app/web/static/app.js` com:

  ```powershell
  npm ci --ignore-scripts
  npm run test:coverage
  ```

  O comando valida cobertura mínima de 80% de linhas e 70% de branches e gera
  `coverage-js/lcov.info`, consumido pelo SonarCloud.

- **Interface web:** depois de iniciar a aplicação, abra
  [http://localhost:8000/app/index.html](http://localhost:8000/app/index.html).
  As telas de busca, criação e gerenciamento das próprias reservas ficam
  disponíveis em `/app/buscar.html`, `/app/reservar.html` e `/app/minhas.html`.
  A validação visual e por teclado do CT-34 ainda depende do checklist manual
  em [ct-34-checklist.md](./docs/qualidade/evidencias/ct-34-checklist.md).

- O plano de carga JMeter e os passos para executá-lo estão em
  [desempenho](./docs/qualidade/desempenho.md). A execução ainda depende de
  PostgreSQL com dados de teste locais.
- **Configurar o SonarCloud no GitHub:** entre no SonarCloud, abra seu perfil e
  acesse **My Account → Security → Generate Tokens**. Crie um token de análise
  e copie-o sem inseri-lo em nenhum arquivo do repositório. No GitHub, abra
  **Settings → Secrets and variables → Actions → New repository secret**,
  informe `SONAR_TOKEN` como nome e cole o token como valor. O workflow executa
  o scan e aguarda o quality gate quando esse segredo estiver disponível; sem
  ele, o scan é ignorado. Nunca publique nem versione o token.
- **Configurar o PostgreSQL do CI no GitHub:** crie o segredo de repositório
  `CI_POSTGRES_PASSWORD` em **Settings → Secrets and variables → Actions** com
  um valor aleatório alfanumérico forte. Os workflows o usam nas URLs de
  conexão sem imprimi-lo nos logs. Pull requests de forks não recebem segredos
  do repositório.
