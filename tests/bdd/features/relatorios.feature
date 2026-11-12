# language: pt
Funcionalidade: Relatórios de utilização
  Como Responsável ou Administrador
  Quero consultar relatórios de um período
  Para acompanhar utilização, carga horária e conflitos

  # Equivale a: CT-31
  # Teste: tests/bdd/test_relatorios.py::test_ct31_report_contains_utilization_teaching_load_and_conflict_count
  Cenário: Gerar relatório de utilização de um período
    Dado que existem reservas e eventos auditáveis em um período
    Quando o Responsável ou Administrador gera o relatório desse período
    Então o relatório apresenta utilização, carga horária e conflitos evitados

  # Equivale a: CT-32
  # Teste: tests/bdd/test_relatorios.py::test_ct32_conflict_counter_increases_for_each_refused_request
  Cenário: Atualizar contador de conflitos evitados no relatório
    Dado que o relatório apresenta o total de conflitos evitados
    Quando são provocados conflitos e o relatório é consultado novamente
    Então o contador aumenta na mesma quantidade de conflitos registrados
