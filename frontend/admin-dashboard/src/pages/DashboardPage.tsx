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
};

export default function DashboardPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    api.get("/orders").then(({ data }) => setOrders(data)).finally(() => setLoading(false));
  }, []);

  const today = new Date().toDateString();
  const todayOrders = orders.filter((o) => new Date(o.created_at).toDateString() === today);
  const pending = orders.filter((o) => o.status === "awaiting_customer_confirmation");
  const confirmed = orders.filter((o) => o.status === "confirmed");

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-slate-800 text-white px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <h1 className="font-bold text-lg">Admin</h1>
          <Link to="/dashboard" className="text-sm hover:text-slate-300">Dashboard</Link>
          <Link to="/orders" className="text-sm hover:text-slate-300">Orders</Link>
          <Link to="/customers" className="text-sm hover:text-slate-300">Customers</Link>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-300">{user?.display_name || user?.username}</span>
          <button onClick={logout} className="text-sm text-slate-400 hover:text-white">Logout</button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto p-6 space-y-6">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border p-4">
            <div className="text-2xl font-bold text-gray-800">{orders.length}</div>
            <div className="text-sm text-gray-500">Total Orders</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-2xl font-bold text-blue-600">{todayOrders.length}</div>
            <div className="text-sm text-gray-500">Today</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-2xl font-bold text-orange-600">{pending.length}</div>
            <div className="text-sm text-gray-500">Awaiting Signature</div>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <div className="text-2xl font-bold text-green-600">{confirmed.length}</div>
            <div className="text-sm text-gray-500">Confirmed</div>
          </div>
        </div>

        {/* Recent Orders */}
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
                      {order.status.replace(/_/g, " ")}
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
