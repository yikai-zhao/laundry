import { useCallback, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../services/api";
import type { Order } from "../types";

const STATUS_LABEL: Record<string, string> = {
  created: "Created",
  inspection_pending: "In Inspection",
  inspection_completed: "Inspection Done",
  awaiting_customer_confirmation: "Awaiting Signature",
  confirmed: "Customer Confirmed",
  ready_for_pickup: "Ready for Pickup",
  picked_up: "Picked Up",
  cancelled: "Cancelled",
};

export default function ReceiptPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const { data } = await api.get(`/orders/${id}`);
      setOrder(data);
    } catch {
      // order not found
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-gray-400">
        <div className="w-6 h-6 border-2 border-indigo-300 border-t-indigo-600 rounded-full animate-spin mr-2" />
        Loading…
      </div>
    );
  }
  if (!order) return <div className="text-center py-12 text-red-500">Order not found</div>;

  const totalIssues = order.items.reduce((sum, item) => sum + (item.inspection?.issues?.length ?? 0), 0);
  const subtotal = order.items.reduce((sum, item) => sum + (item.unit_price ?? 0), 0);
  const discount = order.discount_amount ?? 0;
  const total = subtotal - discount;

  return (
    <>
      {/* Print/back controls — hidden when printing */}
      <div className="print:hidden flex items-center justify-between px-4 py-3 border-b bg-white max-w-2xl mx-auto">
        <Link to={`/orders/${id}`} className="text-sm text-indigo-600 hover:underline">← Back to Order</Link>
        <button
          onClick={() => window.print()}
          className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition flex items-center gap-2"
        >
          🖨 Print Receipt
        </button>
      </div>

      {/* Receipt body */}
      <div className="max-w-2xl mx-auto px-6 py-8 print:p-0 print:max-w-none">
        {/* Header */}
        <div className="text-center mb-8 border-b pb-6">
          <h1 className="text-2xl font-bold text-gray-900">Laundry Receipt</h1>
          <p className="text-gray-500 text-sm mt-1">{new Date(order.created_at).toLocaleString()}</p>
        </div>

        {/* Customer */}
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Customer</h2>
          <p className="text-lg font-semibold text-gray-900">{order.customer?.name}</p>
          {order.customer?.phone && <p className="text-sm text-gray-600">📞 {order.customer.phone}</p>}
          {order.customer?.email && <p className="text-sm text-gray-600">✉ {order.customer.email}</p>}
        </div>

        {/* Order status */}
        <div className="mb-6 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</span>
          <span className={`text-xs px-3 py-1.5 rounded-full font-semibold ${
            order.status === "cancelled" ? "bg-red-100 text-red-600" :
            order.status === "picked_up" ? "bg-slate-100 text-slate-600" :
            order.status === "confirmed" || order.status === "ready_for_pickup" ? "bg-emerald-100 text-emerald-700" :
            "bg-indigo-100 text-indigo-700"
          }`}>
            {STATUS_LABEL[order.status] || order.status}
          </span>
          <span className={`text-xs px-3 py-1.5 rounded-full font-semibold border ${
            order.pickup_type === "home_pickup"
              ? "bg-blue-50 text-blue-700 border-blue-200"
              : "bg-gray-50 text-gray-600 border-gray-200"
          }`}>
            {order.pickup_type === "home_pickup" ? "🚗 Home Pickup" : "🏪 In-Store"}
          </span>
        </div>

        {/* Payment info */}
        <div className="mb-6 grid grid-cols-2 gap-4 text-sm">
          {order.payment_method && (
            <div>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Payment Method</span>
              <span className="font-medium text-gray-800">
                {order.payment_method === "cash" ? "💵 Cash 现金" :
                 order.payment_method === "card" ? "💳 Card 刷卡" :
                 order.payment_method === "wechat" ? "🟢 WeChat 微信" :
                 order.payment_method === "alipay" ? "🔵 Alipay 支付宝" : order.payment_method}
              </span>
            </div>
          )}
          <div>
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">Payment Status</span>
            <span className={`font-semibold ${
              order.payment_status === "paid" ? "text-emerald-600" :
              order.payment_status === "partial" ? "text-yellow-600" : "text-red-500"
            }`}>
              {order.payment_status === "paid" ? "✓ Paid" :
               order.payment_status === "partial" ? "⚡ Partial" : "⏳ Unpaid"}
            </span>
          </div>
        </div>

        {/* Garment list */}
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Garments ({order.items.length})
          </h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-600">Item</th>
                  <th className="text-left px-4 py-2.5 font-semibold text-gray-600">Service</th>
                  <th className="text-right px-4 py-2.5 font-semibold text-gray-600">Issues</th>
                  <th className="text-right px-4 py-2.5 font-semibold text-gray-600">Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {order.items.map((item, idx) => (
                  <tr key={item.id} className={idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                    <td className="px-4 py-3 align-top">
                      <div className="font-medium text-gray-900">{item.garment_type}</div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {[item.color, item.brand].filter(Boolean).join(", ") || ""}
                        {item.has_lining && " · Lined"}
                      </div>
                      {item.note && <div className="text-xs text-gray-400 mt-0.5">{item.note}</div>}
                    </td>
                    <td className="px-4 py-3 align-top">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        item.service_type === 'dry_clean' ? 'bg-blue-50 text-blue-600' :
                        item.service_type === 'water_wash' ? 'bg-cyan-50 text-cyan-600' :
                        item.service_type === 'luxury_care' ? 'bg-purple-50 text-purple-600' :
                        'bg-orange-50 text-orange-600'
                      }`}>
                        {item.service_type === 'dry_clean' ? 'Dry Clean' :
                         item.service_type === 'water_wash' ? 'Water Wash' :
                         item.service_type === 'luxury_care' ? 'Luxury Care' : 'Repair'}
                      </span>
                      {item.fabric_type && (
                        <div className="text-xs text-gray-400 mt-0.5 capitalize">{item.fabric_type}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center align-top">
                      {item.inspection?.issues && item.inspection.issues.length > 0 ? (
                        <span className="text-xs px-2 py-0.5 bg-orange-50 text-orange-600 border border-orange-200 rounded-full font-medium">
                          {item.inspection.issues.length}
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-600">✓</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900 align-top">
                      ${(item.unit_price ?? 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 border-t-2 border-gray-200">
                {discount > 0 && (
                  <>
                    <tr>
                      <td colSpan={3} className="px-4 py-2 text-gray-500 text-right">Subtotal</td>
                      <td className="px-4 py-2 text-gray-700 text-right">${subtotal.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td colSpan={3} className="px-4 py-2 text-purple-600 text-right">🎁 Discount</td>
                      <td className="px-4 py-2 text-purple-600 text-right">-${discount.toFixed(2)}</td>
                    </tr>
                  </>
                )}
                <tr>
                  <td colSpan={3} className="px-4 py-3 font-bold text-gray-700 text-right">Total</td>
                  <td className="px-4 py-3 font-bold text-gray-900 text-right text-base">${total.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Issues summary */}
        {totalIssues > 0 && (
          <div className="mb-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Issues Found ({totalIssues})
            </h2>
            <div className="space-y-2">
              {order.items.flatMap((item) =>
                (item.inspection?.issues ?? []).map((issue) => (
                  <div key={issue.id} className="flex items-center gap-3 text-sm bg-gray-50 rounded-lg px-3 py-2">
                    <span className="font-medium text-gray-700 w-32 shrink-0">{item.garment_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      issue.severity_level === 3 ? "bg-red-50 text-red-600 border border-red-200" :
                      issue.severity_level === 2 ? "bg-orange-50 text-orange-600 border border-orange-200" :
                      "bg-yellow-50 text-yellow-600 border border-yellow-200"
                    }`}>
                      {issue.severity_level === 3 ? "Severe" : issue.severity_level === 2 ? "Moderate" : "Minor"}
                    </span>
                    <span className="text-gray-600 capitalize">{issue.issue_type.replace("_", " ")}</span>
                    {issue.position_desc && <span className="text-gray-400 text-xs">· {issue.position_desc}</span>}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Signature */}
        {order.confirmation?.status === "signed" && (
          <div className="mb-6">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Customer Signature</h2>
            <div className="border rounded-xl p-4 bg-gray-50 text-center">
              {order.confirmation.signature ? (
                <img src={order.confirmation.signature.signature_data} alt="Signature" className="max-h-24 mx-auto" />
              ) : null}
              <p className="text-sm text-gray-600 mt-2">
                Signed by <strong>{order.confirmation.customer_name}</strong>
                {order.confirmation.confirmed_at && (
                  <span className="text-gray-400 ml-2">on {new Date(order.confirmation.confirmed_at).toLocaleString()}</span>
                )}
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 border-t pt-6 mt-6">
          <p>Thank you for choosing our laundry service.</p>
          <p className="mt-1">Order #{order.id.slice(0, 8).toUpperCase()}</p>
        </div>
      </div>
    </>
  );
}
