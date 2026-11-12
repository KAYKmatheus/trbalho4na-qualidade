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

document.querySelectorAll("[data-logout]").forEach((button) => {
  button.addEventListener("click", logout);
});
