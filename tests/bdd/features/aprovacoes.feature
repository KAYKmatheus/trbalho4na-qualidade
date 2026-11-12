# language: pt
Funcionalidade: Aprovação de solicitações
  Como Responsável
  Quero decidir solicitações dentro das regras e do meu escopo
  Para controlar recursos que exigem aprovação

  # Equivale a: CT-21
  # Teste: tests/bdd/test_aprovacoes.py::test_ct21_approval_rechecks_conflict_and_keeps_item_pending
  Cenário: Revalidar disponibilidade antes de aprovar
    Dado que o item de uma solicitação estava disponível quando foi pedido
    E outra reserva ocupou o recurso antes da decisão
    Quando o Responsável tenta aprovar o item
    Então o sistema responde 409 e o item não fica aprovado

  # Equivale a: CT-22
  # Teste: tests/bdd/test_aprovacoes.py::test_ct22_restricted_resource_stays_pending_and_available_until_decision
  Cenário: Manter pendente recurso restrito sem aprovação
    Dado que uma reserva contém um recurso restrito sem decisão
    Quando o sistema consulta o estado e a disponibilidade do recurso
    Então o item permanece PENDENTE e não ocupa a disponibilidade

  # Equivale a: CT-23
  # Teste: tests/bdd/test_aprovacoes.py::test_ct23_decision_requires_justification_and_scope
  Cenário: Recusar decisão sem justificativa ou fora do escopo
    Dado que uma decisão está sem justificativa ou o recurso está fora do escopo do Responsável
    Quando o Responsável tenta registrar a decisão
    Então o sistema responde 422 para justificativa ausente ou 403 para falta de escopo
