import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";
import type { Order } from "../types";

const STATUS_COLORS: Record<string, string> = {
  created: "bg-gray-100 text-gray-700",
  inspection_pending: "bg-yellow-100 text-yellow-800",
  inspection_completed: "bg-blue-100 text-blue-800",
  awaiting_customer_confirmation: "bg-orange-100 text-orange-800",
  confirmed: "bg-green-100 text-green-800",
  ready_for_pickup: "bg-cyan-100 text-cyan-800",
  picked_up: "bg-slate-100 text-slate-600",
};

const STATUS_LABEL: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Insp. Done",
  awaiting_customer_confirmation: "Awaiting Sig",
  confirmed: "Confirmed",
  ready_for_pickup: "Ready Pickup",
  picked_up: "Picked Up",
};

function NavBar() {
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

export { NavBar };

export default function DashboardPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/orders").then(({ data }) => setOrders(data)).finally(() => setLoading(false));
  }, []);

  const today = new Date().toDateString();
  const todayOrders = orders.filter((o) => new Date(o.created_at).toDateString() === today);
  const pending = orders.filter((o) => o.status === "awaiting_customer_confirmation");
  const confirmed = orders.filter((o) => o.status === "confirmed");
  const readyPickup = orders.filter((o) => o.status === "ready_for_pickup");

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <div className="max-w-5xl mx-auto p-6 space-y-6">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { count: orders.length, label: "Total Orders", color: "text-gray-800" },
            { count: todayOrders.length, label: "Today", color: "text-blue-600" },
            { count: pending.length, label: "Awaiting Sig", color: "text-orange-600" },
            { count: confirmed.length, label: "Confirmed", color: "text-green-600" },
            { count: readyPickup.length, label: "Ready Pickup", color: "text-cyan-600" },
          ].map(({ count, label, color }) => (
            <div key={label} className="bg-white rounded-xl border p-4">
              <div className={`text-2xl font-bold ${color}`}>{count}</div>
              <div className="text-sm text-gray-500">{label}</div>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="font-semibold text-gray-700">Recent Orders</h3>
            <Link to="/orders" className="text-sm text-indigo-600 hover:underline">View all →</Link>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : (
            <div className="divide-y">
              {orders.slice(0, 10).map((order) => (
                <Link key={order.id} to={`/orders/${order.id}`} className="flex items-center justify-between p-4 hover:bg-gray-50 transition">
                  <div>
                    <span className="font-medium text-gray-800">{order.customer?.name || "—"}</span>
                    <span className="text-sm text-gray-400 ml-2">{order.items?.length || 0} items</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
                      {STATUS_LABEL[order.status] || order.status}
                    </span>
                    <span className="text-xs text-gray-400">{new Date(order.created_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              ))}
              {orders.length === 0 && <div className="p-8 text-center text-gray-400">No orders yet</div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
