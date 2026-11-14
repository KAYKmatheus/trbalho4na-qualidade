# Histórico de alterações — AlocaSenac

Este documento registra as principais funcionalidades, melhorias e
limitações da versão candidata à entrega acadêmica.

## [1.0.0-rc1] — Em preparação

### Funcionalidades implementadas
- API REST em Python com FastAPI.
- Persistência com PostgreSQL e SQLAlchemy.
- Autenticação e autorização por perfis.
- Cadastro e gerenciamento de recursos acadêmicos.
- Pesquisa de disponibilidade de salas, professores e materiais.
- Criação, alteração e cancelamento de reservas.
- Proteção contra sobreposição de reservas.
- Aprovação de solicitações para recursos restritos.
- Controle de movimentação de materiais.
- Histórico de auditoria e notificações simuladas.
- Relatórios de utilização de recursos.
- Interface web para operações de reserva.

### Qualidade e testes
- Testes automatizados com pytest e cenários BDD.
- Testes de integração e concorrência com PostgreSQL.
- Pipeline GitHub Actions com jobs de qualidade,
  contêiner e integração.
- Integração de análise estática com SonarCloud.
- Relatórios de cobertura Python e JavaScript.
- Plano de teste de carga com Apache JMeter.

### Resultados e limitações conhecidas
- O GitHub Actions apresentou execução bem-sucedida
  na branch de desenvolvimento; a versão da tag final
  ainda precisa ser validada.
- O relatório histórico de cobertura Python registrou
  91,36% de linhas e 75,18% de branches, em execução
  anterior à versão candidata.
- O Quality Gate do SonarCloud ainda precisa de
  aprovação ou registro formal da ressalva.
- O teste JMeter com 100 usuários registrou 956 amostras,
  294 erros (30,75%) e tempo médio de 32,63 segundos.
- Os logs identificaram esgotamento do pool de conexões
  SQLAlchemy durante a carga.
- A validação manual de interface e acessibilidade
  CT-34 ainda depende de evidências.

### Documentação
- Requisitos funcionais e não funcionais.
- Decisões arquiteturais e diagramas.
- Plano e casos de teste.
- Matriz de rastreabilidade (RTM).
- Registro de defeitos.
- Relatório de cobertura e qualidade.
- Documentação do cenário JMeter.

## Observações

Esta versão é uma candidata de release acadêmica.
A criação da tag, a revisão por pares e a decisão final
de qualidade serão realizadas após a conferência
das evidências e do estado do repositório.
