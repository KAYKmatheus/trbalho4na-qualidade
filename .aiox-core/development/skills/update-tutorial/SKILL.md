---
name: update-tutorial
description: Registra cada novo passo concluído no tutorial.md. Executar a cada ação relevante do projeto.
---

# update-tutorial

## Quando usar

Ao concluir um passo que gerou ou alterou artefatos do projeto.

## O que fazer

1. Acrescentar em `tutorial.md` um novo passo numerado com: **Prompt** (o texto literal do usuário, sem reescrever), **Resultado** (arquivos criados ou alterados) e **Aprendizado** (uma frase).
2. Atualizar a árvore de estrutura do tutorial se arquivos foram criados.
3. Atualizar "Próximos passos".
4. Executar `analyze-docs` antes de finalizar.

## Regra

Nunca apagar passos anteriores. Se um passo foi corrigido depois, registrar a correção como novo passo.
