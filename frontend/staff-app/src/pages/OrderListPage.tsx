import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Order } from "../types";

const STATUS_COLORS: Record<string, string> = {
  created: "bg-gray-100 text-gray-600 border border-gray-200",
  inspection_pending: "bg-amber-50 text-amber-700 border border-amber-200",
  inspection_completed: "bg-blue-50 text-blue-700 border border-blue-200",
  awaiting_customer_confirmation: "bg-orange-50 text-orange-700 border border-orange-200",
  confirmed: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  ready_for_pickup: "bg-cyan-50 text-cyan-700 border border-cyan-200",
  picked_up: "bg-slate-50 text-slate-500 border border-slate-200",
};

const STATUS_DOT: Record<string, string> = {
  created: "bg-gray-400",
  inspection_pending: "bg-amber-400",
  inspection_completed: "bg-blue-500",
  awaiting_customer_confirmation: "bg-orange-500",
  confirmed: "bg-emerald-500",
  ready_for_pickup: "bg-cyan-500",
  picked_up: "bg-slate-400",
};

const STATUS_LABELS: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Insp. Done",
  awaiting_customer_confirmation: "Awaiting Sig",
  confirmed: "Confirmed",
  ready_for_pickup: "Ready Pickup",
  picked_up: "Picked Up",
};

const FILTER_TABS = [
  { value: "", label: "All" },
  { value: "created", label: "Created" },
  { value: "inspection_pending", label: "Inspecting" },
  { value: "inspection_completed", label: "Done" },
  { value: "awaiting_customer_confirmation", label: "Awaiting Sig" },
  { value: "confirmed", label: "Confirmed" },
  { value: "ready_for_pickup", label: "Pickup" },
  { value: "picked_up", label: "Done" },
];

function relativeTime(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 172800) return "Yesterday";
  return new Date(dateStr).toLocaleDateString();
}

export default function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [allOrders, setAllOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const [filtered, all] = await Promise.all([
        api.get("/orders", { params: { ...(search ? { q: search } : {}), ...(statusFilter ? { status: statusFilter } : {}) } }),
        search || statusFilter ? api.get("/orders") : Promise.resolve(null),
      ]);
      setOrders(filtered.data);
      setAllOrders(all ? all.data : filtered.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, statusFilter]);

  const today = new Date().toDateString();
  const todayCount = allOrders.filter((o) => new Date(o.created_at).toDateString() === today).length;
  const awaitSig = allOrders.filter((o) => o.status === "awaiting_customer_confirmation").length;
  const readyPickup = allOrders.filter((o) => o.status === "ready_for_pickup").length;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Quick stats */}
      <div className="bg-indigo-700 px-4 py-3 flex divide-x divide-indigo-600">
        {[
          { count: allOrders.length, label: "Total" },
          { count: todayCount, label: "Today" },
          { count: awaitSig, label: "Awaiting Sig", alert: awaitSig > 0 },
          { count: readyPickup, label: "Pickup", alert: readyPickup > 0 },
        ].map(({ count, label, alert }) => (
          <div key={label} className="flex-1 text-center px-2">
            <div className={`text-xl font-bold ${alert ? "text-yellow-300" : "text-white"}`}>{count}</div>
            <div className="text-indigo-300 text-xs mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Search + New */}
      <div className="px-4 pt-4 pb-2 flex gap-2">
        <div className="flex-1 relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            placeholder="Search name or phone..."
            className="w-full border rounded-xl pl-9 pr-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white shadow-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Link
          to="/orders/new"
          className="bg-indigo-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 transition shadow-sm whitespace-nowrap flex items-center gap-1"
        >
          <span className="text-lg leading-none">+</span> New
        </Link>
      </div>

      {/* Status filter chips */}
      <div className="px-4 pb-3 flex gap-2 overflow-x-auto no-scrollbar">
        {FILTER_TABS.slice(0, 7).map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition ${
              statusFilter === tab.value
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-white border border-gray-200 text-gray-600 hover:border-indigo-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="px-4 pb-8 space-y-2">
        {loading ? (
          <div className="flex flex-col items-center py-16 text-gray-400">
            <div className="w-6 h-6 border-2 border-indigo-300 border-t-indigo-600 rounded-full animate-spin mb-3" />
            Loading orders...
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">🧥</div>
            <p className="font-medium">No orders found</p>
            {(search || statusFilter) && (
              <button onClick={() => { setSearch(""); setStatusFilter(""); }} className="mt-2 text-sm text-indigo-600 hover:underline">
                Clear filters
              </button>
            )}
          </div>
        ) : (
          orders.map((order) => (
            <div
              key={order.id}
              onClick={() => nav(`/orders/${order.id}`)}
              className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-indigo-200 cursor-pointer transition-all duration-150 overflow-hidden"
            >
              <div className="flex">
                {/* Left status accent bar */}
                <div className={`w-1 flex-shrink-0 ${STATUS_DOT[order.status] || "bg-gray-300"}`} />
                <div className="flex-1 p-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline gap-2">
                        <span className="font-semibold text-gray-900 text-base truncate">{order.customer?.name}</span>
                        {order.customer?.phone && (
                          <span className="text-xs text-gray-400 shrink-0">{order.customer.phone}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-gray-400">{relativeTime(order.created_at)}</span>
                        {order.items && order.items.length > 0 && (
                          <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                            {order.items.length} item{order.items.length !== 1 ? "s" : ""}
                          </span>
                        )}
                        {order.note && (
                          <span className="text-xs text-gray-400 truncate max-w-[100px]">· {order.note}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${STATUS_COLORS[order.status] || "bg-gray-100 text-gray-600"}`}>
                        {STATUS_LABELS[order.status] || order.status}
                      </span>
                      {order.status === "awaiting_customer_confirmation" && (
                        <span className="text-xs text-orange-500 font-medium animate-pulse">⏳ Needs sig</span>
                      )}
                      {order.status === "ready_for_pickup" && (
                        <span className="text-xs text-cyan-600 font-medium">📦 Ready</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
