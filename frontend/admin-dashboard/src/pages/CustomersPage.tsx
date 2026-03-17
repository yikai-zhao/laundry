import { useEffect, useState } from "react";
import { api } from "../services/api";
import NavBar from "../components/NavBar";
import type { Customer } from "../types";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/customers", { params: search ? { q: search } : {} })
      .then(({ data }) => setCustomers(data))
      .finally(() => setLoading(false));
  }, [search]);

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />

      <div className="max-w-5xl mx-auto p-6 space-y-4">
        <h2 className="text-2xl font-bold text-gray-800">Customers</h2>

        <input
          placeholder="Search by name or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-full max-w-md outline-none focus:ring-2 focus:ring-slate-400"
        />

        <div className="bg-white rounded-xl border">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : customers.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No customers found</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="p-3 font-medium">Name</th>
                  <th className="p-3 font-medium">Phone</th>
                  <th className="p-3 font-medium">Email</th>
                  <th className="p-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="p-3 font-medium text-gray-800">{c.name}</td>
                    <td className="p-3 text-gray-600">{c.phone || "—"}</td>
                    <td className="p-3 text-gray-600">{c.email || "—"}</td>
                    <td className="p-3 text-gray-400">{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
