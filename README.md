# Sistema acadêmico de alocação de recursos

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
- [Modelagem de dados (DBML)](./docs/prd/modelagem-dados-sistema-academico.dbml)

## Desenvolvimento

- O banco padrão da aplicação em desenvolvimento é `alocasenac`. Defina
  `DATABASE_URL` e `APP_ENV` no ambiente ou use `.env.example` como referência.
- O banco `alocasenac_test` do `docker-compose.yml` é reservado aos testes de
  integração (`pytest -m integration`); configure `DATABASE_URL` para apontar
  para ele ao executar esses testes.
- Instale as dependências pela fonte única em `pyproject.toml` com
  `pip install -r requirements.txt`.
- Execute a API com `uvicorn app.main:app --reload`.
