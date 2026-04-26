import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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
  cancelled: "bg-red-100 text-red-500",
};

const STATUS_LABEL: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Insp. Done",
  awaiting_customer_confirmation: "Awaiting Sig",
  confirmed: "Confirmed",
  ready_for_pickup: "Ready Pickup",
  picked_up: "Picked Up",
  cancelled: "Cancelled",
};

export default function AdminPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<{ id: number; username: string; display_name: string; role: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"dashboard" | "users">("dashboard");

  useEffect(() => {
    Promise.all([
      api.get("/orders").then(({ data }) => setOrders(data)),
      api.get("/users").then(({ data }) => setUsers(data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  const today = new Date().toDateString();
  const todayOrders = orders.filter((o) => new Date(o.created_at).toDateString() === today);
  const pending = orders.filter((o) => o.status === "awaiting_customer_confirmation");
  const confirmed = orders.filter((o) => o.status === "confirmed");
  const readyPickup = orders.filter((o) => o.status === "ready_for_pickup");
  const inProgress = orders.filter((o) =>
    ["inspection_pending", "inspection_completed"].includes(o.status)
  );

  const stats = [
    { count: orders.length, label: "Total Orders", color: "text-gray-800" },
    { count: todayOrders.length, label: "Today", color: "text-blue-600" },
    { count: inProgress.length, label: "In Progress", color: "text-yellow-600" },
    { count: pending.length, label: "Awaiting Sig", color: "text-orange-600" },
    { count: confirmed.length, label: "Confirmed", color: "text-green-600" },
    { count: readyPickup.length, label: "Ready Pickup", color: "text-cyan-600" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="max-w-2xl mx-auto px-4 pt-4 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">Admin</h1>
          <Link to="/orders" className="text-sm text-indigo-600 hover:underline">← Orders</Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b">
          {(["dashboard", "users"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition capitalize ${
                tab === t ? "border-indigo-600 text-indigo-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t === "dashboard" ? "Dashboard" : "Staff"}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-400">Loading...</div>
        ) : tab === "dashboard" ? (
          <>
            {/* Stats grid */}
            <div className="grid grid-cols-3 gap-3">
              {stats.map(({ count, label, color }) => (
                <div key={label} className="bg-white rounded-xl border p-3 text-center">
                  <div className={`text-2xl font-bold ${color}`}>{count}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{label}</div>
                </div>
              ))}
            </div>

            {/* Recent orders */}
            <div className="bg-white rounded-xl border overflow-hidden">
              <div className="px-4 py-3 border-b flex justify-between items-center">
                <h3 className="font-semibold text-gray-700 text-sm">Recent Orders</h3>
                <Link to="/orders" className="text-xs text-indigo-600 hover:underline">View all →</Link>
              </div>
              <div className="divide-y">
                {orders.slice(0, 20).map((order) => (
                  <Link
                    key={order.id}
                    to={`/orders/${order.id}`}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition"
                  >
                    <div>
                      <div className="font-medium text-gray-800 text-sm">
                        {(order as any).customer?.name || `Order #${order.id}`}
                      </div>
                      <div className="text-xs text-gray-400">
                        {(order as any).items?.length || 0} items ·{" "}
                        {new Date(order.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
                      {STATUS_LABEL[order.status] || order.status}
                    </span>
                  </Link>
                ))}
                {orders.length === 0 && (
                  <div className="py-8 text-center text-gray-400 text-sm">No orders yet</div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* Staff management */
          <div className="bg-white rounded-xl border overflow-hidden">
            <div className="px-4 py-3 border-b">
              <h3 className="font-semibold text-gray-700 text-sm">Staff Accounts</h3>
            </div>
            <div className="divide-y">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <div className="font-medium text-gray-800 text-sm">{u.display_name || u.username}</div>
                    <div className="text-xs text-gray-400">@{u.username}</div>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    u.role === "admin" ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-600"
                  }`}>
                    {u.role}
                  </span>
                </div>
              ))}
              {users.length === 0 && (
                <div className="py-8 text-center text-gray-400 text-sm">No users found</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
