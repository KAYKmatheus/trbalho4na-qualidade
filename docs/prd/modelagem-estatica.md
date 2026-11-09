# Modelagem estática

## Diagrama de componentes agnóstico de tecnologia

```mermaid
flowchart LR
    U[Usuário]
    P[Apresentação]
    A[API]
    APP[Aplicação]
    D[Dados]
    H[Histórico e auditoria]
    B[(Banco de dados)]

    U --> P
    P --> A
    A --> APP
    APP --> D
    APP --> H
    D --> B
    H --> B
```

## Diagrama de classes das entidades

```mermaid
classDiagram
    class Usuarios {
        +uuid id
        +varchar nome
        +varchar email
        +perfil perfil_usuario
        +boolean ativo
    }

    class Salas {
        +uuid id
        +varchar nome
        +varchar tipo
        +integer capacidade
        +varchar localizacao
        +boolean restrita
        +boolean ativa
    }

    class Professores {
        +uuid id
        +uuid usuario_id
        +varchar nome
        +varchar email
        +boolean ativo
    }

    class Competencias {
        +uuid id
        +varchar nome
        +text descricao
    }

    class Materiais {
        +uuid id
        +varchar nome
        +varchar tipo
        +integer quantidade_total
        +boolean restrito
        +boolean ativo
    }

    class Reservas {
        +uuid id
        +uuid solicitante_id
        +timestamptz inicio
        +timestamptz fim
        +status status_reserva
        +integer versao
        +text finalidade
    }

    class ReservaItens {
        +uuid id
        +uuid reserva_id
        +uuid sala_id
        +uuid professor_id
        +uuid material_id
        +timestamptz inicio
        +timestamptz fim
        +integer quantidade
        +status status_reserva_item
    }

    class Aprovacoes {
        +uuid id
        +uuid reserva_item_id
        +uuid responsavel_id
        +tipo_decisao tipo
        +decisao_aprovacao decisao
        +text justificativa
    }

    class Bloqueios {
        +uuid id
        +uuid sala_id
        +uuid professor_id
        +uuid material_id
        +tipo_bloqueio tipo
        +timestamptz inicio
        +timestamptz fim
        +text motivo
        +status_bloqueio status
    }

    class RetiradasDevolucoes {
        +uuid id
        +uuid reserva_item_id
        +uuid responsavel_id
        +tipo_movimentacao_material tipo
        +integer quantidade
        +timestamptz ocorrido_em
    }

    class Auditoria {
        +uuid id
        +uuid usuario_id
        +varchar origem
        +varchar entidade
        +uuid entidade_id
        +varchar acao
        +json valor_anterior
        +json valor_novo
        +timestamptz ocorrido_em
    }

    class Notificacoes {
        +uuid id
        +uuid usuario_id
        +uuid reserva_id
        +varchar assunto
        +text mensagem
        +status_notificacao status
    }

    class EscoposResponsavel {
        +uuid id
        +uuid responsavel_id
        +uuid sala_id
        +uuid professor_id
        +uuid material_id
    }

    Usuarios "1" --> "0..*" Reservas
    Usuarios "1" --> "0..*" Notificacoes
    Usuarios "1" --> "0..*" Auditoria
    Usuarios "1" --> "0..*" EscoposResponsavel
    Salas "1" --> "0..*" ReservaItens
    Salas "1" --> "0..*" Bloqueios
    Salas "1" --> "0..*" EscoposResponsavel
    Professores "1" --> "0..*" ReservaItens
    Professores "1" --> "0..*" Bloqueios
    Professores "1" --> "0..*" EscoposResponsavel
    Materiais "1" --> "0..*" ReservaItens
    Materiais "1" --> "0..*" Bloqueios
    Materiais "1" --> "0..*" EscoposResponsavel
    Reservas "1" --> "1..*" ReservaItens
    ReservaItens "1" --> "0..*" Aprovacoes
    ReservaItens "1" --> "0..*" RetiradasDevolucoes
    Professores "1" --> "0..*" Competencias
    Usuarios "1" --> "0..*" Aprovacoes
```

## Mapeamento para o DBML

- `usuarios` mapeia para `usuarios`
- `salas`, `professores`, `materiais`, `competencias`, `reservas`, `reserva_itens`, `aprovacoes`, `bloqueios`, `retiradas_devolucoes`, `auditoria`, `notificacoes` e `escopos_responsavel` seguem as definições do DBML
- associações de `Ref` e `checks` preservam as regras de integridade e escopo definidas em `modelagem-dados-sistema-academico.dbml`
