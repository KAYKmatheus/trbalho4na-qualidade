const assert = require("node:assert/strict");
const path = require("node:path");
const { test } = require("node:test");

const appScript = path.resolve(__dirname, "../../app/web/static/app.js");

class FakeElement {
  constructor(values = {}) {
    this.values = values;
    this.listeners = {};
    this.children = [];
    this.dataset = {};
    this.hidden = false;
    this.textContent = "";
    this.value = "";
    this.disabled = false;
  }

  addEventListener(name, callback) {
    this.listeners[name] = callback;
  }

  append(...elements) {
    this.children.push(...elements);
  }

  replaceChildren(...elements) {
    this.children = elements;
  }
}

class FakeStorage {
  constructor(initial = {}) {
    this.values = new Map(Object.entries(initial));
    this.failGet = false;
    this.failSet = false;
    this.failRemove = false;
  }

  getItem(key) {
    if (this.failGet) {
      throw new Error("storage read blocked");
    }
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    if (this.failSet) {
      throw new Error("storage write blocked");
    }
    this.values.set(key, String(value));
  }

  removeItem(key) {
    if (this.failRemove) {
      throw new Error("storage removal blocked");
    }
    this.values.delete(key);
  }
}

class FakeFormData {
  constructor(form) {
    this.values = form.values;
  }

  get(key) {
    return this.values[key] ?? null;
  }
}

function jsonResponse(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => "application/json" },
    json: async () => payload,
  };
}

function textResponse(status = 500) {
  return {
    ok: false,
    status,
    headers: { get: () => "text/plain" },
  };
}

function loadApp({ selectors = {}, storage = new FakeStorage(), responses = [], logoutButtons = [], confirm = true } = {}) {
  const calls = [];
  const navigation = [];
  const errors = [];
  const elements = { ...selectors };
  const originalConsoleError = console.error;
  console.error = (...args) => errors.push(args);
  global.sessionStorage = storage;
  global.FormData = FakeFormData;
  global.document = {
    querySelector: (selector) => elements[selector] || null,
    querySelectorAll: (selector) => (selector === "[data-logout]" ? logoutButtons : []),
    createElement: (tagName) => {
      const element = new FakeElement();
      element.tagName = tagName;
      return element;
    },
  };
  global.window = {
    location: { assign: (url) => navigation.push(url) },
    confirm: () => confirm,
  };
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    const response = responses.shift();
    if (response instanceof Error) {
      throw response;
    }
    if (typeof response === "function") {
      return response(url, options);
    }
    assert.ok(response, `Unexpected request: ${url}`);
    return response;
  };
  delete require.cache[require.resolve(appScript)];
  require(appScript);
  return { calls, elements, errors, navigation, storage };
}

async function submit(element) {
  let prevented = false;
  await element.listeners.submit({ preventDefault: () => { prevented = true; } });
  return prevented;
}

async function click(element) {
  await element.listeners.click();
}

async function flushPromises() {
  await new Promise((resolve) => setImmediate(resolve));
}

test("login sends credentials, stores the token, and redirects", async () => {
  const form = new FakeElement({ email: "user@example.test", password: "secret" });
  const message = new FakeElement();
  const { calls, navigation, storage } = loadApp({
    selectors: { "#login-form": form, "#login-error": message },
    responses: [
      jsonResponse({ access_token: "issued-token" }),
      jsonResponse({ id: "user-1", role: "SOLICITANTE" }),
    ],
  });

  assert.equal(await submit(form), true);
  assert.equal(calls[1].url, "/v1/auth/me");
  assert.equal(calls[0].url, "/v1/auth/login");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.headers.get("Content-Type"), "application/json");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    email: "user@example.test",
    password: "secret",
  });
  assert.equal(storage.getItem("alocasenac_access_token"), "issued-token");
  assert.deepEqual(navigation, ["/app/buscar.html"]);
  assert.equal(message.hidden, true);
});

