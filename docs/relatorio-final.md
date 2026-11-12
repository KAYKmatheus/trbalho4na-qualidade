# Relatório final — AlocaSenac

## Objetivo

Documentar a solução de reserva de salas, professores e materiais, suas
decisões arquiteturais, critérios de qualidade, evidências e limitações.

## Escopo entregue

O repositório contém API FastAPI, serviços de aplicação, persistência
SQLAlchemy/PostgreSQL, migrações, interface web estática, testes unitários,
BDD, concorrência e E2E. Os documentos de requisitos, arquitetura e testes
estão ligados à implementação pela [RTM](./qualidade/RTM.md).

## Arquitetura

A aplicação separa interface web, API, serviços, domínio e persistência. A
API recebe as solicitações, valida autenticação, perfil e escopo, chama os
serviços e persiste os resultados em PostgreSQL. As notificações são simuladas
e gravadas localmente; o sistema não chama provedor externo de e-mail.

Decisões arquiteturais:

- [ADR-01 — integridade e concorrência](./prd/adr-01-integridade-concorrencia.md)
- [ADR-02 — escopo do Responsável](./prd/adr-02-escopo-responsavel.md)
- [ADR-03 — auditoria imutável](./prd/adr-03-auditoria-imutavel.md)
- [ADR-04 — disponibilidade de materiais](./prd/adr-04-disponibilidade-material.md)
- [ADR-05 — API e camadas](./prd/adr-05-api-e-separacao-de-camadas.md)
- [ADR-06 — estados da reserva](./prd/adr-06-estados-da-reserva.md)
- [Diagrama de contexto](./prd/diagrama-contexto.md)

## Regras críticas e proteção no banco

- **Sobreposição:** a migração `002_exclusao_sobreposicao.sql` instala
  `btree_gist` e cria a constraint `reservation_items_no_overlap` com
  `EXCLUDE USING gist` sobre tipo, identificador e intervalo `[)`. Ela protege
  salas e professores nos estados ativos; materiais são excluídos dessa
  constraint para que o controle respeite quantidade.
- **Estoque:** `ReservationService._validate_item_availability` consulta a
  linha de `resources` com `FOR UPDATE` para material e soma as unidades
  reservadas e pendentes antes de permitir a operação.
- **Auditoria:** `003_auditoria_imutavel.sql` instala triggers que recusam
  `UPDATE` e `DELETE` em `audit_entries`, `approvals` e `material_movements`.
  A aplicação grava as ações com `AuditService` e eventos de conflito evitado.

O DBML alinhado às tabelas físicas está em
[modelagem-dados-sistema-academico.dbml](./prd/modelagem-dados-sistema-academico.dbml).
Os modelos e as migrações são a fonte de verdade do esquema.

## Estratégia de testes

- **Unidade:** regras de intervalo, transições de estado e disponibilidade em
  [test_regras_dominio.py](../tests/test_regras_dominio.py).
- **Serviços e API:** testes HTTP autenticados cobrem validação, permissões,
  conflitos, aprovações, movimentações e relatórios.
- **BDD:** cenários em `tests/bdd/features/` apontam para node IDs pytest; o
  teste AST verifica o mapeamento e justificativas para testes sem cenário.
- **Concorrência:** os cenários CT-19 e CT-20 usam PostgreSQL e o código do
  CT-19 configura `THREAD_COUNT` como 10 em
  [test_cenarios_executaveis.py](../tests/bdd/test_cenarios_executaveis.py).
  A execução PostgreSQL não tem evidência neste repositório e permanece
  pendente.
- **E2E:** [test_fluxo_completo.py](../tests/e2e/test_fluxo_completo.py)
  exercita o fluxo pela interface HTTP. O arquivo existe; a execução mais
  recente não foi salva como evidência.

## Resultados registrados

| Medição / execução | Resultado documentado | Evidência |
|---|---|---|
| Validação local em 2026-11-11 | 60 testes passaram e 3 foram desmarcados | [saída completa](./qualidade/evidencias/validacao-limpeza-2026-11-11.txt) |
| Cobertura de linhas | 91,36% (1.121 de 1.227 linhas) | [relatório de cobertura](./qualidade/relatorio-cobertura.md) |
| Cobertura de ramos | 75,18% (212 de 282 ramos) | [relatório de cobertura](./qualidade/relatorio-cobertura.md) |
| Testes contados na geração da cobertura | 84 | [relatório de cobertura](./qualidade/relatorio-cobertura.md) |
| Handler global, etapa vermelha | 1 teste falhou, como esperado | [saída TDD vermelha](./qualidade/evidencias/tdd-handler-vermelho.txt) |
| Handler global, etapa verde | 1 teste passou | [saída TDD verde](./qualidade/evidencias/tdd-handler-verde.txt) |
| Integração PostgreSQL e concorrência | Pendente de execução | [registro de evidências](./qualidade/evidencias/README.md) |
| Interface em navegador e teclado | Pendente de execução manual | [checklist CT-34](./qualidade/evidencias/ct-34-checklist.md) |
| Docker, CI e SonarCloud | Pendente de validação externa/local | [registro de evidências](./qualidade/evidencias/README.md) |
| Desempenho JMeter | Pendente; não há medições de p95 ou erros registradas | [desempenho](./qualidade/desempenho.md) |

Os números de cobertura e contagem de testes acima pertencem à execução
identificada no próprio relatório, cujo commit-base é
`76803453f9cd7fa3beaeb3e577e4e96c17fbd3ff`; não representam uma nova medição
da árvore atual. A execução integral atual sem um arquivo de evidência fica
pendente de registro.

## Defeitos encontrados

O histórico confirmado e as correções correspondentes estão em
[defeitos.md](./qualidade/defeitos.md). O registro contém seis itens com
commits e testes identificados. O defeito de restrição de exclusão de
materiais tem teste PostgreSQL, mas sua execução continua pendente conforme a
evidência disponível.

## Limitações conhecidas

- A integração PostgreSQL não foi executada no ambiente registrado; o
  [README de evidências](./qualidade/evidencias/README.md) informa que
  `DATABASE_URL` não estava configurada e o Docker CLI indisponível.
- A validação visual e por teclado das telas depende de execução e
  preenchimento do [checklist CT-34](./qualidade/evidencias/ct-34-checklist.md).
- Não há medição JMeter salva; nenhuma conclusão de desempenho foi registrada.
- O workflow não foi observado em uma execução de Pull Request. O status
  registrado é “CI: aguardando execução no Pull Request”.
- A análise SonarCloud depende de o grupo configurar `SONAR_TOKEN`; nenhuma
  execução ou quality gate está comprovado por evidência.
- A integração com e-mail permanece fora do escopo atual; as notificações são
  registros simulados.

## Estado `CONFIRMADA`

O grupo decidiu manter `CONFIRMADA` como estado distinto e como estado de itens
que já podem ocupar disponibilidade sem aprovação. `PENDENTE` indica espera
por decisão. A decisão está registrada no
[ADR-06](./prd/adr-06-estados-da-reserva.md), e sua relação com os estados
ativos deve permanecer coerente com a constraint do banco.

## Lições aprendidas

- A integridade de concorrência precisa de proteção transacional no banco,
  além da validação de disponibilidade feita pela aplicação.
- Estoque de materiais exige controle por quantidade e bloqueio da linha do
  recurso, não exclusão total de intervalos.
- O DBML deve ser comparado aos modelos e migrações para evitar uma visão
  conceitual diferente do esquema persistido.
- Um resultado só deve ser chamado de aprovado quando houver saída de execução
  guardada; planejamento, testes existentes e execução observada são coisas
  distintas.
