# language: pt
Funcionalidade: Relatórios de utilização
  Como Responsável ou Administrador
  Quero consultar relatórios de um período
  Para acompanhar utilização, carga horária e conflitos

  # Equivale a: CT-31
  Cenário: Gerar relatório de utilização de um período
    Dado que existem reservas e eventos auditáveis em um período
    Quando o Responsável ou Administrador gera o relatório desse período
    Então o relatório apresenta utilização, carga horária e conflitos evitados

  # Equivale a: CT-32
  Cenário: Atualizar contador de conflitos evitados no relatório
    Dado que o relatório apresenta o total de conflitos evitados
    Quando são provocados conflitos e o relatório é consultado novamente
    Então o contador aumenta na mesma quantidade de conflitos registrados