test("login reports invalid credentials and blocked session storage", async () => {
  const invalidForm = new FakeElement({ email: "bad@example.test", password: "wrong" });
  const invalidMessage = new FakeElement();
  loadApp({
    selectors: { "#login-form": invalidForm, "#login-error": invalidMessage },
    responses: [jsonResponse({ detail: "invalid" }, 401)],
  });
  await submit(invalidForm);
  assert.equal(invalidMessage.textContent, "E-mail ou senha inválidos.");

  const blockedForm = new FakeElement({ email: "user@example.test", password: "secret" });
  const blockedMessage = new FakeElement();
  const storage = new FakeStorage();
  storage.failSet = true;
  const { errors } = loadApp({
    selectors: { "#login-form": blockedForm, "#login-error": blockedMessage },
    storage,
    responses: [jsonResponse({ access_token: "issued-token" })],
  });
  await submit(blockedForm);
  assert.match(blockedMessage.textContent, /navegador não permitiu guardar a sessão/);
  assert.equal(errors.length, 1);
});

test("search validates dates, filters resources, and persists a selected resource", async () => {
  const form = new FakeElement({
    start: "2026-02-01T10:00",
    end: "2026-02-01T11:00",
    resource_type: "sala",
    capacity: "5",
  });
  const message = new FakeElement();
  const results = new FakeElement();
  const { calls, navigation, storage } = loadApp({
    selectors: {
      "#search-form": form,
      "#search-message": message,
      "#search-results": results,
    },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse([
        { id: 1, name: "Sala A", resource_type: "sala", capacity: 0, available_quantity: null },
        { id: 2, name: "Sala B", resource_type: "sala", capacity: 5, available_quantity: 2 },
      ]),
    ],
  });

  await flushPromises();
  assert.equal(await submit(form), true);
  assert.equal(calls[1].url.startsWith("/v1/resources/search?"), true);
  const query = new URLSearchParams(calls[1].url.split("?")[1]);
  assert.equal(query.get("resource_type"), "sala");
  assert.equal(query.get("capacity"), "5");
  assert.equal(calls[0].options.headers.get("Authorization"), "Bearer token");
  assert.equal(results.children.length, 2);
  assert.match(results.children[0].children[1].textContent, /Não se aplica/);
  assert.match(results.children[0].children[1].textContent, /Disponível no período/);
  assert.match(results.children[1].children[1].textContent, /5 lugares/);
  assert.match(results.children[1].children[1].textContent, /2 unidades disponíveis/);
  assert.equal(message.textContent, "2 recurso(s) disponível(is).");

  await click(results.children[0].children[2]);
  assert.equal(storage.getItem("alocasenac_selected_resource"), JSON.stringify({
    id: 1,
    name: "Sala A",
    resource_type: "sala",
    capacity: 0,
    available_quantity: null,
  }));
  assert.equal(storage.getItem("alocasenac_selected_start"), new Date("2026-02-01T10:00").toISOString());
  assert.deepEqual(navigation, ["/app/reservar.html"]);
});

test("search rejects invalid periods and reports empty and forbidden results", async () => {
  const invalidForm = new FakeElement({ start: "bad-date", end: "2026-02-01T11:00" });
  const invalidMessage = new FakeElement();
  loadApp({
    selectors: { "#search-form": invalidForm, "#search-message": invalidMessage, "#search-results": new FakeElement() },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 })],
  });
  await flushPromises();
  await submit(invalidForm);
  assert.equal(invalidMessage.textContent, "Informe um período válido, com início anterior ao fim.");

  const emptyForm = new FakeElement({ start: "2026-02-01T10:00", end: "2026-02-01T11:00" });
  const emptyMessage = new FakeElement();
  const emptyPage = loadApp({
    selectors: { "#search-form": emptyForm, "#search-message": emptyMessage, "#search-results": new FakeElement() },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 }), jsonResponse([])],
  });
  await flushPromises();
  await submit(emptyForm);
  assert.equal(emptyMessage.textContent, "Nenhum recurso disponível para os filtros informados.");
  assert.equal(emptyPage.calls.length, 2);

  const forbiddenForm = new FakeElement({ start: "2026-02-01T10:00", end: "2026-02-01T11:00" });
  const forbiddenMessage = new FakeElement();
  loadApp({
    selectors: { "#search-form": forbiddenForm, "#search-message": forbiddenMessage, "#search-results": new FakeElement() },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 }), jsonResponse({ detail: "sem acesso" }, 403)],
  });
  await flushPromises();
  await submit(forbiddenForm);
  assert.equal(forbiddenMessage.textContent, "Você não tem permissão para realizar esta ação. sem acesso");
});

