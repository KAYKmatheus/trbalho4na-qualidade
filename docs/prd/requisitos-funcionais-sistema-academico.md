# Requisitos funcionais — Sistema acadêmico de reservas

**Status:** Rascunho para validação
**Fonte:** Requisitos informados pelo solicitante e personas em [personas-sistema-academico.md](./personas-sistema-academico.md)

## Objetivo

Permitir que usuários consultem e solicitem recursos acadêmicos, que responsáveis avaliem solicitações sob sua alçada e que administradores mantenham os cadastros, com disponibilidade e histórico confiáveis.

## Regras de negócio formais

- **RN01 — Reserva válida:** toda reserva deve ter um solicitante, um intervalo com início e fim e ao menos um recurso.
- **RN02 — Sem sobreposição de recurso:** um mesmo recurso (sala, professor ou material) não pode ter duas reservas ativas com intervalos sobrepostos.
- **RN03 — Agenda do professor:** a sobreposição deve ser verificada também na agenda do docente, mesmo quando as reservas envolvem salas diferentes.
- **RN04 — Dupla reserva simultânea:** em solicitações concorrentes para o mesmo recurso e horário, somente uma pode ser confirmada; a outra deve receber uma mensagem clara de conflito.
- **RN05 — Recurso restrito:** recursos marcados como restritos só podem ser alocados após aprovação do Responsável autorizado.
- **RN06 — Manutenção e bloqueio:** um recurso bloqueado ou em manutenção não pode ser reservado durante o período do bloqueio.
- **RN07 — Material controlado:** materiais reservados exigem registro de retirada e devolução; devoluções pendentes devem ser sinalizadas.
- **RN08 — Auditoria:** toda criação, alteração, cancelamento, aprovação e bloqueio deve gerar registro histórico imutável, identificando quem realizou a ação, quando, o que foi alterado e os valores anterior e novo. Tentativas recusadas por conflito também geram registro (conflito evitado).
- **RN09 — Escopo do Responsável:** o Responsável só pode aprovar, rejeitar ou validar itens cujo recurso esteja no escopo atribuído a ele pelo Administrador.
- **RN10 — Validação de docente:** todo item de reserva que aloca um professor depende da validação de um Responsável com escopo sobre esse professor antes de ser confirmado.

## Perfis e escopo

- **Solicitante:** professor ou coordenador que pesquisa recursos, cria, altera e cancela as próprias reservas e acompanha o próprio andamento. Não administra cadastros nem aprova as próprias solicitações.
- **Responsável:** analisa solicitações dentro do escopo atribuído, verifica disponibilidade, aprova ou rejeita com justificativa e acompanha reservas e materiais sob sua responsabilidade.
- **Administrador:** gerencia usuários, perfis e cadastros de salas, professores e materiais, além de consultar solicitações, reservas, pendências, utilização e histórico.

O perfil de acesso do usuário autenticado é distinto do cadastro de professor que pode ser consultado ou alocado como recurso.

## Requisitos funcionais obrigatórios

### FR-01 — Autenticar usuários e autorizar ações por perfil

O sistema deve autenticar usuários e permitir ou negar cada ação conforme os perfis de Solicitante, Responsável e Administrador e o escopo de responsabilidade atribuído.

**Critérios de aceite**

- Uma pessoa não autenticada não acessa funcionalidades que exigem autenticação.
- O Solicitante não acessa funções administrativas, não altera solicitações de terceiros e não aprova a própria solicitação.
- O Responsável só decide solicitações dentro do próprio escopo e não concede permissões administrativas a si mesmo.
- O escopo de decisão do Responsável é definido pelos recursos atribuídos a ele (RN09), e uma decisão fora desse escopo é recusada.
- O Administrador gerencia usuários e perfis sem apagar silenciosamente o histórico de decisões ou utilização.

### FR-02 — Cadastrar, consultar e manter recursos

O sistema deve permitir ao Administrador cadastrar e manter salas, professores e materiais, e disponibilizar a consulta desses recursos aos perfis autorizados.

**Critérios de aceite**

- Os cadastros permitem informar os dados necessários à pesquisa: tipo, capacidade e localização de salas, competências de professores, e tipo e quantidade de materiais. A disponibilidade de salas, professores e materiais é calculada a partir das reservas ativas, dos bloqueios e da situação ativa do recurso, sem janelas de horário cadastradas.
- Alterações administrativas relevantes são rastreáveis.
- O Administrador atribui e remove recursos do escopo de cada Responsável, e essas alterações são auditadas (RN09).
- A retirada de um recurso de uso não pode eliminar referências necessárias ao histórico de reservas e utilizações.

### FR-03 — Pesquisar recursos e disponibilidade

O sistema deve permitir pesquisar recursos por tipo, capacidade, localização, competência e disponibilidade, considerando o período informado e as regras de cada tipo de recurso.

**Critérios de aceite**

