# Modelagem dinâmica

## FR-01 — Autenticar usuários e autorizar ações por perfil

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Informe e-mail e senha
    UI->>API: Envia credenciais
    API->>APP: Valida usuário e perfil
    APP->>DB: Busca conta ativa
    alt Credenciais inválidas
        DB-->>APP: Sem registro ou inativo
        APP-->>API: 401 sem detalhes
        API-->>UI: Mensagem genérica
        UI-->>S: Acesso negado
    else Credenciais válidas
        DB-->>APP: Dados válidos
        APP-->>API: Token de sessão
        API-->>UI: Sessão liberada
        UI-->>S: Painel conforme perfil
    end
    Note over S,DB: Persona Solicitante e Administrador, RN01, RN09, NFR-01, NFR-05, NFR-11
```

## FR-02 — Cadastrar, consultar e manter recursos

```mermaid
sequenceDiagram
    actor AD as Administrador
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    AD->>UI: Acessa cadastro de recursos
    UI->>API: Solicita registro de sala, professor ou material
    API->>APP: Valida perfil administrativo
    APP->>DB: Atualiza cadastro
    DB-->>APP: Registro persistido
    APP-->>API: 201 criado
    API-->>UI: Recurso salvo
    UI-->>AD: Confirma operação
    Note over AD,DB: Persona Administrador, RN08, RN09, NFR-01, NFR-10, NFR-11
```

## FR-03 — Pesquisar recursos e disponibilidade

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Seleciona filtros e período
    UI->>API: GET recursos disponíveis
    API->>APP: Calcula disponibilidade
    APP->>DB: Consulta recursos ativos e reservas
    DB-->>APP: Lista disponível
    APP-->>API: Resultado filtrado
    API-->>UI: Recursos e filtros
    UI-->>S: Lista de recursos disponíveis
    Note over S,DB: Persona Solicitante, RN02, RN03, RN06, NFR-04, NFR-06, NFR-11
```

## FR-04 — Criar solicitações de reserva

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Solicita reserva
    UI->>API: POST reserva com intervalo e finalidade
    API->>APP: Valida dados e regras
    APP->>DB: Insere reserva e itens
    alt Conflito
        DB-->>APP: Recurso indisponível
        APP-->>API: 409 conflito
        API-->>UI: Mensagem de indisponibilidade
        UI-->>S: Reserva não confirmada
    else Disponível
        DB-->>APP: Registro criado
        APP-->>API: 201 confirmada
        API-->>UI: Reserva aceita
        UI-->>S: Status atual
    end
    Note over S,DB: Persona Solicitante, RN01, RN02, RN03, RN04, RN05, RN06, NFR-03, NFR-04, NFR-11
```

## FR-05 — Alterar e cancelar solicitações ou reservas

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Solicita alteração ou cancelamento
    UI->>API: PUT ou DELETE reserva
    API->>APP: Valida autoria e versão
    APP->>DB: Revalida disponibilidade
    alt Reserva de terceiro
        DB-->>APP: Sem permissão
        APP-->>API: 403
        API-->>UI: Negado
        UI-->>S: Sem alteração
    else Reserva própria
        DB-->>APP: Atualização aceita
        APP-->>API: 200 ou 409
        API-->>UI: Estado atualizado
        UI-->>S: Reserva alterada ou cancelada
    end
    Note over S,DB: Persona Solicitante, RN01, RN02, RN08, NFR-01, NFR-05, NFR-06, NFR-11
```

## FR-06 — Detectar conflitos de disponibilidade

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Cria ou altera reserva
    UI->>API: Envia reserva
    API->>APP: Revalida reservas ativas
    APP->>DB: Consulta salas, professores e materiais
    alt Conflito
        DB-->>APP: Sobreposição detectada
        APP-->>API: 409 indisponível
        API-->>UI: Aviso de conflito
        UI-->>S: Operação recusada
    else Sem conflito
        DB-->>APP: Disponibilidade válida
        APP-->>API: Próximo passo
        API-->>UI: Continuidade da operação
        UI-->>S: Reserva processada
    end
    Note over S,DB: Persona Solicitante, RN02, RN03, RN06, RN07, NFR-03, NFR-04, NFR-11
```

## FR-07 — Impedir dupla reserva em solicitações simultâneas

```mermaid
sequenceDiagram
    actor S1 as Solicitante 1
    actor S2 as Solicitante 2
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S1->>API: Envia reserva concorrente
    S2->>API: Envia reserva concorrente
    API->>APP: Encaminha operações
    APP->>DB: Verifica conflito e estoque
    alt Primeira operação vence
        DB-->>APP: Operação confirmada
        APP-->>S1: 201 confirmado
        APP-->>S2: 409 conflito
    else Segunda operação vence
        DB-->>APP: Operação confirmada
        APP-->>S2: 201 confirmado
        APP-->>S1: 409 conflito
    end
    Note over S1,DB: Persona Solicitante, RN04, NFR-03, NFR-04, NFR-11
```

## FR-08 — Exigir aprovação para recursos restritos

```mermaid
sequenceDiagram
    actor R as Responsável
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    R->>UI: Acessa pendências
    UI->>API: GET aprovações pendentes
    API->>APP: Filtra escopo e pendências
    APP->>DB: Consulta itens restritos
    R->>UI: Decide e justifica
    UI->>API: POST decisão
    API->>APP: Valida escopo e justificativa
    APP->>DB: Registra aprovação ou rejeição
    DB-->>APP: Decisão persistida
    APP-->>API: 200
    API-->>UI: Resultado
    UI-->>R: Decisão registrada
    Note over R,DB: Persona Responsável, RN05, RN09, NFR-01, NFR-06, NFR-11
