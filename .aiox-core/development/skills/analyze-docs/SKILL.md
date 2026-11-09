---
name: analyze-docs
description: Portão de revisão de documentação. Executar antes de finalizar qualquer tarefa que crie ou edite arquivos .md, .dbml ou diagramas.
---

# analyze-docs

## Quando usar

Sempre ao final de uma tarefa que criou ou editou documentação do projeto.

## Verificações

1. **Links relativos:** todo link `[texto](caminho)` aponta para arquivo existente.
2. **Blocos de código:** fences ``` balanceados e com linguagem indicada.
3. **Mermaid:** nenhuma mensagem contém `;`. Todo `alt`, `else`, `par` e `loop` fecha com `end`. Participantes declarados antes do uso.
4. **DBML:** tabelas referenciadas em `Ref` existem, enums usados estão declarados, sem coluna duplicada.
5. **IDs:** todo `RNxx`, `FR-xx`, `NFR-xx` e `CT-xx` citado existe em sua fonte. Nenhum ID reutilizado ou renumerado.
6. **Rastreabilidade:** requisito novo ou alterado aparece em `docs/prd/matriz-rastreabilidade.md`, e todo CT referenciado existe em `docs/qualidade/casos-de-teste.md`.
7. **README:** estrutura de pastas e lista de documentos em sincronia com o repositório.
8. **Ortografia e consistência de termos** (Solicitante, Responsável, Administrador, recurso, reserva, item).

## Saída

Relatório curto com: verificações aprovadas, problemas encontrados (arquivo, linha, correção) e o que foi corrigido na hora. Se algo não puder ser corrigido, informar ao usuário.
