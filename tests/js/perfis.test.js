const assert = require("node:assert/strict");
const path = require("node:path");
const { test } = require("node:test");

const script = path.resolve(__dirname, "../../app/web/static/perfis.js");

class Element {
  constructor() {
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.style = {};
    this.value = "";
    this.textContent = "";
    this.disabled = false;
    this.hidden = false;
    this.required = false;
    this.firstChild = null;
  }

  addEventListener(event, callback) {
    this.listeners[event] = callback;
  }

  append(...items) {
    this.children.push(...items);
    this.firstChild = this.children[0] || null;
  }

  insertBefore(item) {
    this.children.unshift(item);
    this.firstChild = item;
  }

  replaceChildren(...items) {
    this.children = items;
    this.firstChild = items[0] || null;
  }

  setAttribute(name, value) {
    this[name] = value;
  }

  focus() {
    this.focused = true;
  }

  reset() {
    this.resetCalled = true;
  }

  querySelector() {
    if (!this.submitButton) this.submitButton = new Element();
    return this.submitButton;
  }
}

function createPage(role, user, handler = async () => []) {
  const elements = new Map();
  const calls = [];

  function get(selector) {
    if (!elements.has(selector)) {
      elements.set(selector, new Element());
    }
    return elements.get(selector);
  }

  const panel = get("[data-role-page]");
  panel.dataset.rolePage = role;

  for (const selector of [
    "#lista-pendencias",
    "#responsavel-message",
    "#cadastro-usuarios",
    "#cadastro-recursos",
    "#lista-recursos",
    "#form-vinculo",
    "#vinculo-responsavel",
    "#vinculo-recurso",
    "#vinculo-mensagem",
  ]) {
    get(selector);
  }

  for (const selector of ["#cadastro-usuarios", "#cadastro-recursos"]) {
    const element = get(selector);

    Object.defineProperty(element, "innerHTML", {
      set(html) {
        const ids = html.matchAll(/id="([^"]+)"/g);
        for (const match of ids) get(`#${match[1]}`);
      },
    });
  }

  global.document = {
    querySelector: get,
    getElementById: id => get(`#${id}`),
    createElement: () => new Element(),
  };

  global.FormData = class {
    constructor(form) {
      this.values = form.values || {};
    }

    *[Symbol.iterator]() {
      yield* Object.entries(this.values);
    }
  };

  global.ensureAuthenticated = async () => user;

  global.apiRequest = async (url, options = {}) => {
    calls.push({ url, options });
    return handler(url, options);
  };

  global.userFacingError = error => error.message;

  delete require.cache[require.resolve(script)];
  require(script);

  return { get, calls, panel };
}

async function settle() {
  for (let i = 0; i < 5; i++) {
    await new Promise(resolve => setImmediate(resolve));
  }
}

async function trigger(element, event = "submit") {
  assert.equal(typeof element.listeners[event], "function");
  return element.listeners[event]({
    preventDefault() {},
  });
}

test("bloqueia usuario com perfil diferente", async () => {
  const page = createPage("ADMIN", {
    name: "Solicitante",
    role: "SOLICITANTE",
  });

  await settle();

  assert.equal(page.panel.children[0].textContent, "Acesso não permitido");
  assert.equal(page.calls.length, 0);
});

test("exibe mensagem quando autenticacao falha", async () => {
  const page = createPage("RESPONSAVEL", null);
  global.ensureAuthenticated = async () => {
    throw new Error("Sessão inválida");
  };

  // Recarrega o script para executar com a falha simulada.
  delete require.cache[require.resolve(script)];
  require(script);

  await settle();

  assert.match(
    page.panel.children.at(-1).textContent,
    /Não foi possível verificar seu perfil/
  );
});

test("responsavel visualiza ausencia de pendencias", async () => {
  const page = createPage(
    "RESPONSAVEL",
    { name: "Responsável", role: "RESPONSAVEL" },
    async () => []
  );

  await settle();

  assert.equal(
    page.get("#responsavel-message").textContent,
    "Nenhuma solicitação pendente."
  );
  assert.equal(page.calls[0].url, "/v1/responsavel/pendencias");
});

test("responsavel exige justificativa antes de aprovar", async () => {
  let consultas = 0;

  const page = createPage(
    "RESPONSAVEL",
    { name: "Responsável", role: "RESPONSAVEL" },
    async (url) => {
      if (url === "/v1/responsavel/pendencias") {
        consultas++;
        return consultas === 1 ? [{
          item_id: "item/1",
          resource_name: "Sala A",
          resource_type: "sala",
          start: "2026-12-01T10:00:00Z",
          end: "2026-12-01T11:00:00Z",
          reason: "Aula",
        }] : [];
      }
      return {};
    }
  );

  await settle();

  const card = page.get("#lista-pendencias").children[0];
  assert.equal(card.children[0].textContent, "Sala A");

  const justificativa = card.children[4];
  const aprovar = card.children[5].children[0];

  await trigger(aprovar, "click");

  assert.equal(card.children[6].textContent, "Informe uma justificativa.");
  assert.equal(justificativa.focused, true);

  justificativa.value = "Recurso disponível para a atividade";
  await trigger(aprovar, "click");
  await settle();

  const decisao = page.calls.find(call => call.options.method === "POST");

  assert.equal(
    decisao.url,
    "/v1/reservations/items/item%2F1/decision"
  );

  assert.deepEqual(JSON.parse(decisao.options.body), {
    decision_type: "RECURSO_RESTRITO",
    decision: "APROVADA",
    justification: "Recurso disponível para a atividade",
  });

  assert.equal(
    page.get("#responsavel-message").textContent,
    "Nenhuma solicitação pendente."
  );
});

