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

## Desenvolvimento local

Instale as dependências de desenvolvimento com `pip install -r requirements-dev.txt`.
Para iniciar a aplicação em containers, forneça `POSTGRES_PASSWORD` e `DATABASE_URL`
no ambiente do Docker Compose; não grave credenciais no Dockerfile ou no repositório.
O endpoint de healthcheck é `/v1/health`.