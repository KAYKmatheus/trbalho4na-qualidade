# CT-34 — checklist manual de interface

**Status:** Pendente de execução manual. Não registrar como aprovado até
preencher este checklist e salvar as capturas na pasta de evidências.

## Dados da execução

- Data: ____________________
- Executor: ____________________
- Navegador e versão: ____________________
- Resultado geral: ____________________
- Pasta/nomes das capturas de tela: ____________________

## Preparação

1. Inicie a aplicação com `uvicorn app.main:app --reload` ou `docker compose up --build`.
2. Abra cada rota abaixo no navegador, com zoom em 100%.
3. Repita a verificação nas larguras exatas de 360 px, 768 px, 1280 px e 1920 px.
4. Em cada rota e largura, confirme que não há rolagem horizontal e que o
   conteúdo e os controles permanecem visíveis.
5. Percorra a página somente com `Tab` e `Shift+Tab`. Confirme que o foco está
   sempre visível e que todos os links e controles alcançáveis podem ser usados.
6. Preencha o resultado e salve uma captura por rota e largura, identificada
   como `tela-largura.png`.

## Resultados por rota e largura

| Rota | Largura | Sem rolagem horizontal? | Foco visível e navegação por teclado? | Resultado / observações | Captura |
|---|---:|---|---|---|---|
| `/app/index.html` | 360 px | ______ | ______ | ____________________ | ____________________ |
| `/app/index.html` | 768 px | ______ | ______ | ____________________ | ____________________ |
| `/app/index.html` | 1280 px | ______ | ______ | ____________________ | ____________________ |
| `/app/index.html` | 1920 px | ______ | ______ | ____________________ | ____________________ |
| `/app/buscar.html` | 360 px | ______ | ______ | ____________________ | ____________________ |
| `/app/buscar.html` | 768 px | ______ | ______ | ____________________ | ____________________ |
| `/app/buscar.html` | 1280 px | ______ | ______ | ____________________ | ____________________ |
| `/app/buscar.html` | 1920 px | ______ | ______ | ____________________ | ____________________ |
| `/app/reservar.html` | 360 px | ______ | ______ | ____________________ | ____________________ |
| `/app/reservar.html` | 768 px | ______ | ______ | ____________________ | ____________________ |
| `/app/reservar.html` | 1280 px | ______ | ______ | ____________________ | ____________________ |
| `/app/reservar.html` | 1920 px | ______ | ______ | ____________________ | ____________________ |
| `/app/minhas.html` | 360 px | ______ | ______ | ____________________ | ____________________ |
| `/app/minhas.html` | 768 px | ______ | ______ | ____________________ | ____________________ |
| `/app/minhas.html` | 1280 px | ______ | ______ | ____________________ | ____________________ |
| `/app/minhas.html` | 1920 px | ______ | ______ | ____________________ | ____________________ |

## Conclusão

- Problemas encontrados: __________________________________________________
- Resultado final (Aprovado / Reprovado / Incompleto): ____________________
- Executor e data: ________________________________________________________