```

## FR-09 — Bloquear recursos em manutenção

```mermaid
sequenceDiagram
    actor AD as Administrador
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    AD->>UI: Define bloqueio
    UI->>API: POST bloqueio
    API->>APP: Valida dados e perfil
    APP->>DB: Cria bloqueio ativo
    DB-->>APP: Bloqueio registrado
    APP-->>API: 201
    API-->>UI: Bloqueio criado
    UI-->>AD: Confirmação
    Note over AD,DB: Persona Administrador, RN06, RN08, NFR-03, NFR-05, NFR-11
```

## FR-10 — Registrar retirada e devolução de materiais e equipamentos

```mermaid
sequenceDiagram
    actor R as Responsável
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    R->>UI: Registra retirada
    UI->>API: POST movimentação de retirada
    API->>APP: Valida item e quantidade
    APP->>DB: grava evento e saldo
    R->>UI: Registra devolução
    UI->>API: POST movimentação de devolução
    API->>APP: Calcula saldo pendente
    alt Saldo insuficiente
        DB-->>APP: Quantidade acima do retirado
        APP-->>API: 422
        API-->>UI: Erro de devolução
        UI-->>R: Operação negada
    else Saldo suficiente
        DB-->>APP: Atualização aceita
        APP-->>API: 201
        API-->>UI: Devolução registrada
        UI-->>R: Situação atualizada
    end
    Note over R,DB: Persona Responsável, RN07, RN08, NFR-03, NFR-05, NFR-06, NFR-11
```

## FR-11 — Manter histórico auditável

```mermaid
sequenceDiagram
    actor AD as Administrador
    actor R as Responsável
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    AD->>UI: Executa ação relevante
    UI->>API: Solicita operação
    API->>APP: Processa alteração
    APP->>DB: grava auditoria
    DB-->>APP: Log persistido
    APP-->>API: Resposta da operação
    API-->>UI: Estado final
    UI-->>R: Histórico disponível para consulta
    Note over AD,DB: Persona Administrador e Responsável, RN08, RN09, NFR-01, NFR-02, NFR-05, NFR-09, NFR-11
```

## FR-12 — Notificar mudanças de estado

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Solicita operação
    UI->>API: Envia ação
    API->>APP: Processa solicitação
    APP->>DB: Atualiza reserva e status
    APP->>DB: Cria notificação simulada
    DB-->>APP: Registro persistido
    APP-->>API: 200 ou 202
    API-->>UI: Estado atualizado
    UI-->>S: Mensagem de resultado
    Note over S,DB: Persona Solicitante, RN08, NFR-01, NFR-02, NFR-06, NFR-11
```

## FR-13 — Apresentar relatórios de utilização

```mermaid
sequenceDiagram
    actor R as Responsável
    actor AD as Administrador
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    R->>UI: Solicita relatório
    UI->>API: GET relatórios
    API->>APP: Valida perfil e escopo
    APP->>DB: Agrega dados de reservas e auditoria
    DB-->>APP: Indicadores consolidados
    APP-->>API: Dados do relatório
    API-->>UI: Tabela e gráfico
    UI-->>AD: Relatório de utilização
    Note over R,DB: Persona Responsável e Administrador, RN08, NFR-01, NFR-02, NFR-04, NFR-10, NFR-11
```

## FR-14 — Oferecer interface responsiva e mensagens compreensíveis

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Navega em fluxo principal
    UI->>API: Requisição de recurso
    API->>APP: Processa operação
    alt Falha de validação
        DB-->>APP: Erro de regra
        APP-->>API: 422 ou 409
        API-->>UI: Mensagem clara
        UI-->>S: Explanação do problema
    else Sucesso
        DB-->>APP: Estado válido
        APP-->>API: 200 ou 201
        API-->>UI: Confirmação
        UI-->>S: Resultado em linguagem direta
    end
    Note over S,DB: Persona Solicitante, Responsável e Administrador, NFR-06, NFR-07, NFR-08, NFR-11
```

## FR-15 — Documentar API ou fluxos públicos

```mermaid
sequenceDiagram
    actor AD as Administrador
    participant UI as Interface
    participant DOC as Documentação
    participant API as API

    AD->>DOC: Consulta fluxos públicos
    DOC->>API: Referencia operações
    API-->>DOC: Endpoints e regras
    DOC-->>AD: Documento atualizado
    Note over AD,API: Persona Administrador, NFR-07, NFR-08, NFR-10, NFR-12
```

## FR-16 — Validar a alocação de docentes

```mermaid
sequenceDiagram
    actor S as Solicitante
    actor R as Responsável
    participant UI as Interface
    participant API as API
    participant APP as Aplicação
    participant DB as Dados

    S->>UI: Solicita reserva com professor
    UI->>API: POST reserva com docente
    API->>APP: Valida item de professor
    APP->>DB: Consulta escopo e agenda
    alt Sem escopo ou conflito
        DB-->>APP: Recurso fora do escopo ou indisponível
        APP-->>API: 403 ou 409
        API-->>UI: Rejeição com justificativa
        UI-->>S: Reserva pendente ou recusada
    else Escopo válido
        APP-->>API: Solicita decisão do responsável
        API-->>UI: Encaminha pendência
        UI-->>R: Requer validação
        R->>UI: Aprova ou rejeita
        UI->>API: POST decisão de docente
        API->>APP: Registra justificativa e resultado
        APP->>DB: Atualiza item e histórico
        DB-->>APP: Registro persistido
        APP-->>API: 200
        API-->>UI: Resultado final
        UI-->>S: Notificação do resultado
    end
    Note over S,DB: Persona Solicitante e Responsável, RN03, RN09, RN10, NFR-01, NFR-03, NFR-06, NFR-10, NFR-11
```