- A pesquisa pode ser feita antes de criar uma solicitação.
- Os resultados não apresentam como disponíveis recursos bloqueados por manutenção ou sem disponibilidade no período pesquisado.
- A pesquisa de materiais considera a quantidade disponível; a de professores considera a competência cadastrada e a agenda.

### FR-04 — Criar solicitações de reserva

O sistema deve permitir que o Solicitante crie uma reserva com ao menos um recurso, intervalo de início e fim e finalidade. Uma reserva pode combinar sala, professor e materiais no mesmo intervalo; a solicitação de materiais deve informar quantidade.

**Critérios de aceite**

- Toda reserva registra seu Solicitante, intervalo e ao menos um recurso, e o sistema valida esses dados antes do envio.
- O Solicitante pode combinar sala, professor e materiais em uma mesma reserva e intervalo.
- O sistema informa campos inválidos de forma compreensível.
- O Solicitante pode consultar o status da própria solicitação e, em caso de rejeição, o motivo registrado.
- Reservas que incluem apenas salas e materiais não restritos podem seguir sem aprovação. Reservas com recurso restrito seguem o FR-08, e itens de professor seguem o FR-16.

### FR-05 — Alterar e cancelar solicitações ou reservas

O sistema deve permitir ao Solicitante alterar e cancelar as próprias reservas e impedir que altere ou cancele reservas de terceiros.

**Critérios de aceite**

- O Solicitante pode alterar ou cancelar suas próprias reservas, mas não reservas de terceiros.
- Usuários sem autorização não conseguem alterar ou cancelar solicitações de terceiros.
- Uma alteração volta a validar disponibilidade, sobreposições e bloqueios antes de ser efetivada.
- O cancelamento atualiza a disponibilidade do recurso e preserva o registro da solicitação e da ação realizada.

### FR-06 — Detectar conflitos de disponibilidade

O sistema deve detectar sobreposição de horários em reservas ativas para qualquer recurso alocado — sala, professor ou material — e indisponibilidade de quantidade suficiente de materiais.

**Critérios de aceite**

- A validação ocorre ao criar, alterar e aprovar uma solicitação, incluindo a agenda do professor mesmo quando as salas são diferentes.
- O mesmo recurso não pode constar em duas reservas ativas com intervalos sobrepostos.
- O sistema não confirma uma alocação que conflite com outra reserva ativa, bloqueio, manutenção ou disponibilidade do recurso.
- Para materiais, a validação considera unidades reservadas, em manutenção ou ainda não devolvidas.
- Quando detectar conflito, o sistema informa que a operação não pode ser concluída e, quando possível, indica o recurso indisponível.

### FR-07 — Impedir dupla reserva em solicitações simultâneas

O sistema deve proteger a confirmação de reservas concorrentes para que solicitações simultâneas não ultrapassem a disponibilidade do recurso.

**Critérios de aceite**

- Se duas ou mais operações concorrentes disputarem o mesmo recurso em intervalos sobrepostos, no máximo uma pode ser confirmada. Para materiais, a validação de quantidade disponível também deve impedir confirmação acima do estoque disponível.
- A validação final de disponibilidade acontece no momento de confirmar ou aprovar, não apenas durante a pesquisa ou o preenchimento do pedido.
- Uma operação que perder a disputa recebe uma mensagem clara de conflito e não é apresentada como confirmada.

### FR-08 — Exigir aprovação para recursos restritos

O sistema deve exigir aprovação para todo recurso marcado como restrito e encaminhar a decisão a um Responsável autorizado para aquele escopo.

**Critérios de aceite**

- Uma solicitação de recurso restrito não é confirmada sem aprovação.
- O Responsável pode aprovar ou rejeitar solicitações autorizadas; toda decisão deve ter justificativa registrada.
- Somente um Responsável com o recurso no escopo atribuído pode decidir a solicitação (RN09).
- O Solicitante recebe o resultado e pode consultar o motivo da rejeição.
- Antes da aprovação, o sistema verifica novamente a disponibilidade; entre solicitações concorrentes, somente as compatíveis com a disponibilidade podem ser aprovadas.
- O solicitante não pode aprovar a própria solicitação.

## Outros requisitos funcionais

### FR-09 — Bloquear recursos em manutenção

O sistema deve permitir registrar manutenção para um recurso e impedir sua alocação durante o período informado.

**Critérios de aceite**

- Uma pesquisa ou tentativa de reserva que coincida com a manutenção não apresenta o recurso como disponível nem permite confirmá-lo.
- O bloqueio e sua alteração ficam disponíveis para consulta por perfis autorizados.

### FR-10 — Registrar retirada e devolução de materiais e equipamentos

O sistema deve exigir e registrar a retirada e a devolução de materiais ou equipamentos associados à reserva e sinalizar devoluções pendentes.

**Critérios de aceite**

- O Responsável autorizado registra a retirada e a devolução, incluindo o material e a quantidade correspondente.
- Unidades retiradas e ainda não devolvidas não são consideradas disponíveis para outra alocação.
- A situação da retirada e da devolução pode ser consultada por perfis autorizados; devoluções pendentes são sinalizadas.

