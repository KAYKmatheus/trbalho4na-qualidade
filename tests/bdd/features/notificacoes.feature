# language: pt
Funcionalidade: Notificações de mudanças de estado
  Como pessoa usuária do sistema
  Quero receber notificações sobre operações relevantes
  Para conhecer o resultado das solicitações

  # Equivale a: CT-30
  # Teste: tests/bdd/test_notificacoes.py::test_ct30_notifications_are_recorded_for_send_approve_reject_and_cancel
  Cenário: Gerar notificações para mudanças de estado
    Dado que uma solicitação pode ser enviada, aprovada, rejeitada ou cancelada
    Quando ocorre cada mudança de estado
    Então uma notificação simulada é gerada e a rejeição inclui a justificativa
