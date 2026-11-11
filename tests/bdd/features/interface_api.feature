# language: pt
Funcionalidade: Interface e documentação da API
  Como pessoa usuária ou Administrador
  Quero mensagens compreensíveis, interface acessível e contratos documentados
  Para operar e integrar o sistema com segurança

  # Equivale a: CT-33
  Cenário: Apresentar mensagens corretas para falhas
    Dado que pode ocorrer erro de validação, permissão, conflito ou falha
    Quando uma dessas situações acontece
    Então a mensagem é compreensível e nunca apresenta a operação como sucesso

  # Equivale a: CT-34
  Cenário: Usar os fluxos principais em diferentes larguras e somente pelo teclado
    Dado que os fluxos principais são testados entre 360 e 1920 pixels
    Quando uma pessoa os executa usando apenas o teclado
    Então não há perda de conteúdo nem rolagem horizontal

  # Equivale a: CT-35
  Cenário: Manter documentação OpenAPI alinhada às rotas
    Dado que a documentação OpenAPI descreve as operações públicas
    Quando ela é comparada com as rotas reais
    Então não há divergências entre documentação e implementação
