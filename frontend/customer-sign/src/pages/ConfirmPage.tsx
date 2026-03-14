import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, API_HOST } from "../services/api";
import type { ConfirmationData } from "../types";
import SignatureCanvas from "../components/SignatureCanvas";

export default function ConfirmPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ConfirmationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [signature, setSignature] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.get(`/confirmations/${token}`)
      .then(({ data }) => setData(data))
      .catch(() => setError("Invalid or expired link"))
      .finally(() => setLoading(false));
  }, [token]);

  const submit = async () => {
    if (!name.trim() || !signature) return;
    setSubmitting(true);
    try {
      await api.post(`/confirmations/${token}/submit`, {
        customer_name: name.trim(),
        signature_data: signature,
      });
      navigate("/success");
    } catch {
      setError("Failed to submit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen text-gray-400">Loading...</div>;
  if (error) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <p className="text-red-500 font-medium">{error}</p>
      </div>
    </div>
  );
  if (!data) return null;
  if (data.status === "signed") return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-5xl mb-4">✅</div>
        <p className="text-green-600 font-semibold text-lg">Already confirmed</p>
        <p className="text-gray-500 text-sm mt-1">by {data.customer_name}</p>
      </div>
    </div>
  );

  const order = data.order;
  const totalIssues = order.items.reduce((sum, item) => sum + (item.inspection?.issues.length || 0), 0);

  return (
    <div className="max-w-lg mx-auto p-4 pb-20 space-y-4">
      {/* Header */}
      <div className="text-center py-4">
        <h1 className="text-xl font-bold text-gray-800">Garment Inspection Report</h1>
        <p className="text-sm text-gray-500 mt-1">Please review and sign below</p>
      </div>

      {/* Order info */}
      <div className="bg-white rounded-xl border p-4">
        <div className="text-sm text-gray-500">Customer: <span className="text-gray-800 font-medium">{order.customer.name}</span></div>
        <div className="text-sm text-gray-500 mt-1">Date: {new Date(order.created_at).toLocaleDateString()}</div>
        {order.note && <div className="text-sm text-gray-500 mt-1">Note: {order.note}</div>}
        <div className="text-sm text-gray-500 mt-1">Items: {order.items.length} · Issues found: {totalIssues}</div>
      </div>

      {/* Garments */}
      {order.items.map((item, idx) => (
        <div key={item.id} className="bg-white rounded-xl border p-4 space-y-3">
          <h3 className="font-semibold capitalize">
            {idx + 1}. {item.garment_type}
            {item.color && <span className="text-gray-400 font-normal"> · {item.color}</span>}
            {item.brand && <span className="text-gray-400 font-normal"> · {item.brand}</span>}
          </h3>

          {/* Photos */}
          {item.photos.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-1">
              {item.photos.map((p) => (
                <img key={p.id} src={`${API_HOST}${p.file_path}`} alt="" className="w-24 h-24 object-cover rounded-lg border flex-shrink-0" />
              ))}
            </div>
          )}

          {/* Issues */}
          {item.inspection?.issues && item.inspection.issues.length > 0 ? (
            <div className="space-y-1.5">
              {item.inspection.issues.map((issue) => (
                <div key={issue.id} className="flex items-center gap-2 text-sm bg-red-50 rounded-lg px-3 py-2">
                  <span className="capitalize font-medium text-red-700">{issue.issue_type}</span>
                  <span className="text-red-400">Lv.{issue.severity_level}</span>
                  <span className="text-red-500">{issue.position_desc}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-green-600">No issues found ✓</p>
          )}
        </div>
      ))}

      {/* Signature section */}
      <div className="bg-white rounded-xl border p-4 space-y-3">
        <h3 className="font-semibold text-gray-700">Your Confirmation</h3>
        <p className="text-xs text-gray-500">By signing, you confirm that you have reviewed the inspection results above and agree with the findings.</p>
        <input
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <SignatureCanvas onSignature={setSignature} />
        <button
          onClick={submit}
          disabled={!name.trim() || !signature || submitting}
          className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
        >
          {submitting ? "Submitting..." : "Confirm & Sign"}
        </button>
      </div>
    </div>
  );
}
