import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, API_HOST, getCustomerSignBaseUrl } from "../services/api";
import type { Order, OrderItem, Issue } from "../types";

const GARMENT_PRESETS = [
  "西装上衣", "西裤", "衬衫", "T恤", "毛衣", "针织衫",
  "大衣", "风衣", "羽绒服", "夹克", "皮衣", "休闲外套",
  "连衣裙", "半裙", "牛仔裤", "休闲裤", "运动裤",
  "礼服", "旗袍", "羊绒衫", "丝绸衬衫", "其他",
];

const ISSUE_TYPES_OPTIONS = [
  { value: "stain", label: "污渍" },
  { value: "tear", label: "撕裂" },
  { value: "hole", label: "破洞" },
  { value: "wear", label: "磨损" },
  { value: "wrinkle", label: "褶皱" },
  { value: "fade", label: "褪色" },
  { value: "missing_button", label: "缺扣子" },
  { value: "zipper", label: "拉链问题" },
  { value: "pilling", label: "起球" },
  { value: "other", label: "其他" },
];

const ISSUE_LABEL: Record<string, string> = Object.fromEntries(
  ISSUE_TYPES_OPTIONS.map((o) => [o.value, o.label])
);

const SEV_LABEL: Record<number, string> = { 1: "轻微", 2: "中等", 3: "严重" };
const SEV_COLOR: Record<number, string> = {
  1: "text-yellow-600",
  2: "text-orange-600",
  3: "text-red-600",
};

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
  created: "已创建",
  inspection_pending: "验衣中",
  inspection_completed: "验衣完成",
  awaiting_customer_confirmation: "等待客户签字",
  confirmed: "✓ 已确认",
  ready_for_pickup: "可取衣",
  picked_up: "已取走",
};

// Status workflow transitions
const NEXT_STATUS: Record<string, { status: string; label: string; color: string }[]> = {
  created: [{ status: "inspection_pending", label: "→ 开始验衣", color: "bg-yellow-500 hover:bg-yellow-600" }],
  inspection_pending: [{ status: "inspection_completed", label: "→ 完成验衣", color: "bg-blue-500 hover:bg-blue-600" }],
  inspection_completed: [],
  awaiting_customer_confirmation: [{ status: "ready_for_pickup", label: "→ 通知可取衣", color: "bg-cyan-500 hover:bg-cyan-600" }],
  confirmed: [{ status: "ready_for_pickup", label: "→ 通知可取衣", color: "bg-cyan-500 hover:bg-cyan-600" }],
  ready_for_pickup: [{ status: "picked_up", label: "→ 确认已取走", color: "bg-slate-500 hover:bg-slate-600" }],
  picked_up: [],
};

