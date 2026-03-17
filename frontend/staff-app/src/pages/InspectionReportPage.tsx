import { useCallback, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, API_HOST } from "../services/api";
import type { Order, Issue } from "../types";
import AnnotatedPhoto from "../components/AnnotatedPhoto";

const ISSUE_LABEL: Record<string, string> = {
  stain: "Stain", hole: "Hole", tear: "Tear", wear: "Wear",
  wrinkle: "Wrinkle", fade: "Fade", missing_button: "Missing Button",
  zipper: "Zipper Issue", pilling: "Pilling", other: "Other",
};
const SEV_LABEL: Record<number, string> = { 1: "Minor", 2: "Moderate", 3: "Severe" };
const SEV_COLOR: Record<number, string> = {
  1: "bg-yellow-100 text-yellow-800",
  2: "bg-orange-100 text-orange-800",
  3: "bg-red-100 text-red-800",
};

export default function InspectionReportPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const { data } = await api.get(`/orders/${id}`);
      setOrder(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh] text-gray-400">Loading…</div>;
  if (!order) return <div className="text-center py-12 text-red-500">Order not found</div>;

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 print:p-0">
      <div className="flex items-center justify-between mb-4 print:hidden">
        <Link to={`/orders/${id}`} className="text-indigo-600 text-sm hover:underline">← Back to Order</Link>
        <button onClick={() => window.print()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700">
          🖨 Print Report
        </button>
      </div>

      <div className="bg-white border rounded-2xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="bg-indigo-600 text-white px-6 py-4">
          <h1 className="text-lg font-bold">Inspection Report</h1>
          <p className="text-indigo-200 text-sm mt-1">Order: {order.id.slice(0, 8)}… · {new Date(order.created_at).toLocaleString()}</p>
        </div>

        {/* Customer info */}
        <div className="px-6 py-4 border-b">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Customer:</span>
              <span className="ml-2 font-medium">{order.customer?.name}</span>
            </div>
            <div>
              <span className="text-gray-500">Phone:</span>
              <span className="ml-2 font-medium">{order.customer?.phone || "—"}</span>
            </div>
            <div>
              <span className="text-gray-500">Status:</span>
              <span className="ml-2 font-medium capitalize">{order.status.replace(/_/g, " ")}</span>
            </div>
            <div>
              <span className="text-gray-500">Total:</span>
              <span className="ml-2 font-medium">${(order.total_price ?? 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Garments */}
        {order.items.map((item, idx) => {
          const issues: Issue[] = item.inspection?.issues || [];
          const inspector = item.inspection?.inspector;

          return (
            <div key={item.id} className="border-b last:border-b-0 px-6 py-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {idx + 1}. {item.garment_type}
                  </h3>
                  <p className="text-xs text-gray-400">
                    {[item.color, item.brand].filter(Boolean).join(" · ")}
                    {item.note && ` · ${item.note}`}
                  </p>
                </div>
                <span className="text-sm font-medium text-gray-700">${(item.unit_price ?? 0).toFixed(2)}</span>
              </div>

              {/* Inspector info */}
              {inspector && (
                <div className="text-xs text-gray-500 mb-2">
                  Inspector: <span className="font-medium">{inspector.display_name || inspector.username}</span>
                  {item.inspection?.created_at && (
                    <span className="ml-2">· {new Date(item.inspection.created_at).toLocaleString()}</span>
                  )}
                </div>
              )}

              {/* Photos with annotation overlay */}
              {item.photos.length > 0 && (
                <div className="flex gap-2 flex-wrap mb-3">
                  {item.photos.map((p) => (
                    <AnnotatedPhoto
                      key={p.id}
                      src={`${API_HOST}${p.file_path}`}
                      issues={issues}
                      className="w-32 h-32 rounded-lg border overflow-hidden"
                    />
                  ))}
                </div>
              )}

              {/* Issues table */}
              {issues.length > 0 ? (
                <div className="border rounded-lg overflow-hidden text-sm">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium text-gray-600">Type</th>
                        <th className="text-left px-3 py-2 font-medium text-gray-600">Severity</th>
                        <th className="text-left px-3 py-2 font-medium text-gray-600">Position</th>
                        <th className="text-left px-3 py-2 font-medium text-gray-600">Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {issues.map((iss) => (
                        <tr key={iss.id} className="border-t">
                          <td className="px-3 py-2">{ISSUE_LABEL[iss.issue_type] || iss.issue_type}</td>
                          <td className="px-3 py-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SEV_COLOR[iss.severity_level] || ""}`}>
                              {SEV_LABEL[iss.severity_level]}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-gray-600">{iss.position_desc || "—"}</td>
                          <td className="px-3 py-2">
                            <span className={`text-xs px-1.5 py-0.5 rounded ${iss.source === "ai" ? "bg-violet-100 text-violet-700" : "bg-sky-100 text-sky-700"}`}>
                              {iss.source === "ai" ? "AI" : "Manual"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-emerald-600 bg-emerald-50 rounded-lg px-3 py-2 border border-emerald-100">
                  ✓ No issues detected
                </div>
              )}
            </div>
          );
        })}

        {/* Signature */}
        {order.confirmation?.status === "signed" && order.confirmation.signature && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex items-center gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">Customer Signature</p>
                <p className="text-xs text-gray-400">
                  Signed by {order.confirmation.customer_name}
                  {order.confirmation.confirmed_at && ` on ${new Date(order.confirmation.confirmed_at).toLocaleString()}`}
                </p>
              </div>
              <div className="border rounded-lg p-2 bg-white">
                <img src={order.confirmation.signature.signature_data} alt="Signature" className="max-h-16" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
