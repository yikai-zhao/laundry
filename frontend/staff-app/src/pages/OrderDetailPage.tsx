import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, API_HOST, getCustomerSignBaseUrl } from "../services/api";
import type { Order, OrderItem, Issue } from "../types";

const GARMENT_PRESETS = [
  "Suit Jacket", "Dress Pants", "Shirt", "T-Shirt", "Sweater", "Knit Top",
  "Overcoat", "Trench Coat", "Down Jacket", "Blazer", "Leather Jacket", "Casual Jacket",
  "Dress", "Skirt", "Jeans", "Casual Pants", "Sweatpants",
  "Formal Gown", "Silk Blouse", "Cashmere Sweater", "Linen Shirt", "Other",
];

const ISSUE_TYPES_OPTIONS = [
  { value: "stain", label: "Stain" },
  { value: "tear", label: "Tear" },
  { value: "hole", label: "Hole" },
  { value: "wear", label: "Wear" },
  { value: "wrinkle", label: "Wrinkle" },
  { value: "fade", label: "Fade" },
  { value: "missing_button", label: "Missing Button" },
  { value: "zipper", label: "Zipper Issue" },
  { value: "pilling", label: "Pilling" },
  { value: "other", label: "Other" },
];

const ISSUE_LABEL: Record<string, string> = Object.fromEntries(
  ISSUE_TYPES_OPTIONS.map((o) => [o.value, o.label])
);

const SEV_LABEL: Record<number, string> = { 1: "Minor", 2: "Moderate", 3: "Severe" };
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
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Inspection Done",
  awaiting_customer_confirmation: "Awaiting Signature",
  confirmed: "✓ Confirmed",
  ready_for_pickup: "Ready for Pickup",
  picked_up: "Picked Up",
};

