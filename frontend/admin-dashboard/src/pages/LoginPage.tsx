import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/auth/login", { username: username.trim().toLowerCase(), password });
      setAuth(data.access_token, data.user);
      navigate("/dashboard");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string }; status?: number } };
      const detail = err?.response?.data?.detail || "";
      const status = err?.response?.status;
      if (status === 429) {
        setError(detail || "Account temporarily locked. Please try again later.");
      } else if (status === 403) {
        setError(detail || "Account is disabled. Contact your system administrator.");
      } else {
        setError(detail || "Invalid username or password");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-900 p-4">
      <form onSubmit={submit} className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-sm space-y-5">
        <div className="text-center">
          <div className="text-3xl mb-2">🛡️</div>
          <h1 className="text-2xl font-bold text-slate-800">Admin Dashboard</h1>
          <p className="text-xs text-gray-400 mt-1">Authorized access only</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl flex gap-2">
            <span className="shrink-0">⚠</span>
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Username</label>
          <input
            placeholder="Enter username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-slate-600"
            autoFocus
            required
          />
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">Password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="w-full border rounded-xl px-3 py-2.5 pr-10 text-sm outline-none focus:ring-2 focus:ring-slate-600"
              required
            />
            <button type="button" tabIndex={-1} onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-slate-800 text-white py-2.5 rounded-xl font-semibold hover:bg-slate-700 disabled:opacity-50 transition text-sm"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Signing in…
            </span>
          ) : "Sign In"}
        </button>
      </form>
      <p className="text-xs text-slate-500 text-center mt-4">
        Laundry Management System &copy; {new Date().getFullYear()}
      </p>
    </div>
  );
}

