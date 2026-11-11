# language: pt
Funcionalidade: Movimentação de materiais
  Como Responsável
  Quero registrar retirada e devolução de materiais
  Para acompanhar o saldo pendente

  # Equivale a: CT-25
  Cenário: Calcular saldo após retirada e devolução
    Dado que há uma reserva de material com quantidade definida
    Quando o Responsável registra a retirada e a devolução
    Então o saldo pendente é calculado corretamente

  # Equivale a: CT-26
  Cenário: Recusar devolução maior que a quantidade retirada
    Dado que a quantidade retirada está registrada
    Quando o Responsável tenta devolver mais unidades do que foram retiradas
    Então o sistema responde 422 e não cria nenhum registro de devolução

  # Equivale a: CT-27
  Cenário: Sinalizar material retirado e ainda não devolvido
    Dado que existem unidades retiradas sem devolução
    Quando o sistema consulta a pendência e a disponibilidade do material
    Então a pendência é sinalizada e as unidades continuam indisponíveis para outra reserva
