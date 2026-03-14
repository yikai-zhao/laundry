import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { username, password });
      setAuth(data.access_token, data.user);
      nav("/orders");
    } catch {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100 p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm space-y-5">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-indigo-700">🧥 干洗验衣</h1>
          <p className="text-sm text-gray-500 mt-1">员工登录</p>
        </div>
        {error && <div className="bg-red-50 text-red-600 text-sm p-3 rounded-lg">用户名或密码错误</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
          <input
            className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
          <input
            type="password"
            className="w-full border rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 outline-none"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition"
        >
          {loading ? "登录中..." : "登录"}
        </button>
        <p className="text-xs text-gray-400 text-center">staff / staff123 · admin / admin123</p>
      </form>
    </div>
  );
}