### FR-11 — Manter histórico auditável

O sistema deve manter histórico imutável e consultável das alterações relevantes em cadastros, solicitações, decisões, reservas, bloqueios, manutenções e movimentações de materiais.

**Critérios de aceite**

- Criação, alteração, cancelamento, aprovação e bloqueio registram a ação, o registro afetado, quem a realizou, quando ocorreu e os valores anterior e novo.
- Tentativas recusadas por sobreposição, bloqueio, estoque insuficiente ou perda de disputa simultânea geram um evento de conflito evitado, com o usuário, o recurso disputado, o intervalo pedido e o motivo.
- Os registros são imutáveis e não podem ser alterados ou excluídos, inclusive por ações administrativas rotineiras.
- O acesso ao histórico respeita os perfis e escopos de autorização.

### FR-12 — Notificar mudanças de estado

O sistema deve gerar notificações simuladas quando uma solicitação for enviada, aprovada, rejeitada ou cancelada.

**Critérios de aceite**

- A notificação indica a solicitação e o novo estado; rejeições incluem a justificativa registrada.
- O sistema registra que a notificação simulada foi gerada, sem depender de serviço externo.
- Integração com API externa fica fora do escopo inicial e poderá substituir ou complementar a simulação em etapa futura.

### FR-13 — Apresentar relatórios de utilização

O sistema deve disponibilizar relatórios com utilização por recurso, carga horária alocada e conflitos evitados.

**Critérios de aceite**

- Os relatórios distinguem os recursos e apresentam os três indicadores solicitados.
- Conflitos evitados correspondem aos eventos de conflito evitado registrados no histórico (FR-11) no período consultado.
- A consulta dos relatórios respeita o perfil e o escopo de autorização.

### FR-14 — Oferecer interface responsiva e mensagens compreensíveis

O sistema deve oferecer interface utilizável em diferentes tamanhos de tela e mensagens claras para erros e resultados das operações.

**Critérios de aceite**

- A interface se adapta a telas móveis e desktop sem ocultar as ações essenciais.
- Mensagens explicam o que ocorreu e, quando aplicável, como corrigir ou tentar novamente.
- Erros de validação, falta de permissão, conflito, indisponibilidade e falha de operação não são apresentados como sucesso.

### FR-15 — Documentar API ou fluxos públicos

O sistema deve manter documentação da API ou, se não houver API pública, dos fluxos públicos disponíveis aos usuários.

**Critérios de aceite**

- A documentação descreve as operações ou fluxos disponíveis, seus dados necessários e os resultados e erros esperados.
- A documentação acompanha as mudanças nas operações ou fluxos documentados.

### FR-16 — Validar a alocação de docentes

O sistema deve exigir que um Responsável com escopo sobre o professor valide a alocação de docentes antes de confirmar o item correspondente da reserva.

**Critérios de aceite**

- Um item que aloca professor é criado como pendente, não confirma a reserva e não ocupa a agenda do professor até a validação (RN10).
- Antes da decisão, o Responsável consulta a competência cadastrada, a agenda do professor e a finalidade da reserva, e o sistema revalida a disponibilidade (RN03, RN04).
- A decisão (validar ou rejeitar) exige justificativa registrada e fica no histórico, com tipo de decisão de validação de docente.
- O Solicitante é notificado do resultado e consulta o motivo da rejeição.
- Somente um Responsável com o professor no escopo atribuído valida a alocação (RN09), e o Solicitante não valida a própria reserva.

## Premissas confirmadas

- O Responsável do escopo aprova solicitações de recursos marcados como restritos; o solicitante não pode aprovar o próprio pedido.
- Uma solicitação pendente ainda não confirma a reserva. A disponibilidade é verificada novamente durante a aprovação, e solicitações concorrentes não podem resultar em alocação acima da disponibilidade.
- As regras RN01 a RN10 definem os dados mínimos da reserva, a prevenção de sobreposições, o tratamento de recursos restritos e bloqueados, o controle de materiais e os eventos auditáveis.
- Solicitações de materiais informam quantidade; disponibilidade considera unidades cadastradas, reservadas, em manutenção ou ainda não devolvidas.
- O Administrador define o escopo dos Responsáveis atribuindo recursos a cada um (RN09).
- A disponibilidade de salas, professores e materiais é calculada por agenda, bloqueios e situação ativa, sem tabela de janelas de horário.
- Itens de professor dependem de validação do Responsável (RN10, FR-16).
- O escopo inicial usa notificações simuladas para envio, aprovação, rejeição e cancelamento. Integração externa fica como alternativa futura.

## Pontos para validação institucional

1. Definir quais recursos são restritos.
2. Definir os dados cadastrais e a terminologia institucional para competências de professores.
3. Definir os formatos, filtros e permissões detalhadas dos relatórios.
4. Confirmar se a documentação pública será de uma API, dos fluxos de interface ou de ambos.