function IssueCard({ issue, onDelete, onUpdate }: { issue: Issue; onDelete: () => void; onUpdate: (i: Issue) => void }) {
  const [editing, setEditing] = useState(false);
  const [type, setType] = useState(issue.issue_type);
  const [sev, setSev] = useState(issue.severity_level);
  const [pos, setPos] = useState(issue.position_desc);

  const save = async () => {
    const { data } = await api.put(`/issues/${issue.id}`, { issue_type: type, severity_level: sev, position_desc: pos });
    onUpdate(data);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="border rounded-lg p-3 bg-gray-50 space-y-2 text-sm">
        <div className="flex gap-2">
          <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded px-2 py-1 flex-1">
            {ISSUE_TYPES_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <select value={sev} onChange={(e) => setSev(Number(e.target.value))} className="border rounded px-2 py-1 w-24">
            <option value={1}>轻微</option>
            <option value={2}>中等</option>
            <option value={3}>严重</option>
          </select>
        </div>
        <input value={pos} onChange={(e) => setPos(e.target.value)} placeholder="位置描述（如：前胸左侧）" className="border rounded px-2 py-1 w-full" />
        <div className="flex gap-2">
          <button onClick={save} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs">保存</button>
          <button onClick={() => setEditing(false)} className="text-gray-500 text-xs">取消</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between border rounded-lg p-2.5 text-sm gap-2">
      <div className="flex items-start gap-2 min-w-0 flex-1">
        <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs font-medium ${issue.source === "ai" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}>
          {issue.source === "ai" ? "AI" : "手动"}
        </span>
        <div className="min-w-0">
          <span className={`font-medium ${SEV_COLOR[issue.severity_level] || ""}`}>
            {ISSUE_LABEL[issue.issue_type] || issue.issue_type}
          </span>
          <span className="text-gray-400 ml-1.5 text-xs">{SEV_LABEL[issue.severity_level] || `Lv.${issue.severity_level}`}</span>
          {issue.position_desc && <p className="text-gray-500 text-xs mt-0.5 truncate">{issue.position_desc}</p>}
          {issue.confidence_score && (
            <span className="text-xs text-gray-300">置信度 {Math.round(issue.confidence_score * 100)}%</span>
          )}
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <button onClick={() => setEditing(true)} className="text-indigo-600 text-xs hover:underline">编辑</button>
        <button onClick={onDelete} className="text-red-500 text-xs hover:underline">删除</button>
      </div>
    </div>
  );
}

function GarmentCard({ item, onRefresh }: { item: OrderItem; onRefresh: () => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [showAddIssue, setShowAddIssue] = useState(false);
  const [newType, setNewType] = useState("stain");
  const [newSev, setNewSev] = useState(1);
  const [newPos, setNewPos] = useState("");

  const uploadPhotos = async (files: FileList) => {
    setUploading(true);
    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      await api.post(`/order-items/${item.id}/photos`, form);
    }
    setUploading(false);
    // Auto-detect after uploading if no issues yet
    if (!item.inspection || item.inspection.issues.length === 0) {
      await triggerDetectAuto();
    } else {
      onRefresh();
    }
  };

  const triggerDetectAuto = async () => {
    setDetecting(true);
    try {
      const { data: insp } = await api.post(`/order-items/${item.id}/inspection`);
      await api.post(`/inspections/${insp.id}/detect`);
    } catch (e) {
      console.error(e);
    } finally {
      setDetecting(false);
      onRefresh();
    }
  };

  const triggerDetect = async () => {
    setDetecting(true);
    try {
      const { data: insp } = await api.post(`/order-items/${item.id}/inspection`);
      await api.post(`/inspections/${insp.id}/detect`);
    } catch (e) {
      console.error(e);
    } finally {
      setDetecting(false);
      onRefresh();
    }
  };

  const deleteIssue = async (issueId: string) => {
    await api.delete(`/issues/${issueId}`);
    onRefresh();
  };

  const addManualIssue = async () => {
    if (!item.inspection) return;
    await api.post(`/inspections/${item.inspection.id}/issues`, {
      issue_type: newType,
      severity_level: newSev,
      position_desc: newPos,
    });
    setShowAddIssue(false);
    setNewPos("");
    onRefresh();
  };

  const INSP_STATUS_LABELS: Record<string, string> = {
    pending: "待检测", detecting: "检测中...", reviewing: "已检测", completed: "已完成",
  };

  return (
    <div className="bg-white border rounded-xl p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{item.garment_type}</h3>
          <p className="text-xs text-gray-500">
            {[item.color, item.brand].filter(Boolean).join(" · ") || "—"}
            {item.note && ` · ${item.note}`}
          </p>
        </div>
        {item.inspection && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            item.inspection.status === "reviewing" ? "bg-yellow-100 text-yellow-700" :
            item.inspection.status === "completed" ? "bg-green-100 text-green-700" :
            item.inspection.status === "detecting" ? "bg-purple-100 text-purple-700" :
            "bg-gray-100 text-gray-600"
          }`}>
            {INSP_STATUS_LABELS[item.inspection.status] || item.inspection.status}
          </span>
        )}
      </div>

      {/* Photos */}
      <div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {item.photos.map((p) => (
            <img key={p.id} src={`${API_HOST}${p.file_path}`} alt="" className="w-20 h-20 rounded-lg object-cover border flex-shrink-0" />
          ))}
          {item.photos.length === 0 && <div className="text-xs text-gray-400 py-4">暂无照片，请拍照或上传</div>}
        </div>
        <div className="flex gap-2 mt-2 flex-wrap">
          {/* Camera capture (mobile) */}
          <input ref={cameraRef} type="file" accept="image/*" capture="environment" className="hidden"
            onChange={(e) => e.target.files && uploadPhotos(e.target.files)} />
          {/* Gallery / file picker */}
          <input ref={fileRef} type="file" accept="image/*" multiple className="hidden"
            onChange={(e) => e.target.files && uploadPhotos(e.target.files)} />
          <button onClick={() => cameraRef.current?.click()} disabled={uploading}
            className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-indigo-700 transition disabled:opacity-50">
            {uploading ? "上传中..." : "📷 拍照"}
          </button>
          <button onClick={() => fileRef.current?.click()} disabled={uploading}
            className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-gray-200 transition disabled:opacity-50">
            {uploading ? "上传中..." : "🖼 选图片"}
          </button>
          <button onClick={triggerDetect} disabled={detecting || item.photos.length === 0}
            className="bg-purple-100 text-purple-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-purple-200 transition disabled:opacity-50">
            {detecting ? "AI检测中..." : "🤖 重新检测"}
          </button>
        </div>
        {detecting && (
          <div className="flex items-center gap-2 text-xs text-purple-600 mt-1">
            <div className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
            AI正在分析照片，请稍候...
          </div>
        )}
      </div>

      {/* Issues */}
      {item.inspection && item.inspection.issues.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">问题清单 ({item.inspection.issues.length})</h4>
          {item.inspection.issues.map((issue) => (
            <IssueCard key={issue.id} issue={issue} onDelete={() => deleteIssue(issue.id)} onUpdate={() => onRefresh()} />
          ))}
        </div>
      )}
      {item.inspection && item.inspection.issues.length === 0 && item.inspection.status !== "pending" && (
        <p className="text-sm text-green-600">✓ AI检测未发现问题</p>
      )}

      {/* Add Manual Issue */}
      {item.inspection && (
        <div>
          {!showAddIssue ? (
            <button onClick={() => setShowAddIssue(true)} className="text-xs text-indigo-600 font-medium">+ 手动添加问题</button>
          ) : (
            <div className="border rounded-lg p-3 bg-gray-50 space-y-2 text-sm">
              <div className="flex gap-2">
                <select value={newType} onChange={(e) => setNewType(e.target.value)} className="border rounded px-2 py-1 flex-1">
                  {ISSUE_TYPES_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <select value={newSev} onChange={(e) => setNewSev(Number(e.target.value))} className="border rounded px-2 py-1 w-24">
                  <option value={1}>轻微</option>
                  <option value={2}>中等</option>
                  <option value={3}>严重</option>
                </select>
              </div>
              <input value={newPos} onChange={(e) => setNewPos(e.target.value)} placeholder="位置描述（如：前胸左侧）" className="border rounded px-2 py-1 w-full" />
              <div className="flex gap-2">
                <button onClick={addManualIssue} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs">添加</button>
                <button onClick={() => setShowAddIssue(false)} className="text-gray-500 text-xs">取消</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [garmentType, setGarmentType] = useState("");
  const [garmentColor, setGarmentColor] = useState("");
  const [garmentBrand, setGarmentBrand] = useState("");
  const [qrUrl, setQrUrl] = useState("");
  const [genLoading, setGenLoading] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const { data } = await api.get(`/orders/${id}`);
      setOrder(data);
      if (data.confirmation?.token) {
        setQrUrl(`${getCustomerSignBaseUrl()}/confirm/${data.confirmation.token}`);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const addGarment = async () => {
    if (!garmentType.trim()) return;
    await api.post(`/orders/${id}/items`, {
      garment_type: garmentType,
      color: garmentColor || null,
      brand: garmentBrand || null,
    });
    setGarmentType("");
    setGarmentColor("");
    setGarmentBrand("");
    load();
  };

  const generateConfirmation = async () => {
    setGenLoading(true);
    try {
      const { data } = await api.post(`/orders/${id}/confirmation`);
      setQrUrl(`${getCustomerSignBaseUrl()}/confirm/${data.token}`);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setGenLoading(false);
    }
  };

  const updateStatus = async (status: string) => {
    await api.patch(`/orders/${id}/status`, { status });
    load();
  };

  if (loading) return <div className="text-center py-12 text-gray-400">加载中...</div>;
  if (!order) return <div className="text-center py-12 text-red-500">订单不存在</div>;

  const nextStatuses = NEXT_STATUS[order.status] || [];

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 pb-20">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link to="/orders" className="text-sm text-indigo-600 hover:underline">← 订单列表</Link>
          <h1 className="text-xl font-bold text-gray-800 mt-1">{order.customer?.name}</h1>
          {order.customer?.phone && (
            <a href={`tel:${order.customer.phone}`} className="text-sm text-indigo-600">{order.customer.phone}</a>
          )}
          <p className="text-xs text-gray-400 mt-0.5">{new Date(order.created_at).toLocaleString("zh-CN")}</p>
          {order.note && <p className="text-sm text-gray-500 mt-1 bg-yellow-50 rounded px-2 py-1">备注：{order.note}</p>}
        </div>
        <div className="shrink-0 text-right space-y-1">
          <span className={`text-xs px-3 py-1 rounded-full font-medium block ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
            {STATUS_LABELS[order.status] || order.status}
          </span>
          {nextStatuses.map((n) => (
            <button key={n.status} onClick={() => updateStatus(n.status)}
              className={`text-xs text-white px-2 py-1 rounded-full block w-full ${n.color} transition`}>
              {n.label}
            </button>
          ))}
        </div>
      </div>

      {/* Add Garment */}
      <div className="bg-white border rounded-xl p-4">
        <h2 className="font-semibold text-gray-700 mb-3">添加衣物</h2>
        <div className="flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[150px] relative">
            <input
              list="garment-presets"
              placeholder="衣物类型 *（可输入或选择）"
              className="border rounded-lg px-3 py-2 text-sm w-full outline-none focus:ring-2 focus:ring-indigo-500"
              value={garmentType}
              onChange={(e) => setGarmentType(e.target.value)}
            />
            <datalist id="garment-presets">
              {GARMENT_PRESETS.map((p) => <option key={p} value={p} />)}
            </datalist>
          </div>
          <input
            placeholder="颜色"
            className="border rounded-lg px-3 py-2 text-sm w-20 outline-none focus:ring-2 focus:ring-indigo-500"
            value={garmentColor}
            onChange={(e) => setGarmentColor(e.target.value)}
          />
          <input
            placeholder="品牌"
            className="border rounded-lg px-3 py-2 text-sm w-20 outline-none focus:ring-2 focus:ring-indigo-500"
            value={garmentBrand}
            onChange={(e) => setGarmentBrand(e.target.value)}
          />
          <button onClick={addGarment} disabled={!garmentType.trim()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
            添加
          </button>
        </div>
      </div>

      {/* Garments */}
      {order.items.length === 0 ? (
        <div className="text-center py-8 text-gray-400 text-sm">暂无衣物，请在上方添加</div>
      ) : (
        <div className="space-y-3">
          <h2 className="font-semibold text-gray-700">衣物清单（{order.items.length} 件）</h2>
          {order.items.map((item) => (
            <GarmentCard key={item.id} item={item} onRefresh={load} />
          ))}
        </div>
      )}

      {/* Customer Confirmation */}
      {order.items.length > 0 && (
        <div className="bg-white border rounded-xl p-4">
          <h2 className="font-semibold text-gray-700 mb-3">客户确认签字</h2>
          {order.confirmation?.status === "signed" ? (
            <div className="text-center space-y-2">
              <div className="text-green-600 font-semibold text-lg">✓ 已签字确认</div>
              <p className="text-sm text-gray-600">客户：{order.confirmation.customer_name}</p>
              <p className="text-xs text-gray-400">{order.confirmation.confirmed_at && new Date(order.confirmation.confirmed_at).toLocaleString("zh-CN")}</p>
              {order.confirmation.signature && (
                <img src={order.confirmation.signature.signature_data} alt="签名" className="mx-auto border rounded-lg max-h-24 mt-2" />
              )}
            </div>
          ) : qrUrl ? (
            <div className="text-center space-y-3">
              <div className="inline-block p-3 bg-white border-2 rounded-xl">
                <img src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrUrl)}`} alt="二维码" className="w-52 h-52" />
              </div>
              <p className="text-sm text-gray-500">请客户扫码查看检衣报告并签字</p>
              <p className="text-xs text-gray-300 break-all">{qrUrl}</p>
            </div>
          ) : (
            <button onClick={generateConfirmation} disabled={genLoading} className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition text-sm">
              {genLoading ? "生成中..." : "🔗 生成客户签字二维码"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
