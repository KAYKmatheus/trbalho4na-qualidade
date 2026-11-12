# language: pt
Funcionalidade: Auditoria de operações
  Como Administrador ou Responsável
  Quero consultar um histórico confiável
  Para rastrear alterações e decisões

  # Equivale a: CT-28
  # Teste: tests/test_reservas.py::test_service_creates_reservation_and_audit_record, tests/test_reservas.py::test_ct28_audits_creation_update_approval_cancel_and_resource_block
  Cenário: Auditar operações relevantes
    Dado que ocorrem criação, alteração, cancelamento, aprovação e bloqueio
    Quando cada operação é persistida
    Então a auditoria registra usuário, data, ação, valor anterior e valor novo

  # Equivale a: CT-29
  # Teste: tests/test_postgres_immutability.py::test_ct29_immutable_tables_reject_update_delete_and_accept_insert
  Cenário: Proteger auditoria e aprovações contra alteração e exclusão
    Dado que existem registros de auditoria e de aprovação
    Quando uma operação tenta executar UPDATE ou DELETE nesses registros
    Então o banco de dados nega a operação

  # Equivale a: CT-38
  # Teste: tests/bdd/test_relatorios.py::test_ct38_avoided_conflict_event_has_actor_resource_interval_and_reason, tests/test_postgres_ct38.py::test_ct38_each_avoided_conflict_is_audited_and_counted_by_report
  Cenário: Registrar conflitos evitados na auditoria
    Dado que ocorrem tentativas recusadas por conflito de sala, professor, estoque, bloqueio ou disputa
    Quando cada tentativa é recusada
    Então cada uma gera evento CONFLITO_EVITADO com usuário, recurso, intervalo e motivo
