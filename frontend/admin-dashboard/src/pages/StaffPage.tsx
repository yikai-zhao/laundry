import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";
import NavBar from "../components/NavBar";

interface StaffUser {
  id: string;
  username: string;
  display_name: string;
  role: string;
  created_at: string;
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-800">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>
        <div className="px-5 py-4 space-y-3">{children}</div>
      </div>
    </div>
  );
}

export default function StaffPage() {
  const [users, setUsers] = useState<StaffUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const currentUser = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  // Add user modal
  const [showAdd, setShowAdd] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newRole, setNewRole] = useState("staff");
  const [addError, setAddError] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Change password modal
  const [changePwUser, setChangePwUser] = useState<StaffUser | null>(null);
  const [newPw, setNewPw] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwLoading, setPwLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/users");
      setUsers(data);
    } catch {
      setError("Failed to load users. Admin access required.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!newUsername.trim() || !newPassword.trim()) return;
    setAddLoading(true);
    setAddError("");
    try {
      await api.post("/users", {
        username: newUsername.trim(),
        password: newPassword,
        display_name: newDisplayName.trim() || newUsername.trim(),
        role: newRole,
      });
      setShowAdd(false);
      setNewUsername("");
      setNewPassword("");
      setNewDisplayName("");
      setNewRole("staff");
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setAddError(err?.response?.data?.detail || "Failed to create user");
    } finally {
      setAddLoading(false);
    }
  };

  const handleChangePw = async () => {
    if (!changePwUser || !newPw.trim()) return;
    setPwLoading(true);
    setPwError("");
    try {
      await api.patch(`/users/${changePwUser.id}/password`, { password: newPw });
      setChangePwUser(null);
      setNewPw("");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setPwError(err?.response?.data?.detail || "Failed to change password");
    } finally {
      setPwLoading(false);
    }
  };

  const handleDelete = async (user: StaffUser) => {
    if (!window.confirm(`Delete user "${user.display_name}" (@${user.username})? This cannot be undone.`)) return;
    try {
      await api.delete(`/users/${user.id}`);
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Failed to delete user");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />

      <div className="max-w-3xl mx-auto p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800">Staff Management</h2>
          <button
            onClick={() => setShowAdd(true)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-indigo-700 transition"
          >
            + Add Staff
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">{error}</div>
        )}

        <div className="bg-white rounded-xl border divide-y">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No users found</div>
          ) : (
            users.map((user) => (
              <div key={user.id} className="flex items-center justify-between p-4 gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0 ${
                    user.role === "admin" ? "bg-red-500" : "bg-indigo-500"
                  }`}>
                    {(user.display_name || user.username).charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{user.display_name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        user.role === "admin" ? "bg-red-100 text-red-700" : "bg-indigo-100 text-indigo-700"
                      }`}>
                        {user.role}
                      </span>
                      {user.id === currentUser?.id && (
                        <span className="text-xs text-gray-400">(you)</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400">@{user.username}</p>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => { setChangePwUser(user); setNewPw(""); setPwError(""); }}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium px-2 py-1 rounded-lg hover:bg-indigo-50 transition"
                  >
                    Change Password
                  </button>
                  {user.id !== currentUser?.id && (
                    <button
                      onClick={() => handleDelete(user)}
                      className="text-xs text-red-400 hover:text-red-600 font-medium px-2 py-1 rounded-lg hover:bg-red-50 transition"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <p className="text-xs text-gray-400">
          Staff can log in to the staff app. Admin accounts have full access to this dashboard.
          Only admins can manage users.
        </p>
      </div>

      {/* Add User Modal */}
      {showAdd && (
        <Modal title="Add New Staff" onClose={() => setShowAdd(false)}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
            <input
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              placeholder="e.g. john_staff"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input
              value={newDisplayName}
              onChange={(e) => setNewDisplayName(e.target.value)}
              placeholder="e.g. John Smith"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password * (min 6 chars)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Secure password"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="staff">Staff</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {addError && <p className="text-red-500 text-sm">{addError}</p>}
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleAdd}
              disabled={addLoading || !newUsername.trim() || !newPassword.trim()}
              className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              {addLoading ? "Adding..." : "Add Staff Member"}
            </button>
            <button onClick={() => setShowAdd(false)} className="px-4 text-gray-500 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </Modal>
      )}

      {/* Change Password Modal */}
      {changePwUser && (
        <Modal title={`Change Password — ${changePwUser.display_name}`} onClose={() => setChangePwUser(null)}>
          <p className="text-sm text-gray-500">Setting new password for @{changePwUser.username}</p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password (min 6 chars)</label>
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              placeholder="Enter new password"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          {pwError && <p className="text-red-500 text-sm">{pwError}</p>}
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleChangePw}
              disabled={pwLoading || !newPw.trim()}
              className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              {pwLoading ? "Updating..." : "Update Password"}
            </button>
            <button onClick={() => setChangePwUser(null)} className="px-4 text-gray-500 border border-gray-200 rounded-xl text-sm hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
