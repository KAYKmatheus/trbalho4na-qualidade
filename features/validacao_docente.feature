# language: pt
Funcionalidade: Validação da alocação de docentes
  Como Responsável com escopo sobre o professor
  Quero validar a alocação de docentes
  Para confirmar solicitações de acordo com a agenda

  # Equivale a: CT-36
  Cenário: Validar alocação de docente dentro do escopo
    Dado que o Responsável tem escopo sobre o professor solicitado
    Quando valida a alocação do docente com justificativa
    Então a decisão VALIDACAO_DOCENTE é registrada e o item passa a APROVADA

  # Equivale a: CT-39
  Cenário: Manter item de professor pendente até validação
    Dado que uma reserva inclui um professor e ainda não foi validada
    Quando o sistema registra a solicitação da reserva
    Então o item do professor fica PENDENTE e não ocupa a agenda até a validação
