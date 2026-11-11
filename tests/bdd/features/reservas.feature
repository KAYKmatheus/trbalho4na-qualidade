# language: pt
Funcionalidade: Solicitação e manutenção de reservas
  Como Solicitante
  Quero criar, alterar e cancelar reservas
  Para organizar o uso dos recursos acadêmicos

  # Equivale a: CT-10
  Cenário: Criar reserva válida
    Dado que o Solicitante informa solicitante, finalidade, intervalo e ao menos um recurso
    Quando envia a solicitação de reserva
    Então a reserva é registrada com o Solicitante, o intervalo e o recurso

  # Equivale a: CT-11
  Cenário: Recusar reserva sem dados obrigatórios ou com intervalo inválido
    Dado que a reserva não contém recurso ou finalidade, ou tem início maior ou igual ao fim
    Quando o Solicitante envia a reserva
    Então o sistema responde 422 com erro associado ao campo inválido

  # Equivale a: CT-12
  Cenário: Criar reserva combinando sala, professor e materiais
    Dado que a solicitação contém sala, professor, materiais e suas quantidades
    Quando o Solicitante envia a reserva com um intervalo
    Então todos os itens ficam registrados para o mesmo intervalo

  # Equivale a: CT-13
  Cenário: Preservar reserva original quando alteração conflita
    Dado que a reserva original está registrada
    Quando o Solicitante tenta alterá-la para um horário em conflito
    Então o sistema responde 409 e preserva a reserva original

  # Equivale a: CT-14
  Cenário: Cancelar reserva e liberar recurso
    Dado que existe uma reserva ativa
    Quando o Solicitante cancela a reserva
    Então o status passa a CANCELADA e o recurso volta a ficar disponível
