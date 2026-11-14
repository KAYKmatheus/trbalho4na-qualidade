# Checklist de entrega — AlocaSenac

Versão candidata: `v1.0.0-rc1`
Branch de preparação: `feature/ajustes-projeto`
Situação: em preparação

## 1. Repositório e execução

- [x] Repositório GitHub existente.
- [x] README com instruções de execução.
- [x] Código-fonte da aplicação.
- [x] Dockerfile e Docker Compose.
- [ ] Validar execução em clone limpo.
- [ ] Confirmar repositório público na entrega.

## 2. Arquitetura e requisitos

- [x] Requisitos funcionais e não funcionais.
- [x] Regras de negócio documentadas.
- [x] Diagrama de contexto.
- [x] Documentação de arquitetura.
- [x] Fluxos de sequência.
- [x] Decisões arquiteturais (ADR).

Referências: `docs/prd/`.

## 3. Testes e qualidade

- [x] Plano de testes.
- [x] Casos de teste CT-01 a CT-40.
- [x] Testes automatizados com pytest.
- [x] Cenários BDD.
- [x] Testes de integração e concorrência implementados.
- [x] Pipeline GitHub Actions configurado.
- [x] Relatório histórico de cobertura Python.
- [x] Plano de carga JMeter.
- [x] Execução do JMeter com 100 usuários.
- [ ] Validar o CI no commit final.
- [ ] Confirmar cobertura no commit final.
- [ ] Registrar resultado final do SonarCloud.
- [ ] Anexar resumo do JMeter e registrar defeito de desempenho.
- [ ] Finalizar validação manual CT-34.

Referências: `tests/`, `.github/workflows/ci.yml` e
`docs/qualidade/`.

## 4. Rastreabilidade e defeitos

- [x] Matriz de rastreabilidade RTM.
- [x] Registro de defeitos.
- [ ] Atualizar RTM com evidências recentes.
- [ ] Registrar defeito de esgotamento do pool SQLAlchemy.

Referências: `docs/qualidade/RTM.md` e
`docs/qualidade/defeitos.md`.

## 5. Pacote final

- [x] CHANGELOG preparado.
- [ ] Atualizar relatório final.
- [ ] Criar índice de evidências da entrega.
- [ ] Registrar revisão por pares.
- [ ] Criar decisão de qualidade.
- [ ] Confirmar pipeline e evidências da versão candidata.
- [ ] Criar tag anotada `v1.0.0-rc1`.
- [ ] Enviar link do repositório e tag no formulário.

## 6. Riscos conhecidos

- O teste JMeter registrou 294 erros em 956 amostras (30,75%).
- Os logs apontam esgotamento do pool de conexões SQLAlchemy.
- O Quality Gate do SonarCloud ainda não está comprovado como aprovado.
- A cobertura disponível é histórica e precisa ser vinculada
  corretamente à versão entregue.
- A validação manual CT-34 está pendente.

## 7. Condição de encerramento

A entrega só será considerada finalizada após a conferência
dos itens obrigatórios, registro das ressalvas, validação
da versão candidata e criação da tag correspondente.
