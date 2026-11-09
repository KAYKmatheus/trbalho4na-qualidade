# Fluxos de sequência — Sistema acadêmico de reservas

Diagramas Mermaid (ator, Frontend, API, Banco) com caminhos de sucesso e erro. Rotas e códigos HTTP são **propostas** e devem ser confirmadas na especificação OpenAPI (FR-15).

| # | Fluxo | FR | RN | Tabelas |
|---|---|---|---|---|
| 1 | Autenticação e autorização | FR-01 | | usuarios |
| 2 | Cadastro de recursos | FR-02 | RN08 | salas, professores, materiais, auditoria |
| 3 | Pesquisa de disponibilidade | FR-03 | RN02, RN06 | reserva_itens, bloqueios |
| 4 | Criação de reserva | FR-04, FR-06 | RN01 a RN03, RN06 | reservas, reserva_itens |
| 5 | Reservas concorrentes | FR-07 | RN04 | reserva_itens |
| 6 | Aprovação de recurso restrito e validação de docente | FR-08, FR-16 | RN05, RN09, RN10 | aprovacoes, escopos_responsavel |
| 7 | Bloqueio por manutenção | FR-09 | RN06 | bloqueios |
| 8 | Retirada e devolução | FR-10 | RN07 | retiradas_devolucoes |
| 9 | Alteração e cancelamento | FR-05, FR-11, FR-12 | RN08 | reservas, auditoria, notificacoes |
| 10 | Relatórios | FR-13 | | auditoria, reserva_itens |

## 1. Autenticação e autorização (FR-01)

```mermaid
sequenceDiagram
    actor U as Usuário
    participant F as Frontend
    participant A as API
    participant B as Banco
    U->>F: Informa e-mail e senha
    F->>A: POST /auth/login
    A->>B: Busca usuário ativo por e-mail
    alt Credenciais inválidas ou usuário inativo
        A-->>F: 401 credenciais inválidas
        F-->>U: Mensagem genérica sem revelar qual campo falhou
    else Credenciais válidas
        A-->>F: 200 token de sessão com expiração
        F-->>U: Painel conforme o perfil
    end
    U->>F: Acessa função protegida
    F->>A: Requisição com token
    alt Sem token ou token expirado
        A-->>F: 401
    else Perfil ou escopo não autorizado
        A-->>F: 403 sem alterar dados
    else Autorizado
        A-->>F: 200
    end
```

## 2. Cadastro de recursos (FR-02)

```mermaid
sequenceDiagram
    actor AD as Administrador
    participant F as Frontend
    participant A as API
    participant B as Banco
    AD->>F: Preenche dados da sala, professor ou material
    F->>A: POST /recursos
    A->>A: Valida perfil ADMIN e dados
    alt Dados inválidos
        A-->>F: 422 campos inválidos
    else Válido
        A->>B: Inicia transação
        A->>B: Insere recurso
        A->>B: Insere auditoria com valor novo
        B-->>A: Confirma transação
        A-->>F: 201 recurso criado
    end
    AD->>F: Desativa recurso
    F->>A: PATCH /recursos/id ativo=false
    A->>B: Atualiza ativo e registra auditoria
    A-->>F: 200 histórico preservado
```

## 3. Pesquisa de disponibilidade (FR-03)

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant F as Frontend
    participant A as API
    participant B as Banco
    S->>F: Informa filtros e período
    F->>A: GET /recursos/disponiveis
    A->>A: Valida autenticação e filtros
    A->>B: Consulta recursos ativos com os filtros
    A->>B: Exclui bloqueios ativos e itens APROVADA ou CONFIRMADA sobrepostos
    A->>B: Para materiais, calcula quantidade livre no período
    B-->>A: Recursos disponíveis
    A-->>F: 200 lista paginada
    F-->>S: Resultados ou mensagem de nenhum recurso disponível
```

## 4. Criação de reserva (FR-04, FR-06)

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant F as Frontend
    participant A as API
    participant B as Banco
    S->>F: Escolhe recursos, intervalo e finalidade
    F->>A: POST /reservas
    A->>A: Valida autenticação, perfil e dados (RN01)
    alt Dados inválidos
        A-->>F: 422 campos inválidos
        F-->>S: Erro junto ao campo
    else Dados válidos
        A->>B: Inicia transação
        A->>B: Verifica bloqueios e sobreposições de sala, professor e material (RN02, RN03, RN06)
        alt Conflito
            B-->>A: Recurso indisponível
            A->>B: Registra conflito evitado na auditoria
            A-->>F: 409 informa o recurso indisponível
        else Livre, sem recurso restrito e sem professor
            A->>B: Insere reserva e itens com status CONFIRMADA
            A->>B: Insere auditoria e notificação
            A-->>F: 201 reserva confirmada
        else Livre com recurso restrito ou professor (RN05, RN10)
            A->>B: Insere reserva e itens com status PENDENTE
            A->>B: Insere auditoria e notificação
            A-->>F: 202 aguardando aprovação
        end
    end
```

## 5. Reservas concorrentes (FR-07, RN04)

