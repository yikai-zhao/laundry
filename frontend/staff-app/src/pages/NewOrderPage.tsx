import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { Customer } from "../types";

export default function NewOrderPage() {
  const nav = useNavigate();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Customer | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/customers", { params: { q: search } }).then((r) => setCustomers(r.data));
  }, [search]);

  const createCustomer = async () => {
    if (!newName.trim()) return;
    const { data } = await api.post("/customers", { name: newName, phone: newPhone || null });
    setSelected(data);
    setShowNew(false);
  };

  const createOrder = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      const { data } = await api.post("/orders", { customer_id: selected.id, note: note || null });
      nav(`/orders/${data.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto p-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">New Order</h1>

      {/* Customer Selection */}
      <div className="bg-white border rounded-xl p-4 mb-4">
        <h2 className="font-semibold text-gray-700 mb-3">Select Customer</h2>
        {selected ? (
          <div className="flex items-center justify-between bg-indigo-50 p-3 rounded-lg">
            <div>
              <div className="font-medium">{selected.name}</div>
              {selected.phone && <div className="text-xs text-gray-500">{selected.phone}</div>}
            </div>
            <button onClick={() => setSelected(null)} className="text-sm text-indigo-600">Change</button>
          </div>
        ) : (
          <>
            <input
              placeholder="Search by name or phone..."
              className="w-full border rounded-lg px-3 py-2 text-sm mb-2 outline-none focus:ring-2 focus:ring-indigo-500"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="max-h-40 overflow-y-auto space-y-1 mb-2">
              {customers.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelected(c)}
                  className="p-2 rounded-lg cursor-pointer hover:bg-indigo-50 text-sm flex justify-between"
                >
                  <span>{c.name}</span>
                  <span className="text-gray-400">{c.phone}</span>
                </div>
              ))}
            </div>
            {!showNew ? (
              <button onClick={() => setShowNew(true)} className="text-sm text-indigo-600 font-medium">
                + New Customer
              </button>
            ) : (
              <div className="border-t pt-3 space-y-2">
                <input
                  placeholder="Customer name *"
                  className="w-full border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
                <input
                  placeholder="Phone number"
                  className="w-full border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                />
                <div className="flex gap-2">
                  <button onClick={createCustomer} className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm">Save</button>
                  <button onClick={() => setShowNew(false)} className="text-sm text-gray-500">Cancel</button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Order Note */}
      <div className="bg-white border rounded-xl p-4 mb-4">
        <h2 className="font-semibold text-gray-700 mb-3">Note (optional)</h2>
        <textarea
          className="w-full border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          rows={2}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Special instructions or notes..."
        />
      </div>

      <button
        onClick={createOrder}
        disabled={!selected || loading}
        className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 disabled:opacity-50 transition"
      >
        {loading ? "Creating..." : "Create Order"}
      </button>
    </div>
  );
}
