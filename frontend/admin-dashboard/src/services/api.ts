import axios from "axios";

function getApiHost(): string {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, "");
  return "";
}

export const API_HOST = getApiHost();
export const api = axios.create({ baseURL: `${API_HOST}/api/v1` });

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
  const token = localStorage.getItem("admin_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
