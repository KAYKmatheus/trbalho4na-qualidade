# Casos de teste

Severidade: A = Alta, M = Média, B = Baixa. Resultado inicial de todos: **Não executado**.

| ID | Requisito | RN / NFR | Cenário | Resultado esperado | Sev. |
|---|---|---|---|---|---|
| CT-01 | FR-01 | NFR-01 | Login com credenciais válidas e inválidas | Válidas geram sessão. Inválidas recebem 401 com mensagem genérica | A |
| CT-02 | FR-01 | NFR-01 | Acessar rota protegida sem token ou com token expirado | 401 e nenhum dado alterado | A |
| CT-03 | FR-01 | NFR-01 | Solicitante chama função administrativa | 403 e nenhum dado alterado | A |
| CT-04 | FR-01, FR-05 | NFR-01 | Solicitante tenta alterar ou cancelar reserva de outro usuário | Operação negada e reserva intacta | A |
| CT-05 | FR-01, FR-08 | RN05 | Usuário tenta aprovar a própria solicitação | Operação negada | A |
| CT-06 | FR-02 | | Administrador cadastra, altera e consulta sala, professor e material | Dados persistidos e auditados | M |
| CT-07 | FR-02 | RN08 | Desativar recurso com reservas históricas | Recurso fica inativo e o histórico permanece | A |
| CT-08 | FR-03 | NFR-04 | Pesquisar por tipo, capacidade, localização, competência e período | Retorna apenas recursos que atendem aos filtros | A |
| CT-09 | FR-03 | RN06 | Pesquisar período com recurso bloqueado ou ocupado | Recurso não aparece como disponível | A |
| CT-10 | FR-04 | RN01 | Criar reserva válida | Reserva registrada com solicitante, intervalo e recurso | A |
| CT-11 | FR-04 | RN01 | Reserva sem recurso, com início maior ou igual ao fim, ou sem finalidade | 422 com erro por campo | A |
| CT-12 | FR-04 | RN01 | Reserva combinando sala, professor e materiais | Todos os itens registrados no mesmo intervalo | M |
| CT-13 | FR-05 | RN02 | Alterar reserva para horário em conflito | 409 e reserva original preservada | A |
| CT-14 | FR-05 | | Cancelar reserva | Status CANCELADA e recurso volta a ficar disponível | A |
| CT-15 | FR-06 | RN02 | Duas reservas ativas da mesma sala em intervalos sobrepostos | Segunda recusada com 409 | A |
| CT-16 | FR-06 | RN03 | Mesmo professor em duas salas diferentes no mesmo horário | Segunda recusada com 409 | A |
| CT-17 | FR-06 | RN02 | Reserva que começa exatamente quando outra termina | Permitida, pois o intervalo é aberto no fim | A |
| CT-18 | FR-06 | RN02 | Material pedido acima da quantidade livre | Recusado, informando o recurso indisponível | A |
| CT-19 | FR-07 | RN04, NFR-03 | N requisições paralelas pela mesma sala e horário | Exatamente 1 confirmada e as demais com 409 | A |
| CT-20 | FR-07 | RN04, NFR-03 | N requisições paralelas por material cujo estoque comporta apenas M | No máximo M unidades confirmadas | A |
| CT-21 | FR-08 | RN05 | Aprovar quando outra reserva ocupou o recurso entre pedido e aprovação | 409 e item não aprovado | A |
| CT-22 | FR-08 | RN05 | Reserva de recurso restrito sem aprovação | Permanece PENDENTE e não ocupa disponibilidade | A |
| CT-23 | FR-08 | RN05 | Decisão sem justificativa ou fora do escopo | 422 ou 403 | A |
| CT-24 | FR-09 | RN06 | Reservar recurso em manutenção | Recusado com 409 | A |
| CT-25 | FR-10 | RN07 | Registrar retirada e devolução | Saldo pendente calculado corretamente | A |
| CT-26 | FR-10 | RN07 | Devolução maior que o retirado | 422 e nenhum registro criado | A |
| CT-27 | FR-10 | RN07 | Material retirado e não devolvido | Pendência sinalizada e unidades indisponíveis para outra reserva | M |
| CT-28 | FR-11 | RN08, NFR-09 | Criar, alterar, cancelar, aprovar e bloquear | Auditoria com usuário, data, ação, valor anterior e novo | A |
| CT-29 | FR-11 | RN08, NFR-09 | Tentar UPDATE e DELETE em auditoria e aprovações | Negado pelo banco | A |
| CT-30 | FR-12 | | Enviar, aprovar, rejeitar e cancelar | Notificação simulada gerada, com justificativa na rejeição | M |
| CT-31 | FR-13 | | Gerar relatório de período | Mostra utilização, carga horária e conflitos evitados | A |
| CT-32 | FR-13 | RN02 | Provocar conflitos e consultar relatório | O contador de conflitos evitados aumenta na mesma quantidade | A |
| CT-33 | FR-14 | NFR-06 | Provocar erro de validação, permissão, conflito e falha | Mensagem compreensível, nunca apresentada como sucesso | M |
| CT-34 | FR-14 | NFR-07, NFR-08 | Executar fluxos principais de 360 a 1920 px e só por teclado | Sem perda de conteúdo e sem rolagem horizontal | M |
| CT-35 | FR-15 | NFR-10 | Comparar a documentação OpenAPI com as rotas reais | Sem divergência | M |
| CT-36 | FR-16 | RN10 | Responsável com escopo valida a alocação de um docente | Decisão VALIDACAO_DOCENTE registrada com justificativa, item passa a APROVADA | A |
| CT-37 | FR-08, FR-16 | RN09 | Responsável sem o recurso em seu escopo tenta aprovar, rejeitar ou validar | 403 e nenhum dado alterado | A |
| CT-38 | FR-11, FR-13 | RN08 | Provocar conflito de sala, de professor, de estoque, bloqueio e perda de disputa | Cada tentativa recusada gera um evento CONFLITO_EVITADO com usuário, recurso, intervalo e motivo | A |
| CT-39 | FR-16 | RN10 | Criar reserva que inclui professor | Item de professor fica PENDENTE e não ocupa a agenda até a validação | A |
| CT-40 | FR-02 | RN09 | Administrador atribui e remove recursos do escopo de um Responsável | Escopo alterado e auditado, e o efeito é imediato nas decisões (CT-37) | M |

## Modelo de registro de execução

| CT | Data | Executor | Resultado | Evidência | Defeito |
|---|---|---|---|---|---|
| | | | | | |
