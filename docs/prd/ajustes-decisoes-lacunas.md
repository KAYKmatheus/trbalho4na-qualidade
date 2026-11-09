# Ajustes decorrentes das decisões sobre as lacunas

Trechos para colar nos documentos existentes. Depois de aplicar, este arquivo pode ser apagado ou mantido como registro.

Decisões: [matriz de rastreabilidade](./matriz-rastreabilidade.md).

## 1. DBML (`modelagem-dados-sistema-academico.dbml`)

### 1.1 Comentário da coluna `acao` da tabela `auditoria`

Troque a nota da coluna:

```dbml
acao varchar(40) [not null, note: 'Ex.: CRIACAO, ALTERACAO, CANCELAMENTO, APROVACAO, BLOQUEIO, CONFLITO_EVITADO.']
```

E acrescente à nota da tabela `auditoria`:

```dbml
Note: 'Log append-only. Tentativas recusadas por conflito usam acao CONFLITO_EVITADO, com entidade igual ao tipo do recurso disputado (salas, professores ou materiais), entidade_id igual ao id do recurso e, em valor_novo, o intervalo pedido e o motivo (SOBREPOSICAO, BLOQUEIO, ESTOQUE ou CONCORRENCIA). entidade_id e polimorfico e intencionalmente nao possui FK. Restringir UPDATE/DELETE tambem no banco.'
```

### 1.2 Nova tabela `escopos_responsavel`

Cole depois da tabela `bloqueios`:

```dbml
Table escopos_responsavel {
  id uuid [pk, not null, default: `gen_random_uuid()`]
  responsavel_id uuid [not null]
  sala_id uuid
  professor_id uuid
  material_id uuid
  created_at timestamptz [not null, default: `now()`]

  checks {
    num_nonnulls(`sala_id`, `professor_id`, `material_id`) = 1
  }

  indexes {
    (responsavel_id, sala_id) [unique]
    (responsavel_id, professor_id) [unique]
    (responsavel_id, material_id) [unique]
  }

  Note: 'Recursos que o Responsavel pode decidir (RN09). Exatamente uma entre sala_id, professor_id e material_id deve ser preenchida. O PostgreSQL trata NULL como distinto em indices unicos, entao cada indice impede duplicidade apenas do tipo de recurso correspondente.'
}
```

Cole junto das demais `Ref`:

```dbml
Ref: escopos_responsavel.responsavel_id > usuarios.id [delete: cascade]
Ref: escopos_responsavel.sala_id > salas.id [delete: restrict]
Ref: escopos_responsavel.professor_id > professores.id [delete: restrict]
Ref: escopos_responsavel.material_id > materiais.id [delete: restrict]
```

### 1.3 Comentário de garantias (item 4 da lista)

Substitua o item 4 por:

```text
// 4. Validar em transacao que recurso_id corresponda ao recurso do item em
//    aprovacoes e retiradas_devolucoes, que o responsavel tenha perfil
//    RESPONSAVEL e que o recurso do item esteja em escopos_responsavel desse
//    responsavel (RN09), e que movimentos de devolucao nao excedam retiradas.
```

E a linha do final do cabeçalho que diz "O escopo institucional dos Responsaveis ainda nao foi definido" pode ser trocada por:

```text
// - O escopo dos Responsaveis e definido pela tabela escopos_responsavel (RN09).
//   Um Responsavel decide apenas itens cujo recurso esteja no seu escopo.
```

## 2. Requisitos funcionais

### 2.1 Regras de negócio (acrescentar a lista de RN)

```markdown
- **RN09 — Escopo do Responsável:** o Responsável só pode aprovar, rejeitar ou validar itens cujo recurso esteja no escopo atribuído a ele pelo Administrador.
- **RN10 — Validação de docente:** todo item de reserva que aloca um professor depende da validação de um Responsável com escopo sobre esse professor antes de ser confirmado.
```

