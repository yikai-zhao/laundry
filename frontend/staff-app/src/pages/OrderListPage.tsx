import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Order } from "../types";

const STATUS_COLORS: Record<string, string> = {
  created: "bg-gray-100 text-gray-700",
  inspection_pending: "bg-yellow-100 text-yellow-800",
  inspection_completed: "bg-blue-100 text-blue-800",
  awaiting_customer_confirmation: "bg-orange-100 text-orange-800",
  confirmed: "bg-green-100 text-green-800",
};

const STATUS_LABELS: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Inspected",
  awaiting_customer_confirmation: "Awaiting Signature",
  confirmed: "Confirmed",
};

export default function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search) params.q = search;
      if (statusFilter) params.status = statusFilter;
      const { data } = await api.get("/orders", { params });
      setOrders(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, statusFilter]);

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Orders</h1>
        <Link to="/orders/new" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
          + New Order
        </Link>
      </div>

      <div className="flex gap-3 mb-4">
        <input
          placeholder="Search customer..."
          className="flex-1 border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Status</option>
          <option value="created">Created</option>
          <option value="inspection_pending">Inspecting</option>
          <option value="awaiting_customer_confirmation">Awaiting Signature</option>
          <option value="confirmed">Confirmed</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : orders.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No orders yet</div>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => (
            <div
              key={o.id}
              onClick={() => nav(`/orders/${o.id}`)}
              className="bg-white border rounded-xl p-4 cursor-pointer hover:shadow-md transition flex items-center justify-between"
            >
              <div>
                <div className="font-semibold text-gray-800">{o.customer?.name || "—"}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(o.created_at).toLocaleString()} · {o.items?.length || 0} items
                </div>
                {o.note && <div className="text-xs text-gray-500 mt-1">{o.note}</div>}
              </div>
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[o.status] || "bg-gray-100"}`}>
                {STATUS_LABELS[o.status] || o.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