// Status workflow transitions
const NEXT_STATUS: Record<string, { status: string; label: string; color: string }[]> = {
  created: [{ status: "inspection_pending", label: "→ Start Inspection", color: "bg-yellow-500 hover:bg-yellow-600" }],
  inspection_pending: [{ status: "inspection_completed", label: "→ Finish Inspection", color: "bg-blue-500 hover:bg-blue-600" }],
  inspection_completed: [],
  awaiting_customer_confirmation: [{ status: "ready_for_pickup", label: "→ Ready for Pickup", color: "bg-cyan-500 hover:bg-cyan-600" }],
  confirmed: [{ status: "ready_for_pickup", label: "→ Ready for Pickup", color: "bg-cyan-500 hover:bg-cyan-600" }],
  ready_for_pickup: [{ status: "picked_up", label: "→ Mark Picked Up", color: "bg-slate-500 hover:bg-slate-600" }],
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
            <option value={1}>Minor</option>
            <option value={2}>Moderate</option>
            <option value={3}>Severe</option>
          </select>
        </div>
        <input value={pos} onChange={(e) => setPos(e.target.value)} placeholder="Position (e.g. front left chest)" className="border rounded px-2 py-1 w-full" />
        <div className="flex gap-2">
          <button onClick={save} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs">Save</button>
          <button onClick={() => setEditing(false)} className="text-gray-500 text-xs">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-between border rounded-lg p-2.5 text-sm gap-2">
      <div className="flex items-start gap-2 min-w-0 flex-1">
        <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs font-medium ${issue.source === "ai" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}>
          {issue.source === "ai" ? "AI" : "Manual"}
        </span>
        <div className="min-w-0">
          <span className={`font-medium ${SEV_COLOR[issue.severity_level] || ""}`}>
            {ISSUE_LABEL[issue.issue_type] || issue.issue_type}
          </span>
          <span className="text-gray-400 ml-1.5 text-xs">{SEV_LABEL[issue.severity_level] || `Lv.${issue.severity_level}`}</span>
          {issue.position_desc && <p className="text-gray-500 text-xs mt-0.5 truncate">{issue.position_desc}</p>}
          {issue.confidence_score && (
            <span className="text-xs text-gray-300">Conf. {Math.round(issue.confidence_score * 100)}%</span>
          )}
        </div>
      </div>
      <div className="flex gap-2 shrink-0">
        <button onClick={() => setEditing(true)} className="text-indigo-600 text-xs hover:underline">Edit</button>
        <button onClick={onDelete} className="text-red-500 text-xs hover:underline">Delete</button>
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
    pending: "Pending", detecting: "Detecting...", reviewing: "Reviewed", completed: "Complete",
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
          {item.photos.length === 0 && <div className="text-xs text-gray-400 py-4">No photos yet — take a photo or upload</div>}
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
            {uploading ? "Uploading..." : "📷 Camera"}
          </button>
          <button onClick={() => fileRef.current?.click()} disabled={uploading}
            className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-gray-200 transition disabled:opacity-50">
            {uploading ? "Uploading..." : "🖼 Gallery"}
          </button>
          <button onClick={triggerDetect} disabled={detecting || item.photos.length === 0}
            className="bg-purple-100 text-purple-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-purple-200 transition disabled:opacity-50">
            {detecting ? "Detecting..." : "🤖 Re-detect"}
          </button>
        </div>
        {detecting && (
          <div className="flex items-center gap-2 text-xs text-purple-600 mt-1">
            <div className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
            AI is analyzing photos, please wait...
          </div>
        )}
      </div>

      {/* Issues */}
      {item.inspection && item.inspection.issues.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Issues ({item.inspection.issues.length})</h4>
          {item.inspection.issues.map((issue) => (
            <IssueCard key={issue.id} issue={issue} onDelete={() => deleteIssue(issue.id)} onUpdate={() => onRefresh()} />
          ))}
        </div>
      )}
      {item.inspection && item.inspection.issues.length === 0 && item.inspection.status !== "pending" && (
        <p className="text-sm text-green-600">✓ No issues found by AI</p>
      )}

      {/* Add Manual Issue */}
      {item.inspection && (
        <div>
          {!showAddIssue ? (
            <button onClick={() => setShowAddIssue(true)} className="text-xs text-indigo-600 font-medium">+ Add Issue Manually</button>
          ) : (
            <div className="border rounded-lg p-3 bg-gray-50 space-y-2 text-sm">
              <div className="flex gap-2">
                <select value={newType} onChange={(e) => setNewType(e.target.value)} className="border rounded px-2 py-1 flex-1">
                  {ISSUE_TYPES_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <select value={newSev} onChange={(e) => setNewSev(Number(e.target.value))} className="border rounded px-2 py-1 w-24">
                  <option value={1}>Minor</option>
                  <option value={2}>Moderate</option>
                  <option value={3}>Severe</option>
                </select>
              </div>
              <input value={newPos} onChange={(e) => setNewPos(e.target.value)} placeholder="Position (e.g. front left chest)" className="border rounded px-2 py-1 w-full" />
              <div className="flex gap-2">
                <button onClick={addManualIssue} className="bg-indigo-600 text-white px-3 py-1 rounded text-xs">Add</button>
                <button onClick={() => setShowAddIssue(false)} className="text-gray-500 text-xs">Cancel</button>
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

  if (loading) return <div className="text-center py-12 text-gray-400">Loading...</div>;
  if (!order) return <div className="text-center py-12 text-red-500">Order not found</div>;

  const nextStatuses = NEXT_STATUS[order.status] || [];

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4 pb-20">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link to="/orders" className="text-sm text-indigo-600 hover:underline">← Orders</Link>
          <h1 className="text-xl font-bold text-gray-800 mt-1">{order.customer?.name}</h1>
          {order.customer?.phone && (
            <a href={`tel:${order.customer.phone}`} className="text-sm text-indigo-600">{order.customer.phone}</a>
          )}
          <p className="text-xs text-gray-400 mt-0.5">{new Date(order.created_at).toLocaleString()}</p>
          {order.note && <p className="text-sm text-gray-500 mt-1 bg-yellow-50 rounded px-2 py-1">Note: {order.note}</p>}
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
        <h2 className="font-semibold text-gray-700 mb-3">Add Garment</h2>
        <div className="flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[150px] relative">
            <input
              list="garment-presets"
              placeholder="Garment type * (type or select)"
              className="border rounded-lg px-3 py-2 text-sm w-full outline-none focus:ring-2 focus:ring-indigo-500"
              value={garmentType}
              onChange={(e) => setGarmentType(e.target.value)}
            />
            <datalist id="garment-presets">
              {GARMENT_PRESETS.map((p) => <option key={p} value={p} />)}
            </datalist>
          </div>
          <input
            placeholder="Color"
            className="border rounded-lg px-3 py-2 text-sm w-20 outline-none focus:ring-2 focus:ring-indigo-500"
            value={garmentColor}
            onChange={(e) => setGarmentColor(e.target.value)}
          />
          <input
            placeholder="Brand"
            className="border rounded-lg px-3 py-2 text-sm w-20 outline-none focus:ring-2 focus:ring-indigo-500"
            value={garmentBrand}
            onChange={(e) => setGarmentBrand(e.target.value)}
          />
          <button onClick={addGarment} disabled={!garmentType.trim()} className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
            Add
          </button>
        </div>
      </div>

      {/* Garments */}
      {order.items.length === 0 ? (
        <div className="text-center py-8 text-gray-400 text-sm">No garments added yet</div>
      ) : (
        <div className="space-y-3">
          <h2 className="font-semibold text-gray-700">Garments ({order.items.length})</h2>
          {order.items.map((item) => (
            <GarmentCard key={item.id} item={item} onRefresh={load} />
          ))}
        </div>
      )}

      {/* Customer Confirmation */}
      {order.items.length > 0 && (
        <div className="bg-white border rounded-xl p-4">
          <h2 className="font-semibold text-gray-700 mb-3">Customer Confirmation</h2>
          {order.confirmation?.status === "signed" ? (
            <div className="text-center space-y-2">
              <div className="text-green-600 font-semibold text-lg">✓ Signed & Confirmed</div>
              <p className="text-sm text-gray-600">By: {order.confirmation.customer_name}</p>
              <p className="text-xs text-gray-400">{order.confirmation.confirmed_at && new Date(order.confirmation.confirmed_at).toLocaleString()}</p>
              {order.confirmation.signature && (
                <img src={order.confirmation.signature.signature_data} alt="Signature" className="mx-auto border rounded-lg max-h-24 mt-2" />
              )}
            </div>
          ) : qrUrl ? (
            <div className="text-center space-y-3">
              <div className="inline-block p-3 bg-white border-2 rounded-xl">
                <img src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrUrl)}`} alt="QR Code" className="w-52 h-52" />
              </div>
              <p className="text-sm text-gray-500">Customer scans QR to review report & sign</p>
              <p className="text-xs text-gray-300 break-all">{qrUrl}</p>
            </div>
          ) : (
            <button onClick={generateConfirmation} disabled={genLoading} className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition text-sm">
              {genLoading ? "Generating..." : "🔗 Generate Customer QR Code"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
