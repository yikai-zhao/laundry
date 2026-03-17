import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, API_HOST } from "../services/api";
import NavBar from "../components/NavBar";
import type { Order } from "../types";

const STATUS_COLORS: Record<string, string> = {
  created: "bg-gray-100 text-gray-700",
  inspection_pending: "bg-yellow-100 text-yellow-800",
  inspection_completed: "bg-blue-100 text-blue-800",
  awaiting_customer_confirmation: "bg-orange-100 text-orange-800",
  confirmed: "bg-green-100 text-green-800",
};

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api.get(`/orders/${id}`).then(({ data }) => setOrder(data)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>;
  if (!order) return <div className="text-center py-12 text-red-500">Order not found</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />

      <div className="max-w-3xl mx-auto p-6 space-y-4">
        <Link to="/orders" className="text-sm text-indigo-600 hover:underline">← Back to Orders</Link>

        {/* Order Header */}
        <div className="bg-white rounded-xl border p-4 flex justify-between items-start">
          <div>
            <h2 className="text-lg font-bold text-gray-800">Order for {order.customer?.name}</h2>
            <p className="text-sm text-gray-500">{order.customer?.phone}</p>
            <p className="text-xs text-gray-400 mt-1">{new Date(order.created_at).toLocaleString()}</p>
            {order.note && <p className="text-sm text-gray-500 mt-1">{order.note}</p>}
          </div>
          <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
            {order.status.replace(/_/g, " ")}
          </span>
        </div>

        {/* Items */}
        {order.items.map((item, idx) => (
          <div key={item.id} className="bg-white rounded-xl border p-4 space-y-3">
            <h3 className="font-semibold capitalize">
              {idx + 1}. {item.garment_type}
              {item.color && <span className="text-gray-400 font-normal"> · {item.color}</span>}
              {item.brand && <span className="text-gray-400 font-normal"> · {item.brand}</span>}
            </h3>

            {/* Photos */}
            {item.photos.length > 0 && (
              <div className="flex gap-2 overflow-x-auto">
                {item.photos.map((p) => (
                  <img key={p.id} src={`${API_HOST}${p.file_path}`} alt="" className="w-24 h-24 object-cover rounded-lg border flex-shrink-0" />
                ))}
              </div>
            )}

            {/* Issues */}
            {item.inspection && (
              <div>
                <div className="text-sm text-gray-500 mb-1">
                  Inspection: <span className="capitalize font-medium">{item.inspection.status}</span>
                  {item.inspection.issues.length > 0 && ` · ${item.inspection.issues.length} issues`}
                </div>
                {item.inspection.issues.map((issue) => (
                  <div key={issue.id} className="flex items-center gap-2 text-sm bg-red-50 rounded-lg px-3 py-2 mb-1.5">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${issue.source === "ai" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}>
                      {issue.source === "ai" ? "AI" : "Manual"}
                    </span>
                    <span className="capitalize font-medium text-red-700">{issue.issue_type}</span>
                    <span className="text-red-400">Lv.{issue.severity_level}</span>
                    <span className="text-red-500">{issue.position_desc}</span>
                    {issue.confidence_score && <span className="text-xs text-gray-400">({Math.round(issue.confidence_score * 100)}%)</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Confirmation */}
        {order.confirmation && (
          <div className="bg-white rounded-xl border p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Customer Confirmation</h3>
            {order.confirmation.status === "signed" ? (
              <div className="space-y-2">
                <div className="text-green-600 font-semibold">✓ Signed by {order.confirmation.customer_name}</div>
                <div className="text-xs text-gray-400">{order.confirmation.confirmed_at && new Date(order.confirmation.confirmed_at).toLocaleString()}</div>
                {order.confirmation.signature && (
                  <img src={order.confirmation.signature.signature_data} alt="Signature" className="border rounded-lg max-h-24 mt-2" />
                )}
              </div>
            ) : (
              <div className="text-sm text-orange-600">Awaiting customer signature...</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
