import axios, { AxiosHeaders } from "axios";
import { clearStoredProfile } from "./session";
import { useToast } from "@/composables/useToast";

function resolveApiBaseUrl(): string {
  return "/api";
}

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  withCredentials: true,
});

function isMutatingMethod(method?: string): boolean {
  if (!method) {
    return false;
  }

  return ["post", "put", "patch", "delete"].includes(method.toLowerCase());
}

function normalizeApiUrl(url?: string): string | undefined {
  if (!url || typeof url !== "string") {
    return url;
  }

  if (/^https?:\/\//.test(url)) {
    return url;
  }

  return url;
}

function getAuthToken(): string | null {
  return (
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token")
  );
}

api.interceptors.request.use((config) => {
  config.url = normalizeApiUrl(config.url);

  const token = getAuthToken();

  if (token) {
    const headers = AxiosHeaders.from(config.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    config.headers = headers;
  }

  return config;
});

api.interceptors.response.use(
  (response) => {
    if (isMutatingMethod(response.config.method) && typeof window !== "undefined") {
      window.dispatchEvent(new Event("notifications:refresh"));
    }

    return response;
  },
  (error) => {
    const status = error?.response?.status;
    const url = String(error?.config?.url || "");
    const isAuthEndpoint = url.includes("/login") || url.includes("/register");

    if (status === 401 && !isAuthEndpoint && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      sessionStorage.removeItem("access_token");
      clearStoredProfile();

      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    } else {
      const { error: showErrorToast } = useToast();
      const errorMessage = error?.response?.data?.detail || "Une erreur est survenue";
      showErrorToast(typeof errorMessage === 'string' ? errorMessage : "Erreur inattendue");
    }

    return Promise.reject(error);
  }
);

export default api;
export { api };
