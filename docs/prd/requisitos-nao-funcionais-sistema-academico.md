# Requisitos não funcionais — Sistema acadêmico de reservas

**Status:** Rascunho para validação
**Base:** [Requisitos funcionais](./requisitos-funcionais-sistema-academico.md) e [personas](./personas-sistema-academico.md)

## Objetivo e convenções

Este documento define qualidades e restrições observáveis para o sistema de reservas. Os requisitos funcionais descrevem o que o sistema faz; estes requisitos descrevem condições de segurança, desempenho, confiabilidade e experiência sob as quais ele deve funcionar.

Como a documentação atual não define arquitetura, volume de uso, ambiente de implantação ou políticas institucionais, metas numéricas identificadas como **proposta** são valores iniciais para discussão, não compromissos já aprovados. Metas institucionais e legais devem ser confirmadas antes de usar este documento como especificação final.

## Requisitos não funcionais

A estrutura deste documento está alinhada aos 8 eixos da ISO/IEC 25010: adequação funcional, desempenho, compatibilidade, usabilidade, confiabilidade, segurança, manutenibilidade e portabilidade. Os números NFR existentes foram preservados; os itens novos adicionados a partir do NFR-11 estão marcados como proposta.

### NFR-01 — Segurança de acesso

O sistema deve proteger as funções e os dados de acordo com o perfil e o escopo do usuário autenticado.

**Verificação**

- Todas as operações que consultam ou alteram dados protegidos verificam autenticação, perfil, titularidade e escopo no servidor, não apenas na interface.
- Requisições sem autenticação ou sem autorização são recusadas e não alteram dados.
- Sessões encerradas ou credenciais inválidas não permitem continuar usando funções protegidas.
- Credenciais e segredos não aparecem em mensagens de erro, logs ou respostas públicas.

**Rastreabilidade:** FR-01, FR-02, FR-05, FR-08, FR-11, FR-13 e FR-16; RN09; Solicitante, Responsável e Administrador.

### NFR-02 — Privacidade e minimização de dados

O sistema deve expor a cada perfil somente os dados pessoais e operacionais necessários às suas funções.

**Verificação**

- O Solicitante só consulta informações de solicitações próprias, exceto dados de recursos que sejam visíveis a usuários autorizados.
- Responsáveis consultam solicitações e históricos apenas dentro do escopo atribuído.
- Relatórios e notificações não revelam dados a usuários sem autorização.
- Os dados pessoais coletados, a finalidade de uso e o prazo de retenção são documentados conforme a política institucional aplicável.

**Ponto de validação:** identificar quais dados pessoais são necessários e quais prazos e obrigações legais de retenção se aplicam.

**Rastreabilidade:** FR-01, FR-04, FR-11, FR-12 e FR-13; especialmente as limitações de acesso das três personas.

### NFR-03 — Integridade e concorrência de reservas

O sistema deve preservar a consistência de reservas e quantidades de materiais mesmo quando houver operações simultâneas.

**Verificação**

- Testes concorrentes de criação, alteração e aprovação confirmam que um recurso (sala, professor ou material) não é alocado em reservas ativas com intervalos sobrepostos, incluindo conflitos na agenda do professor entre salas diferentes.
- Em uma disputa simultânea pelo mesmo recurso em intervalos sobrepostos, no máximo uma operação é confirmada; disputas por materiais também respeitam a quantidade disponível e as demais operações recebem resultado claro de conflito.
- Falha durante uma alteração ou confirmação não deixa reserva parcialmente atualizada nem consome disponibilidade sem registro correspondente.
- A disponibilidade é validada novamente na operação que confirma ou aprova a alocação.

**Rastreabilidade:** RN01 a RN07; FR-03 a FR-10.

**Observação:** a RN08 (auditoria) não é verificada neste requisito, e sim no NFR-09. Este requisito trata de integridade e concorrência (RN01 a RN07).

### NFR-04 — Desempenho

As operações frequentes devem responder em tempo adequado para que Solicitantes consultem disponibilidade e Responsáveis analisem pedidos sem atrasos indevidos.

**Metas iniciais propostas — validar com a instituição**

- Pesquisa de recursos e disponibilidade: percentil 95 (p95) em até **2 segundos**.
- Operações de leitura e gravação, incluindo criação e decisão de solicitação: p95 em até **3 segundos**, excluindo o tempo de interação humana.
- Metas medidas em ambiente representativo da implantação, com dados e carga de teste documentados; erros e timeouts devem ser contabilizados, não excluídos da medição.
- Carga inicial sugerida para o teste: **100 usuários simultâneos**. Confirmar ou substituir esse volume conforme o número esperado de usuários.

**Rastreabilidade:** FR-03 a FR-08, FR-12 e FR-13; Solicitante e Responsável.

