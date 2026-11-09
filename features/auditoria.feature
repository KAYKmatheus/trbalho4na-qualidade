# language: pt
Funcionalidade: Auditoria de operações
  Como Administrador ou Responsável
  Quero consultar um histórico confiável
  Para rastrear alterações e decisões

  # Equivale a: CT-28
  Cenário: Auditar operações relevantes
    Dado que ocorrem criação, alteração, cancelamento, aprovação e bloqueio
    Quando cada operação é persistida
    Então a auditoria registra usuário, data, ação, valor anterior e valor novo

  # Equivale a: CT-29
  Cenário: Proteger auditoria e aprovações contra alteração e exclusão
    Dado que existem registros de auditoria e de aprovação
    Quando uma operação tenta executar UPDATE ou DELETE nesses registros
    Então o banco de dados nega a operação

  # Equivale a: CT-38
  Cenário: Registrar conflitos evitados na auditoria
    Dado que ocorrem tentativas recusadas por conflito de sala, professor, estoque, bloqueio ou disputa
    Quando cada tentativa é recusada
    Então cada uma gera evento CONFLITO_EVITADO com usuário, recurso, intervalo e motivo
