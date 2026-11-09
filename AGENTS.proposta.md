# AGENTS.md — Regras do projeto AlocaSenac

1. **Antes de qualquer tarefa**, consulte `.aiox-core/`.
2. **Ao finalizar qualquer tarefa que crie ou edite documentação**, execute a skill `analyze-docs` e inclua o relatório na resposta.
3. **A cada novo passo concluído**, execute a skill `update-tutorial`.
4. Use os identificadores já estabelecidos: `RN01–RN08` (regras de negócio), `FR-xx` (requisitos funcionais), `NFR-xx` (não funcionais), `CT-xx` (casos de teste). Nunca reutilize nem renumere um ID existente.
5. Todo requisito novo ou alterado deve aparecer em `docs/prd/matriz-rastreabilidade.md`.
6. Banco alvo: **PostgreSQL**. Garantias de concorrência (RN02 a RN04) devem ficar no banco, não apenas na aplicação.
7. Em diagramas Mermaid, **não use ponto e vírgula** nas mensagens.
8. Não altere a semântica de auditoria: registros são append-only (RN08).
9. Não marque um caso de teste como aprovado sem evidência em `docs/qualidade/evidencias/`.
