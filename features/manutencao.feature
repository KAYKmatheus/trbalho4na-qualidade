# language: pt
Funcionalidade: Bloqueio e manutenção de recursos
  Como Administrador
  Quero bloquear recursos em manutenção
  Para impedir novas alocações durante a indisponibilidade

  # Equivale a: CT-24
  Cenário: Recusar reserva de recurso em manutenção
    Dado que um recurso está em manutenção no período solicitado
    Quando um Solicitante tenta reservá-lo nesse período
    Então a reserva é recusada com 409
