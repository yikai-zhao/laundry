import axios from "axios";

function getApiHost(): string {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  return "";
}

export const API_HOST = getApiHost();
export const api = axios.create({ baseURL: `${API_HOST}/api/v1` });