test("search reports network failures and selection-storage failures", async () => {
  const form = new FakeElement({ start: "2026-02-01T10:00", end: "2026-02-01T11:00" });
  const message = new FakeElement();
  loadApp({
    selectors: { "#search-form": form, "#search-message": message, "#search-results": new FakeElement() },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 }), new Error("network down")],
  });
  await flushPromises();
  await submit(form);
  assert.equal(message.textContent, "Não foi possível conectar ao serviço. Tente novamente.");

  const storage = new FakeStorage({ alocasenac_access_token: "token" });
  storage.failSet = true;
  const reserveForm = new FakeElement({ start: "2026-02-01T10:00", end: "2026-02-01T11:00" });
  const reserveMessage = new FakeElement();
  const reserveResults = new FakeElement();
  loadApp({
    selectors: {
      "#search-form": reserveForm,
      "#search-message": reserveMessage,
      "#search-results": reserveResults,
    },
    storage,
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse([{ id: 4, name: "Material", resource_type: "material" }]),
    ],
  });
  await flushPromises();
  await submit(reserveForm);
  await click(reserveResults.children[0].children[2]);
  assert.equal(reserveMessage.textContent, "O navegador não permitiu guardar a seleção. Tente novamente.");
});

test("authentication redirects anonymous and expired sessions", async () => {
  const anonymousForm = new FakeElement();
  const anonymousMessage = new FakeElement();
  const anonymousPage = loadApp({
    selectors: { "#search-form": anonymousForm, "#search-message": anonymousMessage, "#search-results": new FakeElement() },
  });
  await flushPromises();
  assert.deepEqual(anonymousPage.navigation, ["/app/index.html"]);
  assert.equal(anonymousPage.calls.length, 0);

  const expiredForm = new FakeElement();
  const expiredPage = loadApp({
    selectors: { "#search-form": expiredForm, "#search-message": new FakeElement(), "#search-results": new FakeElement() },
    storage: new FakeStorage({ alocasenac_access_token: "expired" }),
    responses: [jsonResponse({ detail: "expired" }, 401)],
  });
  await flushPromises();
  assert.deepEqual(expiredPage.navigation, ["/app/index.html"]);
  assert.equal(expiredPage.storage.getItem("alocasenac_access_token"), null);
});

test("reservation submits selected resource and reports conflicts", async () => {
  const resource = { id: 17, name: "Sala A", resource_type: "sala" };
  const storage = new FakeStorage({
    alocasenac_access_token: "token",
    alocasenac_selected_resource: JSON.stringify(resource),
    alocasenac_selected_start: "2026-02-01T10:00:00.000Z",
    alocasenac_selected_end: "2026-02-01T11:00:00.000Z",
  });
  const form = new FakeElement({
    start: "2026-02-01T10:00",
    end: "2026-02-01T11:00",
    resource_id: "17",
    quantity: "2",
    reason: "Aula",
  });
  const message = new FakeElement();
  const select = new FakeElement();
  const start = new FakeElement();
  const end = new FakeElement();
  const page = loadApp({
    selectors: {
      "#reservation-form": form,
      "#reservation-message": message,
      "#resource": select,
      "#start": start,
      "#end": end,
    },
    storage,
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse({ status: "SOLICITADA" }),
    ],
  });
  await flushPromises();

  assert.equal(select.children.length, 1);
  assert.equal(select.children[0].value, 17);
  assert.match(select.children[0].textContent, /sala — Sala A/);
  assert.notEqual(start.value, "");
  assert.notEqual(end.value, "");
  assert.equal(await submit(form), true);
  const request = page.calls[1];
  assert.equal(request.url, "/v1/reservations");
  assert.equal(request.options.method, "POST");
  assert.deepEqual(JSON.parse(request.options.body), {
    solicitante_id: 8,
    reason: "Aula",
    items: [{
      resource_type: "sala",
      resource_id: "17",
      start: new Date("2026-02-01T10:00").toISOString(),
      end: new Date("2026-02-01T11:00").toISOString(),
      quantity: 2,
    }],
  });
  assert.equal(message.textContent, "Solicitação enviada. Estado: SOLICITADA.");
});

