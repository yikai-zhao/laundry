import axios from "axios";

function getApiHost(): string {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  const h = window.location.hostname;
  if (h.includes(".app.github.dev") || h.includes(".preview.app.github.dev"))
    return window.location.origin.replace(/-\d+\./, "-8000.");
  return "http://localhost:8000";
}

export const API_HOST = getApiHost();
export const api = axios.create({ baseURL: `${API_HOST}/api/v1` });
