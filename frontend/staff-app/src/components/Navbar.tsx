import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export default function Navbar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const nav = useNavigate();
  const isAdmin = user?.role === "admin";
  const [open, setOpen] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = () => {
    logout();
    nav("/login");
  };

  if (!user) return null;

  const initials = (user.display_name || user.username)
    .split(" ").slice(0, 2).map((w: string) => w[0]?.toUpperCase()).join("");
  const avatarColors: Record<string, string> = { admin: "bg-rose-500", staff: "bg-indigo-500" };
  const avatarBg = avatarColors[user.role] ?? "bg-gray-500";

  return (
    <nav className="bg-indigo-700 text-white px-4 py-2.5 flex justify-between items-center shadow-sm">
      <div className="flex items-center gap-5">
        <Link to="/orders" className="font-bold text-lg">🧥 Laundry Inspector</Link>
        <Link to="/orders" className="text-sm text-indigo-200 hover:text-white transition">Orders</Link>
        <Link to="/orders/new" className="text-sm text-indigo-200 hover:text-white transition">+ New</Link>
        {isAdmin && (
          <Link to="/admin" className="text-sm text-indigo-200 hover:text-white transition">Admin</Link>
        )}
      </div>
      <div className="relative" ref={dropRef}>
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 hover:opacity-90 transition focus:outline-none"
        >
          {user.must_change_password && (
            <span className="text-amber-300 text-xs font-medium">⚠ Change password</span>
          )}
          <div className={`w-8 h-8 rounded-full ${avatarBg} flex items-center justify-center text-sm font-bold select-none`}>
            {initials}
          </div>
        </button>

        {open && (
          <div className="absolute right-0 mt-1 w-52 bg-white rounded-xl shadow-lg py-1.5 z-50 text-sm text-gray-700 border border-gray-100">
            <div className="px-4 py-2.5 border-b border-gray-100">
              <p className="font-semibold text-gray-800">{user.display_name || user.username}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role}</p>
              {user.last_login_at && (
                <p className="text-xs text-gray-400 mt-0.5">
                  Last login: {new Date(user.last_login_at).toLocaleString()}
                </p>
              )}
            </div>
            <button
              onClick={() => { setOpen(false); nav("/change-password"); }}
              className="w-full text-left px-4 py-2 hover:bg-indigo-50 flex items-center gap-2"
            >
              🔑 Change Password
              {user.must_change_password && (
                <span className="ml-auto text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">Required</span>
              )}
            </button>
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 flex items-center gap-2"
            >
              ↩ Log Out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}

