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
  ready_for_pickup: "bg-cyan-100 text-cyan-800",
  picked_up: "bg-slate-100 text-slate-600",
};

const STATUS_LABELS: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Inspection Done",
  awaiting_customer_confirmation: "Awaiting Signature",
  confirmed: "✓ Confirmed",
  ready_for_pickup: "Ready for Pickup",
  picked_up: "Picked Up",
};

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "created", label: "Created" },
  { value: "inspection_pending", label: "Inspecting" },
  { value: "inspection_completed", label: "Inspection Done" },
  { value: "awaiting_customer_confirmation", label: "Awaiting Signature" },
  { value: "confirmed", label: "Confirmed" },
  { value: "ready_for_pickup", label: "Ready for Pickup" },
  { value: "picked_up", label: "Picked Up" },
];

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
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-800">Orders</h1>
        <Link to="/orders/new" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
          + New Order
        </Link>
      </div>

      <div className="flex gap-3 mb-4 flex-wrap">
        <input
          placeholder="Search by name or phone..."
          className="flex-1 min-w-[160px] border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : orders.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No orders yet</div>
      ) : (
        <div className="space-y-2">
          {orders.map((order) => (
            <div
              key={order.id}
              onClick={() => nav(`/orders/${order.id}`)}
              className="bg-white border rounded-xl p-4 cursor-pointer hover:border-indigo-300 hover:shadow-sm transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{order.customer?.name}</span>
                    {order.customer?.phone && (
                      <span className="text-xs text-gray-400">{order.customer.phone}</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {new Date(order.created_at).toLocaleString()}
                    {order.items && order.items.length > 0 && (
                      <span className="ml-2">{order.items.length} item{order.items.length > 1 ? "s" : ""}</span>
                    )}
                    {order.note && <span className="ml-2 text-gray-300">· {order.note}</span>}
                  </div>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ml-3 whitespace-nowrap ${STATUS_COLORS[order.status] || "bg-gray-100"}` }>
                  {STATUS_LABELS[order.status] || order.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
