# Segurança

**Base:** [NFR-01](../prd/requisitos-nao-funcionais-sistema-academico.md) (acesso), NFR-02 (privacidade) e NFR-09 (auditoria).

## Checklist (OWASP Top 10 aplicável)

| Risco | Controle esperado | Verificação | Status |
|---|---|---|---|
| Controle de acesso quebrado | Autenticação, perfil, titularidade e escopo validados no servidor em toda rota | CT-02 a CT-05, teste de acesso a ID de outro usuário | Pendente |
| Falhas criptográficas | Senhas com hash seguro (bcrypt ou argon2), TLS em produção | Revisão de código e configuração | Pendente |
| Injeção | Consultas parametrizadas, validação de entrada | Testes com payloads de injeção de SQL | Pendente |
| Projeto inseguro | Garantias de concorrência no banco | CT-19, CT-20 | Pendente |
| Configuração incorreta | Segredos fora do repositório, mensagens de erro sem detalhes internos | Revisão e varredura de segredos | Pendente |
| Componentes vulneráveis | Dependências atualizadas | Relatório de auditoria de dependências | Pendente |
| Falhas de autenticação | Expiração de sessão e resposta genérica no login | CT-01, CT-02 | Pendente |
| Integridade de dados e logs | Auditoria append-only | CT-28, CT-29 | Pendente |
| Falhas de registro e monitoramento | Eventos de negação e conflito registrados | CT-32 | Pendente |

## Método

1. Executar os casos CT-01 a CT-05 e CT-29 como testes automatizados.
2. Rodar análise estática e varredura de dependências no pipeline.
3. Testar acesso horizontal (usuário A acessando dados do usuário B) em todas as rotas.
4. Arquivar cada resultado em `evidencias/`.

## Privacidade (NFR-02)

Registrar quais dados pessoais são coletados (nome, e-mail), a finalidade e o prazo de retenção, conforme a política institucional e a LGPD.
