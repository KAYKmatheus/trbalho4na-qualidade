# Roteiro de apresentação — AlocaSenac

**Duração planejada:** 12 minutos. Os nomes ficam em branco para o grupo
preencher. O estado atual das execuções está no
[relatório final](./relatorio-final.md) e no
[README de evidências](./qualidade/evidencias/README.md).

## Agenda

| Tempo | O que falar | O que mostrar na tela | Quem fala |
|---|---|---|---|
| 0:00–1:00 | Problema abordado: alocar salas, professores e materiais sem sobreposição e com autorização por perfil. | README, objetivo do PRD e personas. | ____________________ |
| 1:00–3:00 | Mostrar as fronteiras entre interface, API e banco, e explicar que as notificações são simuladas. | [Diagrama de contexto](./prd/diagrama-contexto.md), `app/main.py` e `app/api/v1.py`. | ____________________ |
| 3:00–5:00 | Percorrer login, busca, criação e minhas reservas; distinguir a resposta da API da interface. | `http://localhost:8000/app/index.html` e rotas `/app/buscar.html`, `/app/reservar.html`, `/app/minhas.html`. | ____________________ |
| 5:00–8:00 | Demonstrar a disputa de duas solicitações pelo mesmo recurso e explicar os resultados HTTP. | Dois terminais PowerShell executando o mesmo `POST /v1/reservations`; em seguida, o teste CT-19. | ____________________ |
| 8:00–10:00 | Explicar a pirâmide de testes, o workflow e quais resultados têm evidência. | Testes de domínio, feature Gherkin, E2E, workflow e arquivos em `docs/qualidade/evidencias/`. | ____________________ |
| 10:00–12:00 | Apresentar limitações, estado `CONFIRMADA`, lições e responder perguntas. | ADR-06, RTM, relatório final e pendências documentadas. | ____________________ |

## Preparação da demonstração concorrente

Use uma instância PostgreSQL descartável, a aplicação iniciada e contas
Solicitante e Administrador previamente provisionadas. Não use credenciais
reais da instituição. Os valores de autenticação devem ser fornecidos pelo
grupo no ambiente de cada terminal, sem gravá-los em arquivos ou no Git.

No terminal de preparação, defina a URL local e faça login como Administrador:

```powershell
$env:BASE_URL = "http://127.0.0.1:8000"
$adminBody = @{ email = $env:ADMIN_EMAIL; password = $env:ADMIN_PASSWORD } | ConvertTo-Json -Compress
$adminLogin = curl.exe -sS -X POST "$env:BASE_URL/v1/auth/login" -H "Content-Type: application/json" --data-raw $adminBody | ConvertFrom-Json
$env:ADMIN_TOKEN = $adminLogin.access_token
```

Crie uma sala de demonstração pela rota administrativa:

```powershell
$resourceBody = @{
  resource_type = "sala"
  name = "Sala demonstracao CT-19"
  category = "aula"
  capacity = 24
  location = "Bloco de demonstracao"
} | ConvertTo-Json -Compress
$resource = curl.exe -sS -X POST "$env:BASE_URL/v1/admin/resources" -H "Authorization: Bearer $env:ADMIN_TOKEN" -H "Content-Type: application/json" --data-raw $resourceBody | ConvertFrom-Json
$env:RESOURCE_ID = $resource.id
```

Faça login como Solicitante e obtenha o identificador autenticado:

```powershell
$requesterBody = @{ email = $env:SOLICITANTE_EMAIL; password = $env:SOLICITANTE_PASSWORD } | ConvertTo-Json -Compress
$requesterLogin = curl.exe -sS -X POST "$env:BASE_URL/v1/auth/login" -H "Content-Type: application/json" --data-raw $requesterBody | ConvertFrom-Json
$env:SOLICITANTE_TOKEN = $requesterLogin.access_token
$me = curl.exe -sS "$env:BASE_URL/v1/auth/me" -H "Authorization: Bearer $env:SOLICITANTE_TOKEN" | ConvertFrom-Json
$env:SOLICITANTE_ID = $me.id
```

Escolha um intervalo futuro, informe os mesmos valores nos dois terminais e
copie para ambos o token do Solicitante, o identificador dele e o ID da sala:

```powershell
$slot = [DateTime]::UtcNow.Date.AddDays(2).AddHours(10)
$env:RESERVATION_START = $slot.ToString("yyyy-MM-ddTHH:mm:ssZ")
$env:RESERVATION_END = $slot.AddHours(1).ToString("yyyy-MM-ddTHH:mm:ssZ")
$env:RESERVATION_START
$env:RESERVATION_END
```

## Disputa ao vivo em dois terminais

