import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";
import NavBar from "../components/NavBar";
import type { User } from "../types";

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

function StrengthBar({ password }: { password: string }) {
  const hasLength = password.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasDigit = /\d/.test(password);
  const score = [hasLength, hasLetter, hasDigit].filter(Boolean).length;
  const colors = ["bg-red-400", "bg-yellow-400", "bg-green-500"];
  return (
    <div className="mt-1 space-y-1">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`h-1 flex-1 rounded-full transition-all ${score > i ? colors[score - 1] : "bg-gray-200"}`} />
        ))}
      </div>
      <ul className="text-xs text-gray-500 space-y-0.5">
        <li className={hasLength ? "text-green-600" : ""}>{hasLength ? "✓" : "·"} At least 8 characters</li>
        <li className={hasLetter ? "text-green-600" : ""}>{hasLetter ? "✓" : "·"} Contains a letter</li>
        <li className={hasDigit ? "text-green-600" : ""}>{hasDigit ? "✓" : "·"} Contains a number</li>
      </ul>
    </div>
  );
}

function relativeTime(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function isLocked(user: User): boolean {
  if (!user.locked_until) return false;
  return new Date(user.locked_until) > new Date();
}

function lockRemaining(user: User): string {
  if (!user.locked_until) return "";
  const diff = new Date(user.locked_until).getTime() - Date.now();
  if (diff <= 0) return "";
  const mins = Math.ceil(diff / 60000);
  return mins < 60 ? `${mins}m` : `${Math.ceil(mins / 60)}h`;
}

export default function StaffPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const currentUser = useAuthStore((s) => s.user);

  // Add user modal
  const [showAdd, setShowAdd] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newRole, setNewRole] = useState("staff");
  const [addError, setAddError] = useState("");
  const [addLoading, setAddLoading] = useState(false);

  // Change password modal
  const [changePwUser, setChangePwUser] = useState<User | null>(null);
  const [newPw, setNewPw] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwLoading, setPwLoading] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);

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
        must_change_password: true,
      });
      setShowAdd(false);
      setNewUsername(""); setNewPassword(""); setNewDisplayName(""); setNewRole("staff");
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
    const hasLength = newPw.length >= 8;
    const hasLetter = /[a-zA-Z]/.test(newPw);
    const hasDigit = /\d/.test(newPw);
    if (!hasLength || !hasLetter || !hasDigit) { setPwError("Password must be 8+ chars with a letter and number."); return; }
    setPwLoading(true); setPwError("");
    try {
      await api.patch(`/users/${changePwUser.id}/password`, { password: newPw });
      setChangePwUser(null); setNewPw("");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setPwError(err?.response?.data?.detail || "Failed to change password");
    } finally {
      setPwLoading(false);
    }
  };

  const handleToggleActive = async (user: User) => {
    const action = user.is_active ? "disable" : "enable";
    if (!window.confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} @${user.username}?`)) return;
    try {
      await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || `Failed to ${action} user`);
    }
  };

  const handleUnlock = async (user: User) => {
    try {
      await api.patch(`/users/${user.id}/unlock`);
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Failed to unlock user");
    }
  };

  const handleForceReset = async (user: User) => {
    if (!window.confirm(`Force @${user.username} to change password on next login?`)) return;
    try {
      await api.patch(`/users/${user.id}/force-reset`);
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Failed to force reset");
    }
  };

  const handleDelete = async (user: User) => {
    if (!window.confirm(`Delete user "${user.display_name}" (@${user.username})? This cannot be undone.`)) return;
    try {
      await api.delete(`/users/${user.id}`);
      load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Failed to delete user");
    }
  };

  const pwValid = newPw.length >= 8 && /[a-zA-Z]/.test(newPw) && /\d/.test(newPw);

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />

      <div className="max-w-4xl mx-auto p-6 space-y-5">
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
            users.map((user) => {
              const locked = isLocked(user);
              const remaining = lockRemaining(user);
              const isSelf = user.id === currentUser?.id;
              return (
                <div key={user.id} className={`p-4 flex flex-col sm:flex-row sm:items-center gap-3 ${!user.is_active ? "opacity-60" : ""}`}>
                  {/* Avatar + info */}
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="relative shrink-0">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white ${
                        user.role === "admin" ? "bg-rose-500" : "bg-indigo-500"
                      }`}>
                        {(user.display_name || user.username).charAt(0).toUpperCase()}
                      </div>
                      {!user.is_active && (
                        <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-gray-400 rounded-full border-2 border-white" title="Disabled" />
                      )}
                      {user.is_active && (
                        <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-400 rounded-full border-2 border-white" title="Active" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="font-medium text-gray-900">{user.display_name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          user.role === "admin" ? "bg-rose-100 text-rose-700" : "bg-indigo-100 text-indigo-700"
                        }`}>
                          {user.role}
                        </span>
                        {!user.is_active && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-medium">Disabled</span>
                        )}
                        {locked && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                            🔒 Locked {remaining && `(${remaining})`}
                          </span>
                        )}
                        {user.must_change_password && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
                            ⚠ Must change pw
                          </span>
                        )}
                        {isSelf && <span className="text-xs text-gray-400">(you)</span>}
                      </div>
                      <div className="flex flex-wrap gap-x-3 mt-0.5">
                        <p className="text-xs text-gray-400">@{user.username}</p>
                        <p className="text-xs text-gray-400">Last login: {relativeTime(user.last_login_at)}</p>
                        {user.failed_login_count > 0 && !locked && (
                          <p className="text-xs text-orange-500">{user.failed_login_count} failed attempt{user.failed_login_count > 1 ? "s" : ""}</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-1.5 shrink-0">
                    <button
                      onClick={() => { setChangePwUser(user); setNewPw(""); setPwError(""); setShowNewPw(false); }}
                      className="text-xs text-indigo-600 hover:text-indigo-800 font-medium px-2.5 py-1.5 rounded-lg hover:bg-indigo-50 border border-indigo-100 transition"
                    >
                      🔑 Password
                    </button>
                    {locked && (
                      <button
                        onClick={() => handleUnlock(user)}
                        className="text-xs text-green-600 hover:text-green-800 font-medium px-2.5 py-1.5 rounded-lg hover:bg-green-50 border border-green-100 transition"
                      >
                        🔓 Unlock
                      </button>
                    )}
                    {!user.must_change_password && (
                      <button
                        onClick={() => handleForceReset(user)}
                        className="text-xs text-amber-600 hover:text-amber-800 font-medium px-2.5 py-1.5 rounded-lg hover:bg-amber-50 border border-amber-100 transition"
                      >
                        ↺ Force Reset
                      </button>
                    )}
                    {!isSelf && (
                      <button
                        onClick={() => handleToggleActive(user)}
                        className={`text-xs font-medium px-2.5 py-1.5 rounded-lg border transition ${
                          user.is_active
                            ? "text-gray-500 hover:text-red-600 border-gray-100 hover:bg-red-50 hover:border-red-100"
                            : "text-green-600 hover:text-green-800 border-green-100 hover:bg-green-50"
                        }`}
                      >
                        {user.is_active ? "Disable" : "Enable"}
                      </button>
                    )}
                    {!isSelf && (
                      <button
                        onClick={() => handleDelete(user)}
                        className="text-xs text-red-400 hover:text-red-600 font-medium px-2.5 py-1.5 rounded-lg hover:bg-red-50 border border-red-100 transition"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <p className="text-xs text-gray-400">
          Staff log into the staff app. Admin accounts have full access to this dashboard.
          Accounts are locked after 5 failed login attempts (15 minutes). Admins can unlock or disable accounts.
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
              autoComplete="off"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input
              value={newDisplayName}
              onChange={(e) => setNewDisplayName(e.target.value)}
              placeholder="e.g. John Smith"
              autoComplete="off"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Temporary Password *</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Min 8 chars, with letter and number"
              autoComplete="new-password"
              className="w-full border rounded-xl px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {newPassword && <StrengthBar password={newPassword} />}
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
          <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-xl">
            ⚠ User will be required to change their password on first login.
          </p>
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
          <p className="text-sm text-gray-500">Admin reset for @{changePwUser.username}. Old password not required.</p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <div className="relative">
              <input
                type={showNewPw ? "text" : "password"}
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                placeholder="Min 8 chars, letter + number"
                autoComplete="new-password"
                className="w-full border rounded-xl px-3 py-2.5 pr-10 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button type="button" tabIndex={-1} onClick={() => setShowNewPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">
                {showNewPw ? "Hide" : "Show"}
              </button>
            </div>
            {newPw && <StrengthBar password={newPw} />}
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input type="checkbox" defaultChecked className="rounded" /> Require user to change password on next login
          </label>
          {pwError && <p className="text-red-500 text-sm">{pwError}</p>}
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleChangePw}
              disabled={pwLoading || !pwValid}
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

