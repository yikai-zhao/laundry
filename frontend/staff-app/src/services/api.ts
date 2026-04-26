import axios from "axios";

function getApiHost(): string {
  // 1. Explicit env var (production web deploy or Capacitor build-time injection)
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, "");

  // 2. In Capacitor native app context the page origin is capacitor://localhost or file://
  //    so there is no working relative path — we must fall back to a configurable URL.
  if (typeof window !== "undefined") {
    const origin = window.location.origin;
    if (
      origin === "capacitor://localhost" ||
      origin.startsWith("ionic://") ||
      origin.startsWith("file://") ||
      origin === "null"
    ) {
      // Native app: must use the deployed API URL set at build time.
      // Callers that forget to set VITE_API_BASE_URL will see a console warning.
      console.warn(
        "[API] Running in native Capacitor context but VITE_API_BASE_URL is not set. " +
        "Set VITE_API_BASE_URL=https://your-api.com when building for production."
      );
      return "";
    }
  }

  // 3. Dev mode — Vite proxy handles /api and /storage relative to the dev server
  return "";
}

export const API_HOST = getApiHost();
console.log("[API] API_HOST configured as:", API_HOST || "(empty - using proxy/relative)");

export const api = axios.create({ baseURL: `${API_HOST}/api/v1` });

console.log("[API] Axios baseURL:", api.defaults.baseURL);

export function resolveAssetUrl(path?: string | null): string {
  if (!path) return "";
  if (/^(?:https?:)?\/\//i.test(path) || path.startsWith("data:") || path.startsWith("blob:")) {
    return path;
  }
  if (path.startsWith("/")) {
    return `${API_HOST}${path}`;
  }
  return API_HOST ? `${API_HOST}/${path}` : `/${path}`;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log("[API]", config.method?.toUpperCase(), config.url, "- Auth header set");
  } else {
    console.log("[API]", config.method?.toUpperCase(), config.url, "- No auth token");
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log("[API] Response OK:", response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error("[API] Request failed:", {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export function getCustomerSignBaseUrl(): string {
  const configured = import.meta.env.VITE_CUSTOMER_SIGN_BASE_URL;
  if (configured) {
    if (configured.startsWith("/")) return window.location.origin + configured;
    return configured;
  }
  const h = window.location.hostname;
  if (h.includes(".app.github.dev") || h.includes(".preview.app.github.dev"))
    return window.location.origin.replace(/-\d+\./, "-3003.");
  return "http://localhost:3003";
}
