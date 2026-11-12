# language: pt
Funcionalidade: Cadastro e manutenção de recursos
  Como Administrador
  Quero manter o cadastro dos recursos acadêmicos
  Para disponibilizá-los de forma consistente

  # Equivale a: CT-06
  # Teste: tests/bdd/test_recursos.py::test_ct06_admin_creates_updates_and_queries_resource_types
  Cenário: Cadastrar, alterar e consultar recursos
    Dado que o Administrador está autenticado
    Quando cadastra, altera e consulta uma sala, um professor e um material
    Então os dados ficam persistidos e as operações ficam auditadas

  # Equivale a: CT-07
  # Teste: tests/bdd/test_recursos.py::test_ct07_deactivating_resource_preserves_reservation_history
  Cenário: Desativar recurso com reservas históricas
    Dado que um recurso possui reservas históricas
    Quando o Administrador desativa o recurso
    Então o recurso fica inativo e o histórico permanece disponível

