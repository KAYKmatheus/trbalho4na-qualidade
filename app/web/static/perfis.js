"use strict";

async function iniciarPainel() {
  const painel = document.querySelector("[data-role-page]");
  if (!painel) return;

  const perfilExigido = painel.dataset.rolePage;

  try {
    const usuario = await ensureAuthenticated();

    if (!usuario) return;

    if (usuario.role !== perfilExigido) {
      painel.replaceChildren();

      const titulo = document.createElement("h1");
      titulo.textContent = "Acesso não permitido";

      const mensagem = document.createElement("p");
      mensagem.textContent =
        "Seu perfil não possui permissão para acessar esta página.";

      painel.append(titulo, mensagem);
      return;
    }

    const mensagem = document.createElement("p");
    mensagem.textContent = `Bem-vindo, ${usuario.name}!`;

    painel.insertBefore(mensagem, painel.firstChild);

    if (perfilExigido === "ADMIN") {
      iniciarAdministrador();
      await iniciarVinculoResponsavel();
    }

    if (perfilExigido === "RESPONSAVEL") {
      await carregarPendencias();
    }

  } catch (error) {
    painel.replaceChildren();

    const mensagem = document.createElement("p");
    mensagem.textContent =
      "Não foi possível verificar seu perfil. Tente entrar novamente.";

    painel.append(mensagem);
  }
}

iniciarPainel();


async function carregarPendencias() {
  const lista = document.querySelector("#lista-pendencias");
  const mensagem = document.querySelector("#responsavel-message");

  if (!lista || !mensagem) return;

  lista.replaceChildren();
  mensagem.textContent = "Carregando solicitações...";

  try {
    const pendencias = await apiRequest("/v1/responsavel/pendencias");

    if (pendencias.length === 0) {
      mensagem.textContent = "Nenhuma solicitação pendente.";
      return;
    }

    mensagem.textContent =
      `${pendencias.length} solicitação(ões) aguardando aprovação.`;

    for (const pedido of pendencias) {
      const card = document.createElement("article");
      card.className = "resource-card";

      const titulo = document.createElement("h2");
      titulo.textContent = pedido.resource_name;

      const detalhes = document.createElement("p");

      const inicio = new Date(pedido.start);
      const fim = new Date(pedido.end);

      detalhes.textContent =
        `Tipo: ${pedido.resource_type} | ` +
        `Início: ${inicio.toLocaleString("pt-BR")} | ` +
        `Fim: ${fim.toLocaleString("pt-BR")}`;

      const finalidade = document.createElement("p");
      finalidade.textContent = `Finalidade: ${pedido.reason}`;

      const label = document.createElement("label");
      label.textContent = "Justificativa:";
      const campoId = `justificativa-${pedido.item_id}`;
      label.htmlFor = campoId;

      const justificativa = document.createElement("textarea");
      justificativa.id = campoId;
      justificativa.rows = 2;
      justificativa.required = true;
      justificativa.placeholder = "Informe a justificativa da decisão";

      const acoes = document.createElement("div");
      acoes.style.display = "flex";
      acoes.style.flexWrap = "wrap";
      acoes.style.gap = "0.5rem";

      const aprovar = document.createElement("button");
      aprovar.type = "button";
      aprovar.textContent = "Aprovar";

      const rejeitar = document.createElement("button");
      rejeitar.type = "button";
      rejeitar.textContent = "Rejeitar";

      const retorno = document.createElement("p");
      retorno.setAttribute("role", "status");

      async function decidir(decisao) {
        const textoJustificativa = justificativa.value.trim();

        if (!textoJustificativa) {
          retorno.textContent = "Informe uma justificativa.";
          justificativa.focus();
          return;
        }

        aprovar.disabled = true;
        rejeitar.disabled = true;
        retorno.textContent = "Registrando decisão...";

        try {
          const tipo = pedido.resource_type === "professor"
            ? "VALIDACAO_DOCENTE"
            : "RECURSO_RESTRITO";

          await apiRequest(
            `/v1/reservations/items/${encodeURIComponent(pedido.item_id)}/decision`,
            {
              method: "POST",
              body: JSON.stringify({
                decision_type: tipo,
                decision: decisao,
                justification: textoJustificativa,
              }),
            }
          );

          await carregarPendencias();

        } catch (error) {
          retorno.textContent = userFacingError(error);
          aprovar.disabled = false;
          rejeitar.disabled = false;
        }
      }

      aprovar.addEventListener("click", () => decidir("APROVADA"));
      rejeitar.addEventListener("click", () => decidir("REJEITADA"));

      acoes.append(aprovar, rejeitar);

      card.append(
        titulo,
        detalhes,
        finalidade,
        label,
        justificativa,
        acoes,
        retorno
      );

      lista.append(card);
    }

  } catch (error) {
    mensagem.textContent = userFacingError(error);
  }
}