test("reservation validates periods and requires a selected resource", async () => {
  const form = new FakeElement({ start: "2026-02-01T11:00", end: "2026-02-01T10:00" });
  const message = new FakeElement();
  const page = loadApp({
    selectors: {
      "#reservation-form": form,
      "#reservation-message": message,
      "#resource": new FakeElement(),
      "#start": new FakeElement(),
      "#end": new FakeElement(),
    },
    storage: new FakeStorage({
      alocasenac_access_token: "token",
      alocasenac_selected_resource: "null",
    }),
    responses: [jsonResponse({ id: 8 })],
  });
  await flushPromises();
  assert.match(message.textContent, /Escolha um recurso na busca/);
  await submit(form);
  assert.equal(message.textContent, "Informe um período válido, com início anterior ao fim.");

  form.values.start = "2026-02-01T10:00";
  form.values.end = "2026-02-01T11:00";
  await submit(form);
  assert.equal(message.textContent, "Entre novamente e escolha um recurso antes de enviar a reserva.");
  assert.equal(page.calls.length, 1);
});

test("reservation maps validation errors and handles unreadable saved selections", async () => {
  const form = new FakeElement({
    start: "2026-02-01T10:00",
    end: "2026-02-01T11:00",
    resource_id: "17",
    quantity: "1",
    reason: "Aula",
  });
  const message = new FakeElement();
  loadApp({
    selectors: {
      "#reservation-form": form,
      "#reservation-message": message,
      "#resource": new FakeElement(),
      "#start": new FakeElement(),
      "#end": new FakeElement(),
    },
    storage: new FakeStorage({
      alocasenac_access_token: "token",
      alocasenac_selected_resource: JSON.stringify({ id: 17, name: "Sala", resource_type: "sala" }),
    }),
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse({ detail: [{ msg: "período inválido" }, { msg: "" }] }, 422),
    ],
  });
  await flushPromises();
  await submit(form);
  assert.equal(message.textContent, "Verifique os dados informados. período inválido");

  const unreadableStorage = new FakeStorage({ alocasenac_access_token: "token" });
  unreadableStorage.failGet = true;
  const unreadableMessage = new FakeElement();
  const unreadablePage = loadApp({
    selectors: {
      "#reservation-form": new FakeElement(),
      "#reservation-message": unreadableMessage,
      "#resource": new FakeElement(),
      "#start": new FakeElement(),
      "#end": new FakeElement(),
    },
    storage: unreadableStorage,
  });
  await flushPromises();
  assert.equal(unreadableMessage.textContent, "A seleção não está disponível. Volte à busca e escolha um recurso.");
  assert.deepEqual(unreadablePage.navigation, ["/app/index.html"]);
});