test("responsavel rejeita recurso docente e trata erro da API", async () => {
  const page = createPage(
    "RESPONSAVEL",
    { name: "Responsável", role: "RESPONSAVEL" },
    async (url, options) => {
      if (options.method === "POST") {
        throw new Error("Conflito na decisão");
      }

      return [{
        item_id: "docente-1",
        resource_name: "Professor A",
        resource_type: "professor",
        start: "2026-12-01T10:00:00Z",
        end: "2026-12-01T11:00:00Z",
        reason: "Orientação",
      }];
    }
  );

  await settle();

  const card = page.get("#lista-pendencias").children[0];
  card.children[4].value = "Solicitação não aprovada";

  const rejeitar = card.children[5].children[1];
  await trigger(rejeitar, "click");

  const decisao = page.calls.find(call => call.options.method === "POST");

  assert.deepEqual(JSON.parse(decisao.options.body), {
    decision_type: "VALIDACAO_DOCENTE",
    decision: "REJEITADA",
    justification: "Solicitação não aprovada",
  });

  assert.equal(card.children[6].textContent, "Conflito na decisão");
  assert.equal(rejeitar.disabled, false);
});

test("administrador cadastra usuarios recursos e vincula responsaveis", async () => {
  const page = createPage(
    "ADMIN",
    { name: "Administrador", role: "ADMIN" },
    async (url, options) => {
      if (options.method === "POST") return { id: "novo" };

      if (url === "/v1/admin/users") {
        return [
          {
            id: "resp-1",
            name: "Responsável",
            email: "resp@example.test",
            role: "RESPONSAVEL",
            active: true,
          },
          {
            id: "sol-1",
            name: "Solicitante",
            role: "SOLICITANTE",
            active: true,
          },
        ];
      }

      if (url === "/v1/admin/resources") {
        return [{
          id: "sala-1",
          resource_type: "sala",
          name: "Sala A",
          active: true,
        }];
      }

      return [];
    }
  );

  await settle();

  const usuario = page.get("#form-usuario");
  usuario.values = {
    name: "Novo usuário",
    email: "novo@example.test",
    password: "senha-de-teste",
    role: "SOLICITANTE",
  };

  await trigger(usuario);

  assert.equal(
    page.get("#usuario-mensagem").textContent,
    "Usuário cadastrado com sucesso!"
  );

  const recurso = page.get("#form-recurso");
  recurso.values = {
    resource_type: "sala",
    name: "Sala B",
    restricted: "true",
    category: "aula",
    location: "Bloco B",
    capacity: "30",
    quantity_total: "",
  };

  await trigger(recurso);

  const cadastro = page.calls.find(call =>
    call.url === "/v1/admin/resources" &&
    call.options.method === "POST"
  );

  assert.deepEqual(JSON.parse(cadastro.options.body), {
    resource_type: "sala",
    name: "Sala B",
    restricted: true,
    category: "aula",
    location: "Bloco B",
    capacity: 30,
  });

  const tipo = page.get("#recurso-tipo");
  tipo.value = "material";
  await trigger(tipo, "change");

  assert.equal(page.get("#recurso-capacidade").disabled, true);
  assert.equal(page.get("#recurso-quantidade").required, true);

  const responsavel = page.get("#vinculo-responsavel");
  const seletorRecurso = page.get("#vinculo-recurso");

  assert.equal(responsavel.children.length, 1);
  assert.equal(seletorRecurso.children.length, 1);

  responsavel.value = "resp-1";
  seletorRecurso.value = "sala-1";

  await trigger(page.get("#form-vinculo"));

  const vinculo = page.calls.find(call =>
    call.url === "/v1/admin/responsaveis/resp-1/recursos"
  );

  assert.deepEqual(JSON.parse(vinculo.options.body), {
    resource_id: "sala-1",
  });

  assert.equal(
    page.get("#vinculo-mensagem").textContent,
    "Responsável vinculado com sucesso!"
  );
});

test("administrador cadastra professor e material com campos desativados", async () => {
  const page = createPage(
    "ADMIN",
    { name: "Administrador", role: "ADMIN" },
    async (url, options) => {
      if (options.method === "POST") return { id: "novo-recurso" };
      return [];
    }
  );

  await settle();

  const formulario = page.get("#form-recurso");
  const tipo = page.get("#recurso-tipo");

  // FormData real não inclui campos disabled: professor não envia categoria/localização.
  tipo.value = "professor";
  await trigger(tipo, "change");
  assert.equal(page.get("#recurso-categoria").disabled, true);
  assert.equal(page.get("#recurso-localizacao").disabled, true);

  formulario.values = {
    resource_type: "professor",
    name: "Professor de Matemática",
    restricted: "false",
  };

  await trigger(formulario);

  // Material não envia a localização desativada, mas exige categoria e quantidade.
  tipo.value = "material";
  await trigger(tipo, "change");
  assert.equal(page.get("#recurso-localizacao").disabled, true);
  assert.equal(page.get("#recurso-quantidade").disabled, false);

  formulario.values = {
    resource_type: "material",
    name: "Projetor",
    category: "audiovisual",
    quantity_total: "5",
    restricted: "true",
  };

  await trigger(formulario);

  const cadastros = page.calls
    .filter(call => call.url === "/v1/admin/resources" && call.options.method === "POST")
    .map(call => JSON.parse(call.options.body));

  assert.deepEqual(cadastros, [
    {
      resource_type: "professor",
      name: "Professor de Matemática",
      restricted: false,
      category: null,
      location: null,
    },
    {
      resource_type: "material",
      name: "Projetor",
      restricted: true,
      category: "audiovisual",
      location: null,
      quantity_total: 5,
    },
  ]);

  assert.equal(
    page.get("#recurso-mensagem").textContent,
    "Recurso cadastrado com sucesso!"
  );
});
