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

  const ISSUE_LABEL: Record<string, string> = {
    stain: "污渍", tear: "撕裂", hole: "破洞", wear: "磨损",
    wrinkle: "褶皱", fade: "褪色", missing_button: "缺扣子",
    zipper: "拉链问题", pilling: "起球", other: "其他",
  };
  const SEV_LABEL: Record<number, string> = { 1: "轻微", 2: "中等", 3: "严重" };
  const SEV_COLOR: Record<number, string> = { 1: "text-yellow-600 bg-yellow-50", 2: "text-orange-600 bg-orange-50", 3: "text-red-600 bg-red-50" };

  if (loading) return <div className="flex items-center justify-center min-h-screen text-gray-400">加载中...</div>;
  if (error) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <p className="text-red-500 font-medium">{error === "Invalid or expired link" ? "链接无效或已过期" : error}</p>
      </div>
    </div>
  );
  if (!data) return null;
  if (data.status === "signed") return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-5xl mb-4">✅</div>
        <p className="text-green-600 font-semibold text-lg">已完成签字确认</p>
        <p className="text-gray-500 text-sm mt-1">{data.customer_name}</p>
      </div>
    </div>
  );

  const order = data.order;
  const totalIssues = order.items.reduce((sum, item) => sum + (item.inspection?.issues.length || 0), 0);

  return (
    <div className="max-w-lg mx-auto p-4 pb-20 space-y-4">
      {/* Header */}
      <div className="text-center py-4">
        <h1 className="text-xl font-bold text-gray-800">🧥 验衣检查报告</h1>
        <p className="text-sm text-gray-500 mt-1">请仔细查阅下方验衣结果，确认无误后签字</p>
      </div>

      {/* Order info */}
      <div className="bg-white rounded-xl border p-4">
        <div className="text-sm text-gray-500">客户：<span className="text-gray-800 font-medium">{order.customer.name}</span></div>
        <div className="text-sm text-gray-500 mt-1">日期：{new Date(order.created_at).toLocaleDateString("zh-CN")}</div>
        {order.note && <div className="text-sm text-gray-500 mt-1">备注：{order.note}</div>}
        <div className="text-sm text-gray-500 mt-1">共 {order.items.length} 件衣物 · 发现 {totalIssues} 个问题</div>
      </div>

      {/* Garments */}
      {order.items.map((item, idx) => (
        <div key={item.id} className="bg-white rounded-xl border p-4 space-y-3">
          <h3 className="font-semibold">
            {idx + 1}. {item.garment_type || "衣物"}
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
                <div key={issue.id} className={`text-sm rounded-lg px-3 py-2 ${SEV_COLOR[issue.severity_level] ?? "bg-red-50 text-red-700"}`}>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{ISSUE_LABEL[issue.issue_type] ?? issue.issue_type}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-white bg-opacity-60 font-semibold">{SEV_LABEL[issue.severity_level] ?? ""}</span>
                  </div>
                  {issue.position_desc && <div className="text-xs mt-0.5 opacity-75">{issue.position_desc}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-green-600">✓ 未发现问题</p>
          )}
        </div>
      ))}

      {/* Signature section */}
      <div className="bg-white rounded-xl border p-4 space-y-3">
        <h3 className="font-semibold text-gray-700">客户签字确认</h3>
        <p className="text-xs text-gray-500">签字即代表您已查阅以上验衣报告，并确认检测结果无误。</p>
        <input
          placeholder="您的姓名"
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
          {submitting ? "提交中..." : "确认签字"}
        </button>
      </div>
    </div>
  );
}