Atualize também o texto da RN08 para: "... identificando quem realizou a ação, quando, o que foi alterado e os valores anterior e novo. Tentativas recusadas por conflito também geram registro (conflito evitado)."

### 2.2 FR-01 (acrescentar critério)

```markdown
- O escopo de decisão do Responsável é definido pelos recursos atribuídos a ele (RN09), e uma decisão fora desse escopo é recusada.
```

### 2.3 FR-02 (trocar a primeira linha de critérios e acrescentar um critério)

Troque o primeiro critério por:

```markdown
- Os cadastros permitem informar os dados necessários à pesquisa: tipo, capacidade e localização de salas, competências de professores, e tipo e quantidade de materiais. A disponibilidade de salas, professores e materiais é calculada a partir das reservas ativas, dos bloqueios e da situação ativa do recurso, sem janelas de horário cadastradas.
```

Acrescente:

```markdown
- O Administrador atribui e remove recursos do escopo de cada Responsável, e essas alterações são auditadas (RN09).
```

### 2.4 FR-04 (ajustar o último critério)

Troque o último critério por:

```markdown
- Reservas que incluem apenas salas e materiais não restritos podem seguir sem aprovação. Reservas com recurso restrito seguem o FR-08, e itens de professor seguem o FR-16.
```

### 2.5 FR-08 (acrescentar critério)

```markdown
- Somente um Responsável com o recurso no escopo atribuído pode decidir a solicitação (RN09).
```

### 2.6 FR-11 (acrescentar critério)

```markdown
- Tentativas recusadas por sobreposição, bloqueio, estoque insuficiente ou perda de disputa simultânea geram um evento de conflito evitado, com o usuário, o recurso disputado, o intervalo pedido e o motivo.
```

### 2.7 FR-13 (trocar o critério sobre conflitos evitados)

```markdown
- Conflitos evitados correspondem aos eventos de conflito evitado registrados no histórico (FR-11) no período consultado.
```

### 2.8 Novo FR-16

Cole depois do FR-15:

```markdown
### FR-16 — Validar a alocação de docentes

O sistema deve exigir que um Responsável com escopo sobre o professor valide a alocação de docentes antes de confirmar o item correspondente da reserva.

**Critérios de aceite**

- Um item que aloca professor é criado como pendente, não confirma a reserva e não ocupa a agenda do professor até a validação (RN10).
- Antes da decisão, o Responsável consulta a competência cadastrada, a agenda do professor e a finalidade da reserva, e o sistema revalida a disponibilidade (RN03, RN04).
- A decisão (validar ou rejeitar) exige justificativa registrada e fica no histórico, com tipo de decisão de validação de docente.
- O Solicitante é notificado do resultado e consulta o motivo da rejeição.
- Somente um Responsável com o professor no escopo atribuído valida a alocação (RN09), e o Solicitante não valida a própria reserva.
```

### 2.9 Premissas confirmadas (acrescentar)

```markdown
- O Administrador define o escopo dos Responsáveis atribuindo recursos a cada um (RN09).
- A disponibilidade de salas, professores e materiais é calculada por agenda, bloqueios e situação ativa, sem tabela de janelas de horário.
- Itens de professor dependem de validação do Responsável (RN10, FR-16).
```

Em "Pontos para validação institucional", o item 1 passa a ser apenas "Definir quais recursos são restritos".

## 3. Requisitos não funcionais

No NFR-03, ao final da seção, acrescente:

```markdown
**Observação:** a RN08 (auditoria) não é verificada neste requisito, e sim no NFR-09. Este requisito trata de integridade e concorrência (RN01 a RN07).
```

Atualize a rastreabilidade do NFR-01 para incluir RN09 e o FR-16.

## 4. Demais arquivos

- `README.md`: atualizar "FR-01 a FR-15, RN01 a RN08" para "FR-01 a FR-16, RN01 a RN10".
- `tutorial.md`: acrescentar um passo registrando a decisão das lacunas e o prompt usado.
