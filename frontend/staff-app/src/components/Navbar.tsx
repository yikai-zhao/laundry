import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export default function Navbar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const nav = useNavigate();

  const handleLogout = () => {
    logout();
    nav("/login");
  };

  if (!user) return null;

  return (
    <nav className="bg-indigo-700 text-white px-4 py-2.5 flex justify-between items-center shadow-sm">
      <div className="flex items-center gap-5">
        <Link to="/orders" className="font-bold text-lg">🧥 Laundry AI</Link>
        <Link to="/orders" className="text-sm text-indigo-200 hover:text-white transition">Orders</Link>
        <Link to="/orders/new" className="text-sm text-indigo-200 hover:text-white transition">+ New</Link>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-indigo-200">{user.display_name || user.username}</span>
        <button onClick={handleLogout} className="text-sm text-indigo-300 hover:text-white transition">Logout</button>
      </div>
    </nav>
  );
}