```mermaid
sequenceDiagram
    actor S1 as Solicitante 1
    actor S2 as Solicitante 2
    participant A as API
    participant B as Banco
    par Solicitação 1
        S1->>A: POST /reservas recurso X no mesmo horário
        A->>B: Insere item
    and Solicitação 2
        S2->>A: POST /reservas recurso X no mesmo horário
        A->>B: Insere item
    end
    Note over B: Restrição de exclusão por intervalo para sala e professor, e bloqueio de linha com verificação de estoque para material
    B-->>A: Primeira transação confirmada
    B-->>A: Segunda transação recusada por conflito
    A-->>S1: 201 confirmada
    A-->>S2: 409 conflito, não é apresentada como confirmada
    A->>B: Registra conflito evitado na auditoria
```

## 6. Aprovação de recurso restrito e validação de docente (FR-08, FR-16, RN05, RN10)

```mermaid
sequenceDiagram
    actor R as Responsável
    participant F as Frontend
    participant A as API
    participant B as Banco
    R->>F: Abre fila de pendências
    F->>A: GET /aprovacoes/pendentes
    A->>A: Filtra pelo escopo do responsável
    A-->>F: Lista de itens pendentes
    R->>F: Decide com justificativa
    Note over F,A: Item de professor segue o mesmo fluxo com tipo VALIDACAO_DOCENTE
    F->>A: POST /aprovacoes
    A->>A: Valida escopo (RN09), justificativa e que o responsável não é o solicitante
    alt Justificativa vazia ou fora do escopo
        A-->>F: 422 ou 403
    else Rejeição
        A->>B: Registra decisão, atualiza itens para REJEITADA, auditoria e notificação
        A-->>F: 200 rejeitada
    else Aprovação
        A->>B: Inicia transação e revalida disponibilidade
        alt Conflito surgiu
            A-->>F: 409 não pode ser aprovada
        else Livre
            A->>B: Registra decisão, atualiza itens para APROVADA, auditoria e notificação
            A-->>F: 200 aprovada
        end
    end
```

## 7. Bloqueio por manutenção (FR-09, RN06)

```mermaid
sequenceDiagram
    actor AD as Administrador
    participant F as Frontend
    participant A as API
    participant B as Banco
    AD->>F: Informa recurso, período e motivo
    F->>A: POST /bloqueios
    A->>A: Valida perfil e dados
    A->>B: Busca reservas APROVADA ou CONFIRMADA no período
    alt Há reservas afetadas
        A-->>F: 200 com aviso listando as reservas afetadas
    end
    A->>B: Insere bloqueio ATIVO e auditoria
    A-->>F: 201 bloqueio criado
    Note over A,B: Nova reserva no período recebe 409 por RN06
```

## 8. Retirada e devolução de material (FR-10, RN07)

```mermaid
sequenceDiagram
    actor R as Responsável
    participant F as Frontend
    participant A as API
    participant B as Banco
    R->>F: Registra retirada com item e quantidade
    F->>A: POST /movimentacoes tipo RETIRADA
    A->>B: Valida que o item é de material e está aprovado ou confirmado
    A->>B: Insere evento e auditoria
    A-->>F: 201 retirada registrada
    R->>F: Registra devolução
    F->>A: POST /movimentacoes tipo DEVOLUCAO
    A->>B: Calcula saldo pendente com retiradas menos devoluções
    alt Devolução maior que o saldo
        A-->>F: 422 quantidade acima do retirado
    else Válida
        A->>B: Insere evento e auditoria
        A-->>F: 201 devolução registrada
    end
    A->>B: Consulta pendências para sinalizar no painel
```

## 9. Alteração e cancelamento (FR-05, FR-11, FR-12)

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant F as Frontend
    participant A as API
    participant B as Banco
    S->>F: Altera ou cancela reserva
    F->>A: PUT ou DELETE /reservas/id com versão
    A->>B: Busca reserva
    alt Reserva de outro usuário
        A-->>F: 403 sem alterar dados
    else Versão desatualizada
        A-->>F: 409 reserva foi modificada, recarregar
    else Cancelamento
        A->>B: Atualiza status CANCELADA e itens
        A->>B: Insere auditoria com valor anterior e novo e notificação
        A-->>F: 200 disponibilidade liberada
    else Alteração
        A->>B: Revalida bloqueios e sobreposições
        alt Conflito
            A-->>F: 409 conflito
        else Livre
            A->>B: Atualiza reserva, incrementa versão e registra auditoria
            A-->>F: 200 alterada
        end
    end
```

## 10. Relatórios (FR-13)

```mermaid
sequenceDiagram
    actor U as Administrador ou Responsável
    participant F as Frontend
    participant A as API
    participant B as Banco
    U->>F: Escolhe período e recurso
    F->>A: GET /relatorios
    A->>A: Valida perfil e escopo
    A->>B: Agrega utilização por recurso
    A->>B: Soma carga horária alocada
    A->>B: Conta conflitos evitados na auditoria
    B-->>A: Indicadores
    A-->>F: 200 três indicadores
    F-->>U: Tabelas e gráficos
```