function iniciarAdministrador() {
  const usuarios = document.querySelector("#cadastro-usuarios");
  const recursos = document.querySelector("#cadastro-recursos");
  const lista = document.querySelector("#lista-recursos");

  if (!usuarios || !recursos || !lista) return;

  usuarios.innerHTML = `
    <form id="form-usuario" class="form-admin">
      <label for="usuario-nome">Nome</label>
      <input id="usuario-nome" name="name" required>

      <label for="usuario-email">E-mail</label>
      <input id="usuario-email" name="email" type="email" required>

      <label for="usuario-senha">Senha</label>
      <input id="usuario-senha" name="password" type="password" required>

      <label for="usuario-perfil">Perfil</label>
      <select id="usuario-perfil" name="role">
        <option value="SOLICITANTE">Solicitante</option>
        <option value="RESPONSAVEL">Responsável</option>
        <option value="ADMIN">Administrador</option>
      </select>

      <button type="submit">Cadastrar usuário</button>
      <p id="usuario-mensagem" role="status"></p>
    </form>
  `;

  recursos.innerHTML = `
    <form id="form-recurso" class="form-admin">
      <label for="recurso-tipo">Tipo de recurso</label>
      <select id="recurso-tipo" name="resource_type">
        <option value="sala">Sala</option>
        <option value="professor">Professor</option>
        <option value="material">Material</option>
      </select>

      <label for="recurso-nome">Nome do recurso</label>
      <input id="recurso-nome" name="name" required>

      <label for="recurso-categoria">Tipo / categoria</label>
      <input id="recurso-categoria" name="category"
             placeholder="Ex.: laboratório, aula, informática">

      <label for="recurso-localizacao">Localização</label>
      <input id="recurso-localizacao" name="location"
             placeholder="Ex.: Bloco A, primeiro andar">

      <label for="recurso-capacidade">Capacidade (salas)</label>
      <input id="recurso-capacidade" name="capacity" type="number" min="1">

      <label for="recurso-quantidade">Quantidade (materiais)</label>
      <input id="recurso-quantidade" name="quantity_total" type="number" min="0">

      <label for="recurso-restrito">Recurso restrito?</label>
      <select id="recurso-restrito" name="restricted">
        <option value="false">Não</option>
        <option value="true">Sim</option>
      </select>

      <button type="submit">Cadastrar recurso</button>
      <p id="recurso-mensagem" role="status"></p>
    </form>
  `;

  const formUsuario = document.querySelector("#form-usuario");
  const formRecurso = document.querySelector("#form-recurso");

  const tipoRecurso = document.querySelector("#recurso-tipo");

  const camposRecurso = [
    {
      id: "recurso-categoria",
      tipos: ["sala", "material"],
    },
    {
      id: "recurso-localizacao",
      tipos: ["sala"],
    },
    {
      id: "recurso-capacidade",
      tipos: ["sala"],
    },
    {
      id: "recurso-quantidade",
      tipos: ["material"],
    },
  ];

  function atualizarCamposRecurso() {
    const tipo = tipoRecurso.value;

    for (const campo of camposRecurso) {
      const input = document.getElementById(campo.id);
      const label = document.querySelector(`label[for="${campo.id}"]`);

      if (!input || !label) continue;

      const visivel = campo.tipos.includes(tipo);

      input.hidden = !visivel;
      label.hidden = !visivel;
      input.disabled = !visivel;
      input.required = visivel;
    }
  }

  tipoRecurso.addEventListener("change", atualizarCamposRecurso);
  atualizarCamposRecurso();

  formUsuario.addEventListener("submit", async (event) => {
    event.preventDefault();

    const mensagem = document.querySelector("#usuario-mensagem");
    const dados = Object.fromEntries(new FormData(formUsuario));

    try {
      await apiRequest("/v1/admin/users", {
        method: "POST",
        body: JSON.stringify(dados),
      });

      mensagem.textContent = "Usuário cadastrado com sucesso!";
      formUsuario.reset();
    } catch (error) {
      mensagem.textContent = userFacingError(error);
    }
  });

  formRecurso.addEventListener("submit", async (event) => {
    event.preventDefault();

    const mensagem = document.querySelector("#recurso-mensagem");
    const dados = Object.fromEntries(new FormData(formRecurso));

    const payload = {
      resource_type: dados.resource_type,
      name: dados.name.trim(),
      restricted: dados.restricted === "true",
      category: dados.category.trim() || null,
      location: dados.location.trim() || null,
    };

    if (dados.resource_type === "sala" && dados.capacity) {
      payload.capacity = Number(dados.capacity);
    }

    if (dados.resource_type === "material" && dados.quantity_total) {
      payload.quantity_total = Number(dados.quantity_total);
    }

    try {
      await apiRequest("/v1/admin/resources", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      mensagem.textContent = "Recurso cadastrado com sucesso!";
      formRecurso.reset();
      atualizarCamposRecurso();
      await carregarRecursosAdmin();
    } catch (error) {
      mensagem.textContent = userFacingError(error);
    }
  });

  async function carregarRecursosAdmin() {
    lista.replaceChildren();

    try {
      const cadastrados = await apiRequest("/v1/admin/resources");

      if (cadastrados.length === 0) {
        lista.textContent = "Nenhum recurso cadastrado.";
        return;
      }

      for (const recurso of cadastrados) {
        const item = document.createElement("p");
        item.textContent =
          `${recurso.resource_type} — ${recurso.name} — ` +
          (recurso.active ? "Ativo" : "Inativo");

        lista.append(item);
      }
    } catch (error) {
      lista.textContent = userFacingError(error);
    }
  }

  carregarRecursosAdmin();
}

async function iniciarVinculoResponsavel() {
  const form = document.querySelector("#form-vinculo");
  if (!form) return;

  const seletorResponsavel = document.querySelector("#vinculo-responsavel");
  const seletorRecurso = document.querySelector("#vinculo-recurso");
  const mensagem = document.querySelector("#vinculo-mensagem");
  const botao = form.querySelector('button[type="submit"]');

  function preencherSelect(seletor, registros, formatar) {
    seletor.replaceChildren();

    for (const registro of registros) {
      const option = document.createElement("option");
      option.value = registro.id;
      option.textContent = formatar(registro);
      seletor.append(option);
    }
  }

  async function carregarOpcoes() {
    mensagem.textContent = "Carregando responsáveis e recursos...";
    botao.disabled = true;

    try {
      const [usuarios, recursos] = await Promise.all([
        apiRequest("/v1/admin/users"),
        apiRequest("/v1/admin/resources"),
      ]);

      const responsaveis = usuarios.filter(
        usuario => usuario.role === "RESPONSAVEL" && usuario.active
      );

      preencherSelect(
        seletorResponsavel,
        responsaveis,
        usuario => `${usuario.name} (${usuario.email})`
      );

      preencherSelect(
        seletorRecurso,
        recursos,
        recurso => `${recurso.resource_type} — ${recurso.name}`
      );

      if (!responsaveis.length || !recursos.length) {
        mensagem.textContent =
          "Cadastre pelo menos um Responsável e um recurso.";
        return;
      }

      botao.disabled = false;
      mensagem.textContent = "";

    } catch (error) {
      mensagem.textContent = userFacingError(error);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    botao.disabled = true;
    mensagem.textContent = "Registrando vínculo...";

    try {
      const responsavelId = seletorResponsavel.value;
      const recursoId = seletorRecurso.value;

      if (!responsavelId || !recursoId) {
        throw new Error("Selecione um Responsável e um recurso.");
      }

      await apiRequest(
        `/v1/admin/responsaveis/${encodeURIComponent(responsavelId)}/recursos`,
        {
          method: "POST",
          body: JSON.stringify({ resource_id: recursoId }),
        }
      );

      mensagem.textContent = "Responsável vinculado com sucesso!";

    } catch (error) {
      mensagem.textContent = userFacingError(error);
    } finally {
      botao.disabled = false;
    }
  });

  await carregarOpcoes();
}
