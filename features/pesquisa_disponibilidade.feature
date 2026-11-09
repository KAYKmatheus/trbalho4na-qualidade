# language: pt
Funcionalidade: Pesquisa de recursos e disponibilidade
  Como Solicitante
  Quero pesquisar recursos por critérios e período
  Para encontrar opções disponíveis

  # Equivale a: CT-08
  Cenário: Pesquisar com filtros de recurso e período
    Dado que existem recursos com diferentes tipos, capacidades, localizações e competências
    Quando o Solicitante pesquisa por esses filtros e informa um período
    Então o sistema retorna somente recursos que atendem a todos os filtros

  # Equivale a: CT-09
  Cenário: Excluir da pesquisa recursos bloqueados ou ocupados
    Dado que um recurso está bloqueado ou ocupado no período pesquisado
    Quando o Solicitante pesquisa a disponibilidade desse período
    Então o recurso não aparece como disponível