test("reservations list renders empty and populated results", async () => {
  const emptyList = new FakeElement();
  const emptyMessage = new FakeElement();
  loadApp({
    selectors: { "#reservations-list": emptyList, "#reservations-message": emptyMessage },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 }), jsonResponse([])],
  });
  await flushPromises();
  assert.equal(emptyList.children.length, 0);
  assert.equal(emptyMessage.textContent, "Você ainda não possui reservas.");

  const list = new FakeElement();
  const message = new FakeElement();
  const reservations = [
    {
      id: 1,
      status: "PENDENTE",
      items: [{ start: "not-a-date", end: "2026-02-01T11:00:00Z", resource_type: "sala", resource_id: 4 }],
    },
    {
      id: 2,
      status: "CANCELADA",
      items: [{ start: "2026-02-01T10:00:00Z", end: "2026-02-01T11:00:00Z", resource_type: "material", resource_id: 9 }],
    },
  ];
  loadApp({
    selectors: { "#reservations-list": list, "#reservations-message": message },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ id: 8 }), jsonResponse(reservations)],
  });
  await flushPromises();
  assert.equal(list.children.length, 2);
  assert.equal(list.children[0].children[1].textContent.includes("not-a-date"), true);
  assert.equal(list.children[0].children[2].textContent, "sala: 4");
  assert.equal(list.children[0].children[3].children[0].disabled, false);
  assert.equal(list.children[1].children[3].children[0].disabled, true);
  assert.match(list.children[1].children[3].children[0].title, /CANCELADA/);
  assert.equal(message.hidden, true);
});

test("reservation cancellation honors confirmation, encodes ids, and reloads", async () => {
  const list = new FakeElement();
  const message = new FakeElement();
  const page = loadApp({
    selectors: { "#reservations-list": list, "#reservations-message": message },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse([{
        id: "R/1",
        status: "APROVADA",
        items: [{ start: "2026-02-01T10:00:00Z", end: "2026-02-01T11:00:00Z", resource_type: "sala", resource_id: 4 }],
      }]),
      jsonResponse({ status: "CANCELADA" }),
      jsonResponse([]),
    ],
    confirm: false,
  });
  await flushPromises();
  const button = list.children[0].children[3].children[0];
  await click(button);
  assert.equal(page.calls.length, 2);

  global.window.confirm = () => true;
  await click(button);
  assert.equal(page.calls[2].url, "/v1/reservations/R%2F1");
  assert.equal(page.calls[2].options.method, "DELETE");
  assert.equal(page.calls[3].url, "/v1/reservations");
  assert.equal(message.textContent, "Você ainda não possui reservas.");
});

test("reservation cancellation recovers from API errors", async () => {
  const list = new FakeElement();
  const message = new FakeElement();
  const page = loadApp({
    selectors: { "#reservations-list": list, "#reservations-message": message },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [
      jsonResponse({ id: 8 }),
      jsonResponse([{
        id: 3,
        status: "SOLICITADA",
        items: [],
      }]),
      jsonResponse({ detail: "já processada" }, 409),
    ],
  });
  await flushPromises();
  const button = list.children[0].children[3].children[0];
  global.window.confirm = () => true;
  await click(button);
  assert.equal(button.disabled, false);
  assert.equal(message.textContent, "Conflito: já processada");
  assert.equal(page.calls[2].options.method, "DELETE");
});

test("reservation list reports authorization errors and logout always redirects", async () => {
  const list = new FakeElement();
  const message = new FakeElement();
  loadApp({
    selectors: { "#reservations-list": list, "#reservations-message": message },
    storage: new FakeStorage({ alocasenac_access_token: "token" }),
    responses: [jsonResponse({ detail: "sem acesso" }, 403)],
  });
  await flushPromises();
  assert.equal(message.textContent, "Você não tem permissão para realizar esta ação. sem acesso");

  const logoutButton = new FakeElement();
  const storage = new FakeStorage({ alocasenac_access_token: "token" });
  storage.failRemove = true;
  const page = loadApp({ storage, logoutButtons: [logoutButton] });
  await click(logoutButton);
  assert.equal(storage.getItem("alocasenac_access_token"), "token");
  assert.deepEqual(page.navigation, ["/app/index.html"]);
  assert.equal(page.errors.length, 1);
});
