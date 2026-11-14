# Evidências de qualidade — AlocaSenac

## Integração na branch principal

- Pull Request: #1
- Commit de merge: 9432ac12c09cf2f6af178206c90a0abae2628e4c
- Resultado: merge concluído com sucesso.

## GitHub Actions

Execução da principal:
https://github.com/KAYKmatheus/trbalho4na-qualidade/actions/runs/43533759121

Resultado: SUCCESS.

Jobs aprovados:
- Quality
- Integration
- Container

## SonarCloud

O Quality Gate do Pull Request #1 foi aprovado.

https://github.com/KAYKmatheus/trbalho4na-qualidade/pull/1

## Testes automatizados

Últimas validações locais:
- Python: 133 testes aprovados.
- JavaScript: 19 testes aprovados.
- Cobertura JavaScript de linhas: 96,60%.
- Cobertura JavaScript de branches: 82,53%.

## Desempenho — Apache JMeter

Teste realizado em 13/11/2026:
- 100 usuários virtuais.
- 956 amostras.
- 294 erros.
- Taxa de erro: 30,75%.

Resultado: metas de desempenho não atendidas.

Problema identificado: esgotamento do pool de conexões
SQLAlchemy durante a execução sob carga.

A otimização será tratada posteriormente em uma
branch específica, preservando a versão entregue.

## Conclusão

O CI e o Quality Gate foram aprovados.

O projeto está apto à preparação da entrega acadêmica,
com ressalva documentada sobre desempenho sob carga.
