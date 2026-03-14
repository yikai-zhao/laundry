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

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (search) params.q = search;
    if (statusFilter) params.status = statusFilter;
    api.get("/orders", { params }).then(({ data }) => setOrders(data)).finally(() => setLoading(false));
  }, [search, statusFilter]);

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-slate-800 text-white px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <h1 className="font-bold text-lg">Admin</h1>
          <Link to="/dashboard" className="text-sm hover:text-slate-300">Dashboard</Link>
          <Link to="/orders" className="text-sm text-white font-medium">Orders</Link>
          <Link to="/customers" className="text-sm hover:text-slate-300">Customers</Link>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-300">{user?.display_name || user?.username}</span>
          <button onClick={logout} className="text-sm text-slate-400 hover:text-white">Logout</button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto p-6 space-y-4">
        <h2 className="text-2xl font-bold text-gray-800">All Orders</h2>

        <div className="flex gap-3">
          <input
            placeholder="Search customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm flex-1 outline-none focus:ring-2 focus:ring-slate-400"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm outline-none"
          >
            <option value="">All Status</option>
            <option value="created">Created</option>
            <option value="inspection_pending">Inspecting</option>
            <option value="inspection_completed">Inspected</option>
            <option value="awaiting_customer_confirmation">Awaiting Signature</option>
            <option value="confirmed">Confirmed</option>
          </select>
        </div>

        <div className="bg-white rounded-xl border divide-y">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : orders.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No orders found</div>
          ) : (
            orders.map((order) => (
              <Link key={order.id} to={`/orders/${order.id}`} className="flex items-center justify-between p-4 hover:bg-gray-50 transition">
                <div>
                  <span className="font-medium text-gray-800">{order.customer?.name || "—"}</span>
                  <span className="text-sm text-gray-400 ml-2">{order.items?.length || 0} items</span>
                  {order.note && <span className="text-sm text-gray-400 ml-2">· {order.note}</span>}
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
                    {order.status.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-gray-400">{new Date(order.created_at).toLocaleString()}</span>
                  <span className="text-gray-300">→</span>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
