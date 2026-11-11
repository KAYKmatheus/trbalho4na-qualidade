# language: pt
Funcionalidade: Conflitos e concorrência de disponibilidade
  Como pessoa usuária do sistema
  Quero que a disponibilidade considere intervalos e quantidades
  Para evitar alocações incompatíveis

  # Equivale a: CT-15
  Cenário: Recusar sobreposição de reservas para a mesma sala
    Dado que há uma reserva ativa de sala em determinado intervalo
    Quando outra reserva da mesma sala solicita um intervalo sobreposto
    Então a segunda reserva é recusada com 409

  # Equivale a: CT-16
  Cenário: Recusar sobreposição na agenda de um professor
    Dado que um professor está reservado em uma sala durante um intervalo
    Quando outra reserva solicita o mesmo professor em outra sala no mesmo intervalo
    Então a segunda reserva é recusada com 409

  # Equivale a: CT-17
  Cenário: Permitir reservas em intervalos contíguos
    Dado que uma reserva termina em determinado horário
    Quando outra reserva do mesmo recurso começa exatamente nesse horário
    Então a segunda reserva é permitida porque o fim do intervalo é aberto

  # Equivale a: CT-18
  Cenário: Recusar pedido de material acima da quantidade livre
    Dado que a quantidade livre de um material é conhecida
    Quando uma reserva pede mais unidades do que estão livres
    Então o sistema recusa a solicitação e informa o recurso indisponível

  # Equivale a: CT-19
  Cenário: Processar requisições simultâneas pela mesma sala
    Dado que N requisições concorrentes solicitam a mesma sala e horário
    Quando o sistema processa as requisições simultaneamente
    Então exatamente uma é confirmada e as demais recebem 409

  # Equivale a: CT-20
  Cenário: Respeitar o estoque em requisições simultâneas de material
    Dado que o estoque do material comporta apenas M unidades
    Quando N requisições concorrentes solicitam esse material
    Então no máximo M unidades ficam confirmadas
