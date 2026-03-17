import { Link } from "react-router-dom";
import { useAuthStore } from "../store/auth";

export default function NavBar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  return (
    <nav className="bg-slate-800 text-white px-6 py-3 flex justify-between items-center">
      <div className="flex items-center gap-6">
        <h1 className="font-bold text-lg">🧥 Admin</h1>
        <Link to="/dashboard" className="text-sm hover:text-slate-300">Dashboard</Link>
        <Link to="/orders" className="text-sm hover:text-slate-300">Orders</Link>
        <Link to="/customers" className="text-sm hover:text-slate-300">Customers</Link>
        <Link to="/staff" className="text-sm hover:text-slate-300">Staff</Link>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-300">{user?.display_name || user?.username}</span>
        <button onClick={logout} className="text-sm text-slate-400 hover:text-white">Logout</button>
      </div>
    </nav>
  );
}
