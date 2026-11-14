# Decisão de qualidade — AlocaSenac

## 1. Identificação

- **Projeto:** AlocaSenac
- **Versão candidata:** v1.0.0-rc1
- **Branch:** feature/ajustes-projeto
- **Data:** 13/11/2026
- **Commit final:** pendente
- **Decisão:** proposta de LIBERAÇÃO COM RESSALVAS
- **Situação:** aguardando validação e aprovação do grupo

## 2. Justificativa

O projeto possui implementação das funcionalidades acadêmicas,
documentação de requisitos, arquitetura, rastreabilidade,
testes automatizados e integração contínua.

A branch de desenvolvimento apresentou execução bem-sucedida
dos jobs de qualidade, contêiner e integração no GitHub Actions.

Entretanto, a versão candidata ainda possui pendências
de desempenho, análise estática e evidências de entrega.

## 3. Evidências disponíveis

| Evidência | Resultado |
|---|---|
| Testes automatizados | Executados no CI da branch |
| Pipeline GitHub Actions | Jobs aprovados na branch de desenvolvimento |
| Cobertura Python | Medição histórica: 91,36% de linhas e 75,18% de branches |
| JMeter | 100 usuários, 956 amostras e 30,75% de erros |
| RTM | Disponível, com atualizações pendentes |
| Registro de defeitos | Disponível, com novo defeito a registrar |
| SonarCloud | Quality Gate ainda não aprovado |
| CT-34 | Validação manual pendente |

As evidências da execução final deverão ser associadas
ao commit identificado pela tag de entrega.

## 4. Riscos conhecidos

### R-01 — Desempenho sob carga

O teste Apache JMeter com 100 usuários apresentou
294 erros em 956 amostras (30,75%).

Os logs da aplicação identificaram esgotamento do pool
de conexões SQLAlchemy, provocando erros HTTP 500.

**Impacto:** indisponibilidade e elevada latência sob carga.

**Tratamento recomendado:** investigar o gerenciamento
das sessões, dimensionar o pool e repetir os testes.

**Situação:** aberto.

### R-02 — Quality Gate do SonarCloud

A aprovação do pipeline não comprova a aprovação do
Quality Gate, pois o workflow permite que a etapa
de análise estática falhe sem reprovar o job.

**Impacto:** pendências de qualidade estática podem
permanecer sem bloquear a integração.

**Tratamento recomendado:** registrar os indicadores
reais do SonarCloud e corrigir os problemas aplicáveis.

**Situação:** aberto.

### R-03 — Evidências incompletas

Ainda precisam ser consolidadas evidências recentes
de cobertura, validação manual CT-34 e revisão por pares.

**Impacto:** redução da rastreabilidade da entrega.

**Tratamento recomendado:** atualizar os registros
e apontar explicitamente cada evidência disponível.

**Situação:** aberto.

## 5. Condições para a liberação

Antes da decisão definitiva:

- [ ] Validar execução a partir de clone limpo.
- [ ] Verificar autorização e prevenção de dupla reserva.
- [ ] Confirmar execução do CI no commit final.
- [ ] Registrar resultado real do SonarCloud.
- [ ] Atualizar relatório final e RTM.
- [ ] Registrar revisão por pares.
- [ ] Identificar responsáveis pelos riscos.
- [ ] Criar tag anotada v1.0.0-rc1.

## 6. Responsáveis

- **Equipe responsável:** integrantes do projeto AlocaSenac.
- **Responsável pela decisão final:** a definir pelo grupo.
- **Responsável pelo tratamento dos riscos:** a definir.
- **Revisor por pares:** a definir.

## 7. Parecer provisório

A proposta é LIBERAR COM RESSALVAS para fins de avaliação
acadêmica, desde que os limitadores de nota e as condições
obrigatórias de entrega sejam verificados.

Esta proposta não representa aprovação definitiva das
metas de desempenho nem do Quality Gate do SonarCloud.

Caso seja confirmado um defeito bloqueante de autorização
ou integridade de reservas, a decisão deverá ser BLOQUEAR.

A decisão definitiva será registrada após a revisão
das evidências e a aprovação dos integrantes.

---

## Atualização após o merge — 13/11/2026

### Qualidade e integração

- Pull Request #1 integrado à branch `principal`.
- GitHub Actions aprovado após o merge.
- Quality Gate do SonarCloud aprovado no PR #1.
- 19 testes JavaScript aprovados localmente.
- Cobertura JavaScript de linhas: 96,60%.
- Cobertura JavaScript de branches: 82,53%.

Evidência: [Validação final de CI](./evidencias/validacao-final-ci.md).

### Risco de desempenho

O teste JMeter com 100 usuários registrou
294 erros em 956 amostras (30,75%).

O problema de esgotamento do pool SQLAlchemy
permanece aberto.

### Parecer atualizado

Recomenda-se a liberação da versão candidata
`v1.0.0-rc1` para avaliação acadêmica,
com ressalva explícita de desempenho.

Esta recomendação não significa que as metas
de desempenho tenham sido atendidas.

A aprovação definitiva permanece condicionada
à revisão do grupo e à conferência dos requisitos
obrigatórios da entrega.
