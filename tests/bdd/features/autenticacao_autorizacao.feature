# language: pt
Funcionalidade: Autenticação e autorização
  Como pessoa usuária do sistema
  Quero acessar apenas as funções permitidas ao meu perfil
  Para proteger dados e operações acadêmicas

  # Equivale a: CT-01
  # Teste: tests/bdd/test_autenticacao.py::test_ct01_login_uses_generic_response_for_invalid_credentials
  Cenário: Autenticar com credenciais válidas ou inválidas
    Dado que existem credenciais válidas e inválidas para usuários do sistema
    Quando o usuário tenta iniciar uma sessão com cada conjunto de credenciais
    Então as credenciais válidas geram uma sessão e as inválidas recebem 401 com mensagem genérica

  # Equivale a: CT-02
  # Teste: tests/bdd/test_autenticacao.py::test_ct02_protected_route_rejects_missing_and_expired_tokens
  Cenário: Recusar rota protegida sem token ou com token expirado
    Dado que a rota exige autenticação
    Quando uma requisição chega sem token ou com token expirado
    Então o sistema responde 401 e não altera nenhum dado

  # Equivale a: CT-03
  # Teste: tests/bdd/test_autenticacao.py::test_ct03_requester_cannot_call_admin_only_dependency
  Cenário: Impedir que Solicitante execute função administrativa
    Dado que o usuário autenticado tem perfil Solicitante
    Quando ele chama uma função administrativa
    Então o sistema responde 403 e não altera nenhum dado

  # Equivale a: CT-04
  # Teste: tests/bdd/test_alteracao_cancelamento.py::test_ct04_requester_cannot_change_or_cancel_another_users_reservation
  Cenário: Impedir alteração ou cancelamento de reserva de outra pessoa
    Dado que uma reserva pertence a outro Solicitante
    Quando o Solicitante tenta alterar ou cancelar essa reserva
    Então a operação é negada e a reserva permanece intacta

  # Equivale a: CT-05
  # Teste: tests/bdd/test_aprovacoes.py::test_ct05_responsible_cannot_approve_own_reservation
  Cenário: Impedir aprovação da própria solicitação
    Dado que a solicitação pertence ao usuário que decide
    Quando esse usuário tenta aprovar a solicitação
    Então o sistema nega a operação
