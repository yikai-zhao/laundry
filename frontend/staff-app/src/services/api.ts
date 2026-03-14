import axios from "axios";

function getApiHost(): string {
  // In production, VITE_API_BASE_URL is set explicitly.
  // In dev (Codespaces or localhost), return "" so Vite proxy handles /api and /storage.
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  return "";
}

export const API_HOST = getApiHost();
export const api = axios.create({ baseURL: `${API_HOST}/api/v1` });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getCustomerSignBaseUrl(): string {
  if (import.meta.env.VITE_CUSTOMER_SIGN_BASE_URL) return import.meta.env.VITE_CUSTOMER_SIGN_BASE_URL;
  const h = window.location.hostname;
  if (h.includes(".app.github.dev") || h.includes(".preview.app.github.dev"))
    return window.location.origin.replace(/-\d+\./, "-3003.");
  return "http://localhost:3003";
}
