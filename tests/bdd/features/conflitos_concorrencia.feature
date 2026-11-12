# language: pt
Funcionalidade: Conflitos e concorrência de disponibilidade
  Como pessoa usuária do sistema
  Quero que a disponibilidade considere intervalos e quantidades
  Para evitar alocações incompatíveis

  # Equivale a: CT-15
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_recusar_sobreposição_de_reservas_para_a_mesma_sala, tests/test_postgres_integrity.py::test_ct15_overlapping_room_insert_is_rejected_by_database, tests/bdd/test_api_errors.py::test_ct15_overlapping_room_reservation_returns_http_409
  @integration
  Cenário: Recusar sobreposição de reservas para a mesma sala
    Dado que há uma reserva ativa de sala em determinado intervalo
    Quando outra reserva da mesma sala solicita um intervalo sobreposto
    Então a segunda reserva é recusada com 409

  # Equivale a: CT-16
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_recusar_sobreposição_na_agenda_de_um_professor, tests/test_postgres_integrity.py::test_ct16_overlapping_teacher_insert_is_rejected_by_database
  @integration
  Cenário: Recusar sobreposição na agenda de um professor
    Dado que um professor está reservado em uma sala durante um intervalo
    Quando outra reserva solicita o mesmo professor em outra sala no mesmo intervalo
    Então a segunda reserva é recusada com 409

  # Equivale a: CT-17
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_permitir_reservas_em_intervalos_contíguos
  @integration
  Cenário: Permitir reservas em intervalos contíguos
    Dado que uma reserva termina em determinado horário
    Quando outra reserva do mesmo recurso começa exatamente nesse horário
    Então a segunda reserva é permitida porque o fim do intervalo é aberto

  # Equivale a: CT-18
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_recusar_pedido_de_material_acima_da_quantidade_livre, tests/test_regras_dominio.py::test_material_stock_is_rejected_when_exceeded, tests/test_concorrencia.py::test_overlapping_material_reservations_respect_available_stock, tests/bdd/test_api_errors.py::test_ct18_material_over_stock_returns_http_409
  Cenário: Recusar pedido de material acima da quantidade livre
    Dado que a quantidade livre de um material é conhecida
    Quando uma reserva pede mais unidades do que estão livres
    Então o sistema recusa a solicitação e informa o recurso indisponível

  # Equivale a: CT-19
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_processar_requisições_simultâneas_pela_mesma_sala
  @integration @concorrencia
  Cenário: Processar requisições simultâneas pela mesma sala
    Dado que N requisições concorrentes solicitam a mesma sala e horário
    Quando o sistema processa as requisições simultaneamente
    Então exatamente uma é confirmada e as demais recebem 409

  # Equivale a: CT-20
  # Teste: tests/bdd/test_cenarios_executaveis.py::test_respeitar_o_estoque_em_requisições_simultâneas_de_material
  @integration @concorrencia
  Cenário: Respeitar o estoque em requisições simultâneas de material
    Dado que o estoque do material comporta apenas M unidades
    Quando N requisições concorrentes solicitam esse material
    Então no máximo M unidades ficam confirmadas
