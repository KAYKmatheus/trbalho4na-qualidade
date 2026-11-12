const AUTH_TOKEN_KEY = "alocasenac_access_token";

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getAuthToken() {
  try {
    return sessionStorage.getItem(AUTH_TOKEN_KEY);
  } catch (error) {
    console.error("Não foi possível acessar a sessão do navegador.", error);
    return null;
  }
}

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch (error) {
    throw new ApiError(0, "Não foi possível conectar ao serviço. Tente novamente.");
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const detail = payload && payload.detail;
    throw new ApiError(response.status, typeof detail === "string" ? detail : "Não foi possível concluir a solicitação.");
  }
  return payload;
}

function logout() {
  try {
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
  } catch (error) {
    console.error("Não foi possível limpar a sessão do navegador.", error);
  }
  window.location.assign("/app/index.html");
}

function showMessage(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function userFacingError(error) {
  if (error.status === 403) {
    return `Você não tem permissão para realizar esta ação. ${error.message}`;
  }
  if (error.status === 409) {
    return `Conflito: ${error.message}`;
  }
  if (error.status === 422) {
    return `Verifique os dados informados. ${error.message}`;
  }
  return error.message || "Não foi possível concluir a solicitação. Tente novamente.";
}

async function ensureAuthenticated() {
  if (!getAuthToken()) {
    window.location.assign("/app/index.html");
    return false;
  }
  try {
    await apiRequest("/v1/auth/me");
    return true;
  } catch (error) {
    if (error.status === 401) {
      logout();
      return false;
    }
    throw error;
  }
}

const loginForm = document.querySelector("#login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.querySelector("#login-error");
    message.hidden = true;

    try {
      const formData = new FormData(loginForm);
      const result = await apiRequest("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });

      try {
        sessionStorage.setItem(AUTH_TOKEN_KEY, result.access_token);
      } catch (error) {
        console.error("Não foi possível guardar a sessão no navegador.", error);
        throw new Error("O navegador não permitiu guardar a sessão. Verifique as configurações e tente novamente.");
      }

      window.location.assign("/app/buscar.html");
    } catch (error) {
      const messageText = error.status === 401 ? "E-mail ou senha inválidos." : error.message;
      showMessage(message, messageText || "Não foi possível entrar. Tente novamente.");
    }
  });
}

const searchForm = document.querySelector("#search-form");
if (searchForm) {
  const searchMessage = document.querySelector("#search-message");
  const searchResults = document.querySelector("#search-results");
  ensureAuthenticated().catch((error) => showMessage(searchMessage, userFacingError(error)));

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    searchMessage.hidden = true;
    searchResults.replaceChildren();

    const formData = new FormData(searchForm);
    const start = new Date(String(formData.get("start")));
    const end = new Date(String(formData.get("end")));
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start >= end) {
      showMessage(searchMessage, "Informe um período válido, com início anterior ao fim.");
      return;
    }

    const params = new URLSearchParams({
      start: start.toISOString(),
      end: end.toISOString(),
    });
    const resourceType = String(formData.get("resource_type") || "");
    const capacity = String(formData.get("capacity") || "");
    if (resourceType) {
      params.set("resource_type", resourceType);
    }
    if (capacity) {
      params.set("capacity", capacity);
    }

    try {
      const resources = await apiRequest(`/v1/resources/search?${params.toString()}`);
      if (resources.length === 0) {
        showMessage(searchMessage, "Nenhum recurso disponível para os filtros informados.");
        return;
      }

      for (const resource of resources) {
        const card = document.createElement("article");
        card.className = "resource-card";
        const heading = document.createElement("h2");
        heading.textContent = resource.name;
        const details = document.createElement("p");
        const capacityText = resource.capacity ? `${resource.capacity} lugares` : "Não se aplica";
        const availability = resource.available_quantity === null || resource.available_quantity === undefined
          ? "Disponível no período"
          : `${resource.available_quantity} unidades disponíveis`;
        details.textContent = `${resource.resource_type} · Capacidade: ${capacityText} · ${availability}`;
        const reserveButton = document.createElement("button");
        reserveButton.type = "button";
        reserveButton.textContent = "Reservar";
        reserveButton.addEventListener("click", () => {
          try {
            sessionStorage.setItem("alocasenac_selected_resource", JSON.stringify(resource));
            sessionStorage.setItem("alocasenac_selected_start", start.toISOString());
            sessionStorage.setItem("alocasenac_selected_end", end.toISOString());
            window.location.assign("/app/reservar.html");
          } catch (error) {
            console.error("Não foi possível guardar a seleção no navegador.", error);
            showMessage(searchMessage, "O navegador não permitiu guardar a seleção. Tente novamente.");
          }
        });
        card.append(heading, details, reserveButton);
        searchResults.append(card);
      }
      showMessage(searchMessage, `${resources.length} recurso(s) disponível(is).`);
    } catch (error) {
      showMessage(searchMessage, userFacingError(error));
    }
  });
}

document.querySelectorAll("[data-logout]").forEach((button) => {
  button.addEventListener("click", logout);
});