### NFR-05 — Confiabilidade e recuperação

O sistema deve permanecer acessível durante os períodos de uso institucional e permitir a recuperação dos dados após falhas.

**Metas iniciais propostas — validar com a instituição**

- Disponibilidade mensal sugerida: **99,5%** durante o período de operação acordado, excluindo janelas de manutenção previamente comunicadas.
- Ponto de recuperação sugerido (RPO): no máximo **24 horas** de dados.
- Tempo de recuperação sugerido (RTO): até **8 horas** após uma falha que exija restauração.
- Backups devem incluir os dados necessários para recuperar cadastros, solicitações, reservas, auditoria e movimentações de materiais; restaurações devem ser testadas periodicamente.

**Pontos de validação:** período de operação, disponibilidade esperada, frequência de backup e objetivos de recuperação dependem do ambiente e da política institucional.

**Rastreabilidade:** RN01 a RN10; FR-01 a FR-16; Solicitante, Responsável e Administrador.

### NFR-06 — Usabilidade e compreensão

Os fluxos principais devem permitir que cada persona execute suas tarefas com orientações claras, sem depender de contato manual para entender o estado de uma operação.

**Verificação**

- Formulários indicam campos obrigatórios e apresentam erros junto ao campo correspondente ou em resumo acessível.
- Mensagens identificam se a operação foi concluída, recusada por conflito, negada por permissão ou falhou por outro motivo; nunca mostram sucesso quando a alteração não foi persistida.
- Status e justificativas de rejeição são apresentados em linguagem direta e consistente.
- Em avaliação de usabilidade, participantes representativos das três personas conseguem concluir os fluxos de pesquisa e solicitação, análise e decisão, e manutenção de cadastro sem instruções externas para interpretar estados e erros.

**Rastreabilidade:** FR-03 a FR-05, FR-08, FR-10, FR-12 e FR-14; experiências esperadas das três personas.

### NFR-07 — Acessibilidade e responsividade

As telas devem ser utilizáveis em dispositivos móveis e desktop e atender a práticas de acessibilidade.

**Meta proposta — validar:** conformidade WCAG **2.2 nível AA** nos fluxos principais.

**Verificação**

- Fluxos de pesquisa, solicitação, decisão e administração funcionam em larguras de tela de **360 px a 1920 px**, sem perda de conteúdo ou rolagem horizontal para realizar ações essenciais.
- As ações podem ser operadas por teclado, com foco visível e ordem de navegação coerente.
- Campos, botões, estados e mensagens têm nomes ou rótulos programaticamente identificáveis e contraste suficiente segundo o nível de conformidade adotado.
- A interface não depende exclusivamente de cor, gesto ou elemento visual para comunicar estado ou erro.

**Rastreabilidade:** FR-03 a FR-05, FR-08, FR-10, FR-14 e FR-15; todas as personas.

### NFR-08 — Compatibilidade

Os fluxos públicos devem funcionar nos ambientes de navegador e dispositivo oficialmente suportados pela instituição.

**Proposta inicial:** suportar versões estáveis atuais e imediatamente anteriores dos navegadores Chrome, Edge, Firefox e Safari, além dos navegadores móveis padrão em Android e iOS.

**Verificação**

- Os fluxos essenciais são testados nos navegadores e dispositivos da matriz de suporte aprovada.
- Nenhum fluxo crítico depende de comportamento exclusivo de um único navegador sem alternativa documentada.

**Ponto de validação:** aprovar a matriz de navegadores e dispositivos considerando o parque tecnológico institucional.

**Rastreabilidade:** FR-14 e FR-15; Solicitante, Responsável e Administrador.

### NFR-09 — Auditabilidade e preservação do histórico

O histórico deve ser confiável, legível por perfis autorizados e resistente a alterações não autorizadas.

**Verificação**

- Cada evento registra, no mínimo, usuário ou origem da ação, ação realizada, registro afetado e data/hora.
- Criação, alteração, cancelamento, aprovação e bloqueio registram quem realizou a ação, quando ocorreu, o que foi alterado e os valores anterior e novo.
- Os registros são imutáveis e protegidos contra alteração ou exclusão, inclusive por operações administrativas rotineiras.
- As datas e horas são armazenadas e exibidas de forma consistente, incluindo fuso horário aplicável.
- A política institucional define prazo de retenção e acesso, preservando a imutabilidade do histórico e as obrigações de privacidade aplicáveis.

**Rastreabilidade:** RN08; FR-02, FR-05, FR-08 a FR-12 e FR-13; principalmente Responsável e Administrador.

### NFR-10 — Manutenibilidade e consistência documental

As mudanças devem preservar as regras de negócio e manter documentação suficiente para usuários e responsáveis pela evolução do sistema.