Em **cada** terminal PowerShell, defina os mesmos valores `BASE_URL`,
`SOLICITANTE_TOKEN`, `SOLICITANTE_ID`, `RESOURCE_ID`,
`RESERVATION_START` e `RESERVATION_END`. Execute o comando abaixo nos dois
terminais ao mesmo sinal. Ambos enviam `POST /v1/reservations` com a mesma
sala e intervalo:

```powershell
$body = @{
  solicitante_id = $env:SOLICITANTE_ID
  reason = "Demonstracao concorrencia CT-19"
  items = @(@{
    resource_type = "sala"
    resource_id = $env:RESOURCE_ID
    start = $env:RESERVATION_START
    end = $env:RESERVATION_END
    quantity = 1
  })
} | ConvertTo-Json -Depth 5 -Compress

curl.exe -sS --write-out "`nHTTP %{http_code}`n" -X POST "$env:BASE_URL/v1/reservations" `
  -H "Authorization: Bearer $env:SOLICITANTE_TOKEN" `
  -H "Content-Type: application/json" `
  --data-raw $body
```

**Resultado esperado da demonstração:** uma resposta `201` e uma resposta
`409`. O resultado é esperado pelo contrato, não uma execução já comprovada;
se a demonstração não for executada, não o apresente como resultado observado.
O endpoint e o corpo correspondem a `app/api/v1.py` e
`ReservationCreate` em `app/api/schemas.py`.

## CT-19 com dez threads

O cenário pytest configurado para CT-19 usa `THREAD_COUNT = 10` em
[test_cenarios_executaveis.py](../tests/bdd/test_cenarios_executaveis.py). Com
PostgreSQL de teste acessível, execute:

```powershell
py -m pytest -o addopts="" -m "integration and concorrencia" "tests/bdd/test_cenarios_executaveis.py::test_processar_requisições_simultâneas_pela_mesma_sala" -v
```

O resultado esperado do cenário é uma reserva criada e as concorrentes
recusadas com `409`. A evidência PostgreSQL está pendente; consulte
[docs/qualidade/evidencias/README.md](./qualidade/evidencias/README.md). O
grupo deve guardar a saída real antes de afirmar que CT-19 passou.

## Plano B se o banco não subir

1. Abra
   [validacao-limpeza-2026-11-11.txt](./qualidade/evidencias/validacao-limpeza-2026-11-11.txt)
   e mostre somente o resultado local que essa saída registra.
2. Mostre o
   [README de evidências](./qualidade/evidencias/README.md), que registra a
   pendência de PostgreSQL, e o teste de concorrência no código.
3. Explique que a saída local não comprova CT-19 nem uma disputa real em
   PostgreSQL. Não simule uma resposta `409` nem declare a concorrência
   validada sem execução salva.

## Perguntas prováveis

1. **Como o banco impede duas reservas da mesma sala no mesmo horário?**  
   `reservation_items_no_overlap` usa `EXCLUDE USING gist` com `btree_gist`
   para intervalos `[)` em recursos não materiais. A definição está em
   [002_exclusao_sobreposicao.sql](../migrations/002_exclusao_sobreposicao.sql).

2. **Por que materiais não usam essa mesma exclusão?**  
   Porque podem ter reservas simultâneas até o limite do estoque. O serviço
   bloqueia a linha de `resources` com `FOR UPDATE` e valida a soma em
   [reservas.py](../app/servicos/reservas.py).

3. **O que acontece se duas requisições chegam juntas?**  
   A constraint PostgreSQL protege sala e professor; para material, o bloqueio
   de linha serializa a verificação de quantidade. O teste de integração CT-19
   está pendente de execução conforme o
   [registro](./qualidade/evidencias/README.md).

4. **Como o sistema mantém a trilha de auditoria imutável?**  
   A migração cria triggers que recusam `UPDATE` e `DELETE` em
   `audit_entries`, `approvals` e `material_movements`; consulte
   [003_auditoria_imutavel.sql](../migrations/003_auditoria_imutavel.sql).

5. **Como se limita o que um Responsável pode decidir?**  
   `require_roles` protege as rotas e `ApprovalService` verifica o recurso
   contra `resource_scopes`; as decisões ficam registradas em `approvals`.

6. **Por que há o estado `CONFIRMADA`?**  
   O grupo decidiu mantê-lo como estado distinto; a decisão e a relação com
   `PENDENTE` estão no [ADR-06](./prd/adr-06-estados-da-reserva.md).

7. **O sistema envia e-mail de verdade?**  
   Não. `NotificationService` grava notificações simuladas em `notifications`;
   o PRD deixa provedor externo fora do escopo atual.

8. **Qual a diferença entre teste E2E e teste de integração PostgreSQL?**  
   O E2E exercita fluxos pela API HTTP com `TestClient`; o teste de integração
   precisa do PostgreSQL para validar constraints e concorrência reais. A
   execução PostgreSQL segue pendente no
   [registro de evidências](./qualidade/evidencias/README.md).
