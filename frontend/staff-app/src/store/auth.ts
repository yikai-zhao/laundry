import { create } from "zustand";
import type { User } from "../types";

interface AuthState {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

function safeGetFromLocalStorage(key: string, defaultValue: string): string {
  try {
    const value = localStorage.getItem(key);
    console.log(`[Auth] Retrieved ${key}:`, value ? `${value.substring(0, 20)}...` : "null");
    return value || defaultValue;
  } catch (error) {
    console.error(`[Auth] Failed to read ${key} from localStorage:`, error);
    return defaultValue;
  }
}

function safeJsonParse(json: string, defaultValue: null): User | null {
  try {
    const parsed = json ? JSON.parse(json) : defaultValue;
    console.log(`[Auth] Parsed user:`, parsed ? `User ID: ${(parsed as any)?.id}` : "null");
    return parsed;
  } catch (error) {
    console.error("[Auth] Failed to parse user from JSON:", error);
    return defaultValue;
  }
}

const initialToken = safeGetFromLocalStorage("token", "");
const initialUser = safeJsonParse(safeGetFromLocalStorage("user", "null"), null);

console.log("[Auth] Store initialization - Token present:", !!initialToken, "User present:", !!initialUser);

export const useAuthStore = create<AuthState>((set) => ({
  token: initialToken || null,
  user: initialUser,
  setAuth: (token, user) => {
    try {
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      console.log("[Auth] setAuth successful");
      set({ token, user });
    } catch (error) {
      console.error("[Auth] Failed to save auth to localStorage:", error);
    }
  },
  logout: () => {
    try {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      console.log("[Auth] logout successful");
      set({ token: null, user: null });
    } catch (error) {
      console.error("[Auth] Failed to clear auth from localStorage:", error);
    }
  },
}));
