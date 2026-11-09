# language: pt
Funcionalidade: Escopo de atuação do Responsável
  Como Administrador
  Quero atribuir recursos ao escopo dos Responsáveis
  Para limitar as decisões aos recursos autorizados

  # Equivale a: CT-37
  Cenário: Recusar decisões fora do escopo do Responsável
    Dado que o recurso não está no escopo do Responsável
    Quando ele tenta aprovar, rejeitar ou validar uma solicitação para esse recurso
    Então o sistema responde 403 e não altera nenhum dado

  # Equivale a: CT-40
  Cenário: Atribuir e remover recursos do escopo de um Responsável
    Dado que o Administrador gerencia os escopos dos Responsáveis
    Quando atribui ou remove recursos do escopo de um Responsável
    Então a alteração fica auditada e tem efeito imediato nas decisões