**Verificação**

- Alterações em autenticação, disponibilidade, aprovações, conflitos ou movimentações de materiais incluem testes para os respectivos critérios de aceite e regras RN01 a RN10.
- Mudanças em operações ou fluxos públicos atualizam a documentação correspondente.
- Os termos usados na interface, nos registros e na documentação são consistentes com o glossário institucional aprovado.

**Rastreabilidade:** RN01 a RN10; FR-01, FR-02, FR-04, FR-05, FR-06, FR-08, FR-11, FR-12, FR-13, FR-15 e FR-16; Solicitante, Responsável e Administrador.

### NFR-11 — Adequação funcional (proposta)

O sistema deve cobrir adequadamente os objetivos de negócio e responder às regras de reserva, aprovação, manutenção, auditoria e relatório previstos no escopo institucional.

**Verificação**

- Cada requisito funcional principal tem um correspondente em comportamento, validação ou resposta observável no produto.
- Os fluxos de autenticação, pesquisa, criação, aprovação, bloqueio, relatório e auditoria cobrem as ações esperadas pelas personas e pelos critérios de aceite.
- Regras de negócio RN01 a RN10 são observáveis em mensagens, estados, registros e restrições do sistema, sem depender de convenções informais.
- O produto não exige comportamento implícito para executar operações críticas e documentadas.

**Rastreabilidade:** RN01 a RN10; FR-01 a FR-16; Solicitante, Responsável e Administrador.

### NFR-12 — Portabilidade e implantação (proposta)

O sistema deve ser implantável e operar de forma consistente em ambientes e plataformas suportados pela instituição, sem dependências exclusivas de um ambiente específico.

**Verificação**

- O sistema pode ser executado em ambientes de homologação e produção com configuração documentada e sem ajustes manuais de código.
- A implantação considera compatibilidade com a stack de banco, servidor, sistema operacional e navegador suportados pela instituição.
- Configurações específicas de ambiente são descritas, versionadas e separadas do código de negócio.
- O comportamento principal não depende de um único host, caminho local ou variável de ambiente não documentada.

**Rastreabilidade:** RN01 a RN10; FR-01 a FR-16; Solicitante, Responsável e Administrador.

## Matriz FR × NFR

| FR | NFRs relacionadas |
|---|---|
| FR-01 | NFR-01, NFR-05, NFR-10, NFR-11 |
| FR-02 | NFR-01, NFR-02, NFR-05, NFR-10, NFR-11 |
| FR-03 | NFR-04, NFR-06, NFR-07, NFR-11 |
| FR-04 | NFR-03, NFR-04, NFR-06, NFR-11 |
| FR-05 | NFR-01, NFR-03, NFR-05, NFR-06, NFR-10, NFR-11 |
| FR-06 | NFR-03, NFR-04, NFR-06, NFR-11 |
| FR-07 | NFR-03, NFR-04, NFR-11 |
| FR-08 | NFR-01, NFR-06, NFR-08, NFR-10, NFR-11 |
| FR-09 | NFR-03, NFR-05, NFR-06, NFR-11 |
| FR-10 | NFR-03, NFR-05, NFR-06, NFR-11 |
| FR-11 | NFR-01, NFR-02, NFR-05, NFR-09, NFR-10, NFR-11 |
| FR-12 | NFR-01, NFR-02, NFR-06, NFR-10, NFR-11 |
| FR-13 | NFR-01, NFR-02, NFR-04, NFR-10, NFR-11 |
| FR-14 | NFR-06, NFR-07, NFR-08, NFR-11 |
| FR-15 | NFR-07, NFR-08, NFR-10, NFR-12 |
| FR-16 | NFR-01, NFR-03, NFR-06, NFR-10, NFR-11 |

## Decisões necessárias para fechar as metas

1. Quantos usuários simultâneos e quantos recursos/registros são esperados?
2. Qual é o horário institucional de operação e a disponibilidade mensal exigida?
3. Quais são os objetivos aceitáveis de perda de dados (RPO) e tempo de recuperação (RTO)?
4. Quais dispositivos e navegadores precisam ser suportados?
5. Quais políticas legais e institucionais definem dados pessoais, retenção e acesso ao histórico?
6. A instituição confirma WCAG 2.2 AA como meta de acessibilidade?

## Observação sobre os requisitos funcionais

Os requisitos funcionais atuais formam uma boa base para as três personas: cobrem acesso por perfil, consulta e solicitação de recursos, decisão responsável, prevenção de conflitos, administração e rastreabilidade. Antes de tratá-los como especificação final, ainda convém definir quais recursos são restritos e o escopo dos Responsáveis, conforme os pontos de validação do documento funcional. Este documento não substitui essas decisões.
