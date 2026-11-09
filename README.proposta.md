# AlocaSenac — Sistema de alocação de salas, professores e materiais

> Nome provisório. Troque pelo nome real do projeto.

Aplicação que organiza a alocação de **salas, professores e materiais sem conflitos de horário**. O foco da avaliação é apresentar **evidências objetivas de qualidade, segurança, rastreabilidade e desempenho**, além de o sistema funcionar.

## Personas

| Persona | Resumo | Documento |
|---|---|---|
| Administrador | Gerencia salas, professores, materiais, usuários, bloqueios e manutenções | [administrador.md](./docs/prd/personas/administrador.md) |
| Responsável | Aprova solicitações restritas, valida docentes, acompanha retiradas e devoluções | [responsavel.md](./docs/prd/personas/responsavel.md) |
| Solicitante | Consulta disponibilidade e cria, altera ou cancela as próprias reservas | [solicitante.md](./docs/prd/personas/solicitante.md) |

## Estrutura do repositório

```
├── AGENTS.md
├── README.md
├── tutorial.md
├── docs/
│   ├── prd/
│   │   ├── personas/
│   │   ├── personas-sistema-academico.md
│   │   ├── requisitos-funcionais-sistema-academico.md
│   │   ├── requisitos-nao-funcionais-sistema-academico.md
│   │   ├── modelagem-dados-sistema-academico.dbml
│   │   ├── fluxos-sequencia.md
│   │   └── matriz-rastreabilidade.md
│   └── qualidade/
│       ├── plano-de-testes.md
│       ├── casos-de-teste.md
│       ├── seguranca.md
│       ├── desempenho.md
│       └── evidencias/
└── .aiox-core/development/skills/
    ├── analyze-docs/SKILL.md
    └── update-tutorial/SKILL.md
```

## Documentação

- [Requisitos funcionais](./docs/prd/requisitos-funcionais-sistema-academico.md) (FR-01 a FR-15, RN01 a RN08)
- [Requisitos não funcionais](./docs/prd/requisitos-nao-funcionais-sistema-academico.md) (NFR-01 a NFR-10)
- [Modelagem de dados (DBML)](./docs/prd/modelagem-dados-sistema-academico.dbml), importável em dbdiagram.io
- [Fluxos de sequência](./docs/prd/fluxos-sequencia.md)
- [Matriz de rastreabilidade](./docs/prd/matriz-rastreabilidade.md)
- [Plano de testes](./docs/qualidade/plano-de-testes.md) e [casos de teste](./docs/qualidade/casos-de-teste.md)
- [Segurança](./docs/qualidade/seguranca.md) e [desempenho](./docs/qualidade/desempenho.md)
- [Tutorial de construção](./tutorial.md)

## Roadmap

1. [x] Personas
2. [x] Requisitos funcionais e não funcionais
3. [x] Modelagem de dados
4. [x] Fluxos de sequência, rastreabilidade e plano de qualidade
5. [ ] Definição da pilha tecnológica
6. [ ] Wireframes responsivos
7. [ ] Especificação OpenAPI
8. [ ] Implementação
9. [ ] Execução dos testes e coleta de evidências
