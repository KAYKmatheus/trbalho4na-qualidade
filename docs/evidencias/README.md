# Índice de evidências — AlocaSenac

**Versão:** v1.0.0-rc1 (em preparação)
**Branch:** feature/ajustes-projeto
**Commit da versão:** pendente de definição
**Data de preparação:** 13/11/2026

Este índice centraliza os artefatos de qualidade. A existência de
um relatório não significa, por si só, que o requisito foi aprovado.
Resultados históricos são diferenciados das evidências da versão final.

## 1. Requisitos, arquitetura e rastreabilidade

| Evidência | Localização | Situação |
|---|---|---|
| Requisitos funcionais | [Documento](../prd/requisitos-funcionais-sistema-academico.md) | Disponível |
| Requisitos não funcionais | [Documento](../prd/requisitos-nao-funcionais-sistema-academico.md) | Disponível |
| Arquitetura | [Documento](../prd/arquitetura.md) | Disponível |
| Diagrama de contexto | [Documento](../prd/diagrama-contexto.md) | Disponível |
| Diagramas e fluxos de sequência | [Documento](../prd/fluxos-sequencia.md) | Disponível |
| RTM | [Documento](../qualidade/RTM.md) | Atualização pendente |

## 2. Testes e cobertura

| Evidência | Localização | Situação |
|---|---|---|
| Plano de testes | [Documento](../qualidade/plano-de-testes.md) | Disponível |
| Casos CT-01 a CT-40 | [Documento](../qualidade/casos-de-teste.md) | Disponível |
| Testes automatizados | [Diretório](../../tests/) | Implementados |
| Relatório de cobertura Python | [Documento](../qualidade/relatorio-cobertura.md) | Histórico; nova medição pendente |
| Registro de execução dos testes | [Diretório](../qualidade/evidencias/) | Evidências parciais |
| CT-34: interface e acessibilidade | [Checklist](../qualidade/evidencias/ct-34-checklist.md) | Pendente |

O relatório histórico de 12/11/2026 registra 91,36% de cobertura
de linhas e 75,18% de cobertura de branches. Esses valores
não devem ser atribuídos automaticamente ao commit da entrega.

## 3. Integração contínua e análise estática

- [GitHub Actions — workflow CI](https://github.com/KAYKmatheus/trbalho4na-qualidade/actions/workflows/ci.yml)
- [Repositório GitHub](https://github.com/KAYKmatheus/trbalho4na-qualidade)
- [Configuração do pipeline](../../.github/workflows/ci.yml)

**CI:** execução bem-sucedida observada na branch de desenvolvimento;
verificação do commit final pendente.

**SonarCloud:** integração configurada, porém Quality Gate ainda
não comprovado como aprovado. Registrar relatório e resultado
correspondentes à versão candidata.

## 4. Teste de carga — Apache JMeter

- [Plano e instruções](../qualidade/desempenho.md)
- [Plano executável](../../tests/desempenho/reservas.jmx)

- [Resumo dos resultados do JMeter](../qualidade/evidencias/jmeter-resumo-2026-11-13.md)

### Execução realizada em 13/11/2026

| Indicador | Resultado |
|---|---|
| Usuários configurados | 100 |
| Ramp-up | 30 segundos |
| Duração configurada | 300 segundos |
| Amostras registradas | 956 |
| Amostras com erro | 294 |
| Taxa de erro | 30,75% |
| Tempo médio | 32.633 ms |
| Maior tempo | 122.066 ms |
| Resultado | Metas de desempenho não atendidas |

A análise dos logs identificou esgotamento do pool de conexões
do SQLAlchemy (QueuePool: 5 conexões + 10 de overflow;
timeout de 30 segundos), com erros HTTP 500.

Os arquivos JTL e HTML foram gerados localmente em
`/tmp/alocasenac-jmeter-java17/`, no Codespaces utilizado
para a execução. Eles ainda não estão publicados no repositório.

**Atenção:** não versionar o arquivo
`tests/desempenho/reservas.csv`, pois contém credenciais
de contas de teste.

## 5. Defeitos e relatório final

- [Registro de defeitos](../qualidade/defeitos.md)
- [Relatório final](../relatorio-final.md)
- [Checklist de entrega](../entrega/checklist.md)
- [Decisão de qualidade](../decisao-qualidade.md)

**Pendências:** registrar formalmente o defeito de desempenho,
atualizar o relatório final e concluir a decisão de qualidade.

## 6. Fechamento da versão

Antes da entrega, confirmar:

- [ ] Evidências associadas ao commit final.
- [ ] Pipeline verificado no commit da versão.
- [ ] Resultado do SonarCloud registrado.
- [ ] Teste de carga documentado no relatório final.
- [ ] Revisão por pares realizada e registrada.
- [ ] Tag anotada `v1.0.0-rc1` criada.
- [ ] Formulário de entrega preenchido.
