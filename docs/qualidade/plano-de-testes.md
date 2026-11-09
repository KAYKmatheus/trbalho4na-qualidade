# Plano de testes

**Base:** [FR e RN](../prd/requisitos-funcionais-sistema-academico.md), [NFR](../prd/requisitos-nao-funcionais-sistema-academico.md), [matriz de rastreabilidade](../prd/matriz-rastreabilidade.md).

## Objetivo

Produzir evidências objetivas de que o sistema cumpre os 14 requisitos obrigatórios e os NFR de segurança, concorrência, desempenho e auditabilidade.

## Níveis e tipos de teste

| Nível | Foco | Exemplos |
|---|---|---|
| Unitário | Regras puras | Cálculo de sobreposição de intervalos, saldo de material, validação de reserva |
| Integração | API com banco real PostgreSQL | Restrição de exclusão, transações, auditoria append-only |
| API / contrato | Rotas, códigos HTTP, autorização | Perfis, 401, 403, 409, 422 |
| Concorrência | Disputas simultâneas | CT-19 e CT-20 com N requisições paralelas |
| Segurança | Controle de acesso e ataques comuns | Ver [segurança](./seguranca.md) |
| Desempenho | Latência p95 sob carga | Ver [desempenho](./desempenho.md) |
| Interface / E2E | Fluxos das três personas | Responsividade 360 a 1920 px, teclado, mensagens |

## Ambiente

- Banco: PostgreSQL com a extensão `btree_gist`, mesma versão da implantação.
- Dados de teste reproduzíveis por script (seed), documentados na pasta de evidências.
- Testes de integração e concorrência **não** usam banco simulado, pois o objetivo é provar a garantia no banco.

## Critérios de entrada e saída

- **Entrada:** requisito com critério de aceite no FR e caso de teste em [casos-de-teste.md](./casos-de-teste.md).
- **Saída:** 100% dos casos de severidade Alta aprovados, nenhum defeito aberto de severidade Alta ou Crítica, e evidência arquivada para cada caso.

## Métricas a reportar

- Casos planejados, executados, aprovados e reprovados por requisito.
- Cobertura de código (meta inicial proposta: 80% nas regras de negócio, a validar).
- Resultado dos testes de concorrência (N requisições, quantas confirmadas, esperado 1).
- Latência p50, p95 e p99 e taxa de erro nos testes de carga.
- Defeitos por severidade.
- Rastreabilidade: percentual de requisitos obrigatórios com caso de teste aprovado.

## Gestão de defeitos

Registrar para cada defeito: ID, caso de teste de origem, severidade (Crítica, Alta, Média, Baixa), passos para reproduzir, evidência, status e commit da correção.

## Evidências

Guardar em `docs/qualidade/evidencias/` seguindo a convenção `CT-xx-descricao-AAAA-MM-DD.ext` (log, print, relatório). Ver [README das evidências](./evidencias/README.md).
