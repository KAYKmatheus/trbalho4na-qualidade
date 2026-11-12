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

document.querySelectorAll("[data-logout]").forEach((button) => {
  button.addEventListener("click", logout);
});
