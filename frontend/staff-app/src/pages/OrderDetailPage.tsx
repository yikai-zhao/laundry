import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
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
const SEV_BADGE: Record<number, string> = {
  1: "bg-yellow-50 text-yellow-700 border border-yellow-200",
  2: "bg-orange-50 text-orange-700 border border-orange-200",
  3: "bg-red-50 text-red-700 border border-red-200",
};

const STATUS_LABELS: Record<string, string> = {
  created: "Created",
  inspection_pending: "Inspecting",
  inspection_completed: "Insp. Done",
  awaiting_customer_confirmation: "Awaiting Sig",
  confirmed: "Confirmed",
  ready_for_pickup: "Ready Pickup",
  picked_up: "Picked Up",
  cancelled: "Cancelled",
};

const STATUS_STEPS = [
  "created",
  "inspection_pending",
  "inspection_completed",
  "awaiting_customer_confirmation",
  "confirmed",
  "ready_for_pickup",
  "picked_up",
];

const STEP_SHORT = ["New", "Inspect", "Done", "Sig", "✓", "Pack", "Gone"];

const NEXT_STATUS: Record<string, { status: string; label: string; cls: string }[]> = {
  created: [{ status: "inspection_pending", label: "Start Inspection →", cls: "bg-amber-500 hover:bg-amber-600" }],
  inspection_pending: [{ status: "inspection_completed", label: "Finish Inspection →", cls: "bg-blue-600 hover:bg-blue-700" }],
  inspection_completed: [],
  awaiting_customer_confirmation: [{ status: "ready_for_pickup", label: "Mark Ready for Pickup →", cls: "bg-cyan-600 hover:bg-cyan-700" }],
  confirmed: [{ status: "ready_for_pickup", label: "Mark Ready for Pickup →", cls: "bg-cyan-600 hover:bg-cyan-700" }],
  ready_for_pickup: [{ status: "picked_up", label: "Mark Picked Up ✓", cls: "bg-slate-600 hover:bg-slate-700" }],
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
          <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded-lg px-2 py-1.5 flex-1 text-sm">
            {ISSUE_TYPES_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <select value={sev} onChange={(e) => setSev(Number(e.target.value))} className="border rounded-lg px-2 py-1.5 w-28 text-sm">
            <option value={1}>Minor</option>
            <option value={2}>Moderate</option>
            <option value={3}>Severe</option>
          </select>
        </div>
        <input value={pos} onChange={(e) => setPos(e.target.value)} placeholder="Location (e.g. front left chest)" className="border rounded-lg px-3 py-1.5 w-full text-sm" />
        <div className="flex gap-2">
          <button onClick={save} className="bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium">Save</button>
          <button onClick={() => setEditing(false)} className="text-gray-500 text-sm px-2">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between rounded-lg p-2.5 bg-white border gap-2 text-sm">
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <span className={`shrink-0 text-xs px-1.5 py-0.5 rounded font-medium ${issue.source === "ai" ? "bg-violet-100 text-violet-700" : "bg-sky-100 text-sky-700"}`}>
          {issue.source === "ai" ? "AI" : "Manual"}
        </span>
        <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${SEV_BADGE[issue.severity_level] || ""}`}>
          {SEV_LABEL[issue.severity_level]}
        </span>
        <div className="min-w-0">
          <span className="font-medium text-gray-800">{ISSUE_LABEL[issue.issue_type] || issue.issue_type}</span>
          {issue.position_desc && <span className="text-gray-400 ml-1.5">· {issue.position_desc}</span>}
          {issue.confidence_score != null && (
            <span className="text-xs text-gray-300 ml-1">({Math.round(issue.confidence_score * 100)}%)</span>
          )}
        </div>
      </div>
      <div className="flex gap-3 shrink-0">
        <button onClick={() => setEditing(true)} className="text-indigo-600 text-xs hover:underline">Edit</button>
        <button onClick={onDelete} className="text-red-400 text-xs hover:underline">✕</button>
      </div>
    </div>
  );
}

function GarmentCard({ item, onRefresh, onDelete }: { item: OrderItem; onRefresh: () => void; onDelete: () => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [showAddIssue, setShowAddIssue] = useState(false);
  const [newType, setNewType] = useState("stain");
  const [newSev, setNewSev] = useState(1);
  const [newPos, setNewPos] = useState("");
  const [lightbox, setLightbox] = useState<string | null>(null);
  const [editingPrice, setEditingPrice] = useState(false);
  const [priceInput, setPriceInput] = useState(String(item.unit_price ?? 0));

  const savePrice = async () => {
    const price = parseFloat(priceInput) || 0;
    await api.patch(`/order-items/${item.id}`, { unit_price: price });
    setEditingPrice(false);
    onRefresh();
  };

  const uploadPhotos = async (files: FileList) => {
    setUploading(true);
    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      await api.post(`/order-items/${item.id}/photos`, form);
    }
    setUploading(false);
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

  const inspStatus = item.inspection?.status;
  const issues = item.inspection?.issues || [];

  return (
    <>
      {lightbox && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4" onClick={() => setLightbox(null)}>
          <img src={lightbox} alt="" className="max-w-full max-h-full rounded-lg" onClick={(e) => e.stopPropagation()} />
          <button className="absolute top-4 right-4 text-white text-2xl font-light" onClick={() => setLightbox(null)}>✕</button>
        </div>
      )}

      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
        {/* Garment header */}
        <div className="flex items-start justify-between px-4 pt-4 pb-3 border-b border-gray-50">
          <div>
            <h3 className="font-semibold text-gray-900 text-base">{item.garment_type}</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {[item.color, item.brand].filter(Boolean).join(" · ") || "No color / brand specified"}
              {item.note && ` · ${item.note}`}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {editingPrice ? (
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500 font-medium">$</span>
                <input
                  autoFocus
                  type="number"
                  min="0"
                  step="0.01"
                  value={priceInput}
                  onChange={(e) => setPriceInput(e.target.value)}
                  onBlur={savePrice}
                  onKeyDown={(e) => { if (e.key === "Enter") savePrice(); if (e.key === "Escape") setEditingPrice(false); }}
                  className="w-20 border rounded-lg px-2 py-1 text-sm text-right focus:ring-2 focus:ring-green-400 outline-none"
                />
              </div>
            ) : (
              <button
                onClick={() => { setPriceInput(String(item.unit_price ?? 0)); setEditingPrice(true); }}
                title="Click to set price"
                className="text-xs px-2.5 py-1 rounded-full font-medium bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 transition"
              >
                ${(item.unit_price ?? 0).toFixed(2)}
              </button>
            )}
            {inspStatus && (
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                inspStatus === "completed" ? "bg-emerald-50 text-emerald-600 border border-emerald-200" :
                inspStatus === "detecting" ? "bg-violet-50 text-violet-600 border border-violet-200" :
                inspStatus === "reviewing" ? "bg-blue-50 text-blue-600 border border-blue-200" :
                "bg-gray-100 text-gray-500"
              }`}>
                {inspStatus === "completed" ? "✓ Scanned" :
                 inspStatus === "detecting" ? "⏳ Scanning…" :
                 inspStatus === "reviewing" ? "Reviewed" : "Pending"}
              </span>
            )}
            <button
              onClick={onDelete}
              title="Remove this garment"
              className="text-gray-300 hover:text-red-500 transition text-base leading-none ml-1"
            >
              🗑
            </button>
          </div>
        </div>

        {/* Photos */}
        <div className="px-4 py-3">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {item.photos.map((p) => (
              <button key={p.id} onClick={() => setLightbox(`${API_HOST}${p.file_path}`)} className="shrink-0">
                <img src={`${API_HOST}${p.file_path}`} alt="" className="w-20 h-20 rounded-xl object-cover border border-gray-100 hover:opacity-90 transition" />
              </button>
            ))}
            {item.photos.length === 0 && (
              <div className="w-full text-center py-4 text-xs text-gray-400">No photos yet — use Camera or Gallery below</div>
            )}
          </div>

          {/* Upload buttons */}
          <input ref={cameraRef} type="file" accept="image/*" capture="environment" className="hidden"
            onChange={(e) => e.target.files && uploadPhotos(e.target.files)} />
          <input ref={fileRef} type="file" accept="image/*" multiple className="hidden"
            onChange={(e) => e.target.files && uploadPhotos(e.target.files)} />

          <div className="flex gap-2 mt-3 flex-wrap">
            <button onClick={() => cameraRef.current?.click()} disabled={uploading || detecting}
              className="flex items-center gap-1.5 bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 shadow-sm">
              <span>📷</span> {uploading ? "Uploading…" : "Camera"}
            </button>
            <button onClick={() => fileRef.current?.click()} disabled={uploading || detecting}
              className="flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-xl text-sm font-medium hover:bg-gray-50 transition disabled:opacity-50">
              <span>🖼</span> Gallery
            </button>
            <button onClick={triggerDetect} disabled={detecting || item.photos.length === 0}
              className="flex items-center gap-1.5 bg-violet-50 border border-violet-200 text-violet-700 px-4 py-2 rounded-xl text-sm font-medium hover:bg-violet-100 transition disabled:opacity-50 ml-auto">
              <span>🤖</span> {detecting ? "Analyzing…" : "Re-detect"}
            </button>
          </div>

          {detecting && (
            <div className="flex items-center gap-2 mt-2 text-xs text-violet-600 bg-violet-50 rounded-lg px-3 py-2">
              <div className="w-3 h-3 border-2 border-violet-400 border-t-violet-700 rounded-full animate-spin shrink-0" />
              AI is analyzing garment photos…
            </div>
          )}
        </div>

        {/* Issues */}
        {issues.length > 0 && (
          <div className="px-4 pb-3 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold text-gray-700">Issues Found ({issues.length})</h4>
            </div>
            {issues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} onDelete={() => deleteIssue(issue.id)} onUpdate={() => onRefresh()} />
            ))}
          </div>
        )}

        {item.inspection && issues.length === 0 && inspStatus !== "pending" && !detecting && (
          <div className="px-4 pb-3">
            <div className="text-sm text-emerald-600 bg-emerald-50 rounded-lg px-3 py-2 border border-emerald-100">
              ✓ No issues detected — garment looks good
            </div>
          </div>
        )}

        {/* Manual issue */}
        {item.inspection && (
          <div className="px-4 pb-4">
            {!showAddIssue ? (
              <button onClick={() => setShowAddIssue(true)}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
                <span className="text-base leading-none">+</span> Add Issue Manually
              </button>
            ) : (
              <div className="border border-indigo-100 rounded-xl p-3 bg-indigo-50/40 space-y-2">
                <div className="flex gap-2">
                  <select value={newType} onChange={(e) => setNewType(e.target.value)}
                    className="border rounded-lg px-2 py-1.5 text-sm flex-1 bg-white">
                    {ISSUE_TYPES_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <select value={newSev} onChange={(e) => setNewSev(Number(e.target.value))}
                    className="border rounded-lg px-2 py-1.5 text-sm w-28 bg-white">
                    <option value={1}>Minor</option>
                    <option value={2}>Moderate</option>
                    <option value={3}>Severe</option>
                  </select>
                </div>
                <input value={newPos} onChange={(e) => setNewPos(e.target.value)}
                  placeholder="Location (e.g. front left chest)"
                  className="border rounded-lg px-3 py-1.5 w-full text-sm bg-white" />
                <div className="flex gap-2">
                  <button onClick={addManualIssue}
                    className="bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700">
                    Add
                  </button>
                  <button onClick={() => setShowAddIssue(false)} className="text-gray-500 text-sm">Cancel</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [garmentType, setGarmentType] = useState("");
  const [garmentColor, setGarmentColor] = useState("");
  const [garmentBrand, setGarmentBrand] = useState("");
  const [garmentNote, setGarmentNote] = useState("");
  const [garmentPrice, setGarmentPrice] = useState("0");
  const [qrUrl, setQrUrl] = useState("");
  const [genLoading, setGenLoading] = useState(false);
  const [showAddGarment, setShowAddGarment] = useState(false);
  const [cancelling, setCancelling] = useState(false);

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
      note: garmentNote || null,
      unit_price: parseFloat(garmentPrice) || 0,
    });
    setGarmentType("");
    setGarmentColor("");
    setGarmentBrand("");
    setGarmentNote("");
    setGarmentPrice("0");
    setShowAddGarment(false);
    load();
  };

  const deleteGarment = async (itemId: string) => {
    if (!confirm("Remove this garment from the order?")) return;
    await api.delete(`/order-items/${itemId}`);
    load();
  };

  const cancelOrder = async () => {
    if (!confirm("Cancel this order? This cannot be undone if the order has been picked up.")) return;
    setCancelling(true);
    try {
      await api.post(`/orders/${id}/cancel`);
      navigate("/orders");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Could not cancel order");
      setCancelling(false);
    }
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-gray-400">
        <div className="w-8 h-8 border-2 border-indigo-300 border-t-indigo-600 rounded-full animate-spin mb-3" />
        Loading order…
      </div>
    );
  }
  if (!order) return <div className="text-center py-12 text-red-500">Order not found</div>;

  const stepIdx = STATUS_STEPS.indexOf(order.status);
  const nextStatuses = NEXT_STATUS[order.status] || [];

  return (
    <div className="max-w-2xl mx-auto pb-28">
      {/* Status timeline */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center overflow-x-auto">
          {STATUS_STEPS.map((step, idx) => {
            const done = idx < stepIdx;
            const current = idx === stepIdx;
            return (
              <div key={step} className="flex items-center shrink-0">
                <div className="flex flex-col items-center">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    done ? "bg-indigo-600 text-white" :
                    current ? "bg-indigo-600 text-white ring-4 ring-indigo-100 scale-110" :
                    "bg-gray-100 text-gray-400"
                  }`}>
                    {done ? "✓" : idx + 1}
                  </div>
                  <div className={`mt-1 text-center leading-tight w-10 ${
                    current ? "text-indigo-600 font-semibold" :
                    done ? "text-gray-500" : "text-gray-300"
                  }`} style={{ fontSize: "9px" }}>
                    {STEP_SHORT[idx]}
                  </div>
                </div>
                {idx < STATUS_STEPS.length - 1 && (
                  <div className={`h-0.5 w-4 mx-0.5 mb-4 shrink-0 transition-colors ${idx < stepIdx ? "bg-indigo-600" : "bg-gray-200"}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Customer info */}
      <div className="px-4 pt-4 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <Link to="/orders" className="text-xs text-indigo-500 hover:underline flex items-center gap-1 mb-1">
              ← All Orders
            </Link>
            <h1 className="text-xl font-bold text-gray-900">{order.customer?.name}</h1>
            {order.customer?.phone && (
              <a href={`tel:${order.customer.phone}`} className="text-sm text-indigo-600 flex items-center gap-1 mt-0.5">
                📞 {order.customer.phone}
              </a>
            )}
            {order.customer?.email && (
              <p className="text-xs text-gray-400 mt-0.5">✉ {order.customer.email}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">{new Date(order.created_at).toLocaleString()}</p>
          </div>
          <div className="text-right shrink-0 space-y-2">
            <span className={`inline-block text-xs px-3 py-1.5 rounded-full font-semibold ${
              order.status === "cancelled" ? "bg-red-100 text-red-600" :
              order.status === "picked_up" ? "bg-slate-100 text-slate-600" :
              order.status === "confirmed" || order.status === "ready_for_pickup" ? "bg-emerald-100 text-emerald-700" :
              order.status === "awaiting_customer_confirmation" ? "bg-orange-100 text-orange-700" :
              "bg-indigo-100 text-indigo-700"
            }`}>
              {STATUS_LABELS[order.status] || order.status}
            </span>
            {order.items.length > 0 && (
              <div className="text-right">
                <span className="text-base font-bold text-gray-900">${(order.total_price ?? 0).toFixed(2)}</span>
                <span className="text-xs text-gray-400 ml-1">total</span>
              </div>
            )}
            <div className="flex gap-2 justify-end">
              {order.status !== "cancelled" && order.status !== "picked_up" && (
                <button
                  onClick={cancelOrder}
                  disabled={cancelling}
                  className="text-xs px-2.5 py-1 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 transition disabled:opacity-50"
                >
                  {cancelling ? "…" : "Cancel Order"}
                </button>
              )}
              <Link
                to={`/orders/${id}/receipt`}
                className="text-xs px-2.5 py-1 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition"
              >
                🖨 Receipt
              </Link>
            </div>
          </div>
        </div>
        {order.note && (
          <div className="mt-2 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2 text-sm text-amber-800">
            📝 {order.note}
          </div>
        )}
      </div>

      {/* Garments */}
      <div className="px-4 pb-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-gray-800 text-base">
            Garments {order.items.length > 0 && <span className="text-gray-400 font-normal text-sm">({order.items.length})</span>}
          </h2>
          <button
            onClick={() => setShowAddGarment((v) => !v)}
            className="text-sm text-indigo-600 font-medium flex items-center gap-1 hover:text-indigo-800"
          >
            <span className="text-lg leading-none">+</span> Add Garment
          </button>
        </div>

        {/* Add garment form */}
        {showAddGarment && (
          <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-4 space-y-3">
            <div className="relative">
              <input
                list="garment-presets"
                placeholder="Garment type (required)"
                className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={garmentType}
                onChange={(e) => setGarmentType(e.target.value)}
              />
              <datalist id="garment-presets">
                {GARMENT_PRESETS.map((p) => <option key={p} value={p} />)}
              </datalist>
            </div>
            <div className="flex gap-2">
              <input
                placeholder="Color"
                className="border rounded-xl px-3 py-2.5 text-sm flex-1 outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={garmentColor}
                onChange={(e) => setGarmentColor(e.target.value)}
              />
              <input
                placeholder="Brand"
                className="border rounded-xl px-3 py-2.5 text-sm flex-1 outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={garmentBrand}
                onChange={(e) => setGarmentBrand(e.target.value)}
              />
            </div>
            <input
              placeholder="Note (optional)"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              value={garmentNote}
              onChange={(e) => setGarmentNote(e.target.value)}
            />
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500 font-medium shrink-0">Price ($)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                className="border rounded-xl px-3 py-2.5 text-sm w-28 outline-none focus:ring-2 focus:ring-indigo-500 bg-white text-right"
                value={garmentPrice}
                onChange={(e) => setGarmentPrice(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <button onClick={addGarment} disabled={!garmentType.trim()}
                className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
                Add Garment
              </button>
              <button onClick={() => setShowAddGarment(false)}
                className="px-4 text-gray-500 text-sm rounded-xl border border-gray-200 hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        )}

        {order.items.length === 0 && !showAddGarment && (
          <div className="text-center py-10 text-gray-400 text-sm bg-gray-50 rounded-2xl">
            <div className="text-3xl mb-2">👕</div>
            No garments added yet.<br />Tap "+ Add Garment" to start.
          </div>
        )}

        {order.items.map((item) => (
          <GarmentCard key={item.id} item={item} onRefresh={load} onDelete={() => deleteGarment(item.id)} />
        ))}
      </div>

      {/* Customer Confirmation / QR */}
      {order.items.length > 0 && (
        <div className="px-4 pb-4">
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-4">
            <h2 className="font-bold text-gray-800 text-base mb-3">Customer Confirmation</h2>
            {order.confirmation?.status === "signed" ? (
              <div className="text-center space-y-2">
                <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full font-semibold text-sm border border-emerald-200">
                  ✓ Signed & Confirmed
                </div>
                <p className="text-sm text-gray-600">By: <strong>{order.confirmation.customer_name}</strong></p>
                <p className="text-xs text-gray-400">
                  {order.confirmation.confirmed_at && new Date(order.confirmation.confirmed_at).toLocaleString()}
                </p>
                {order.confirmation.signature && (
                  <div className="border rounded-xl p-2 inline-block bg-gray-50 mt-2">
                    <img src={order.confirmation.signature.signature_data} alt="Signature" className="max-h-20" />
                  </div>
                )}
              </div>
            ) : qrUrl ? (
              <div className="text-center space-y-3">
                <div className="inline-block p-3 bg-white border-2 border-gray-100 rounded-2xl shadow-sm">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrUrl)}`}
                    alt="QR Code"
                    className="w-52 h-52"
                  />
                </div>
                <p className="text-sm text-gray-600 font-medium">Show QR to customer to sign</p>
                <p className="text-xs text-gray-400 break-all">{qrUrl}</p>
              </div>
            ) : (
              <button
                onClick={generateConfirmation}
                disabled={genLoading}
                className="w-full bg-emerald-600 text-white py-3 rounded-xl font-semibold hover:bg-emerald-700 disabled:opacity-50 transition flex items-center justify-center gap-2 text-sm"
              >
                <span>📱</span> {genLoading ? "Generating…" : "Generate Customer QR Code"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Sticky action footer */}
      {nextStatuses.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 shadow-lg px-4 py-3 z-40">
          <div className="max-w-2xl mx-auto flex gap-2">
            {nextStatuses.map((n) => (
              <button
                key={n.status}
                onClick={() => updateStatus(n.status)}
                className={`flex-1 text-white py-3 rounded-xl font-semibold text-sm transition shadow-sm ${n.cls}`}
              >
                {n.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Send for signature (when inspection is done) */}
      {order.status === "inspection_completed" && order.items.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 shadow-lg px-4 py-3 z-40">
          <div className="max-w-2xl mx-auto">
            {!qrUrl ? (
              <button
                onClick={generateConfirmation}
                disabled={genLoading}
                className="w-full bg-emerald-600 text-white py-3 rounded-xl font-semibold text-sm hover:bg-emerald-700 disabled:opacity-50 transition shadow-sm"
              >
                <span className="mr-2">📱</span>
                {genLoading ? "Generating QR…" : "Send to Customer for Signature"}
              </button>
            ) : (
              <div className="text-center text-sm text-gray-500">
                QR code generated above — awaiting customer signature
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
