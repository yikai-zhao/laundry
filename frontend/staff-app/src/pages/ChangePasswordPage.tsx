import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuthStore } from "../store/auth";

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

export default function ChangePasswordPage() {
  const nav = useNavigate();
  const { user, setAuth, token, logout } = useAuthStore();
  const mustChange = user?.must_change_password ?? false;

  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const isValid = newPw.length >= 8 && /[a-zA-Z]/.test(newPw) && /\d/.test(newPw);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPw !== confirmPw) { setError("New passwords do not match."); return; }
    if (!isValid) { setError("Password does not meet requirements."); return; }
    setError("");
    setLoading(true);
    try {
      const { data } = await api.put("/auth/me/password", {
        old_password: oldPw,
        new_password: newPw,
      });
      // Update stored user
      if (data.user && token) {
        setAuth(token, data.user);
      }
      setSuccess(true);
      setTimeout(() => nav("/orders"), 1500);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail || "Failed to change password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100 p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm space-y-5">
        <div className="text-center">
          <div className="text-3xl mb-2">🔑</div>
          <h1 className="text-xl font-bold text-gray-800">Change Password</h1>
          {mustChange && (
            <p className="text-sm text-amber-600 mt-1 bg-amber-50 px-3 py-2 rounded-xl">
              You must change your password before continuing.
            </p>
          )}
        </div>

        {success ? (
          <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-xl text-center text-sm">
            ✓ Password changed successfully. Redirecting…
          </div>
        ) : (
          <>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl flex gap-2">
                <span className="shrink-0">⚠</span>
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Current Password</label>
              <div className="relative">
                <input
                  type={showOld ? "text" : "password"}
                  autoComplete="current-password"
                  value={oldPw}
                  onChange={(e) => setOldPw(e.target.value)}
                  className="w-full border rounded-xl px-3 py-2.5 pr-10 focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                  required
                />
                <button type="button" tabIndex={-1} onClick={() => setShowOld((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">
                  {showOld ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">New Password</label>
              <div className="relative">
                <input
                  type={showNew ? "text" : "password"}
                  autoComplete="new-password"
                  value={newPw}
                  onChange={(e) => setNewPw(e.target.value)}
                  className="w-full border rounded-xl px-3 py-2.5 pr-10 focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                  required
                />
                <button type="button" tabIndex={-1} onClick={() => setShowNew((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">
                  {showNew ? "Hide" : "Show"}
                </button>
              </div>
              <StrengthBar password={newPw} />
            </div>

            <div className="space-y-1">
              <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                className={`w-full border rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-indigo-500 outline-none text-sm ${confirmPw && newPw !== confirmPw ? "border-red-400" : ""}`}
                required
              />
              {confirmPw && newPw !== confirmPw && (
                <p className="text-xs text-red-500">Passwords do not match</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !isValid || newPw !== confirmPw}
              className="w-full bg-indigo-600 text-white py-2.5 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 transition text-sm"
            >
              {loading ? "Changing…" : "Change Password"}
            </button>

            {!mustChange && (
              <button
                type="button"
                onClick={() => nav(-1)}
                className="w-full text-center text-sm text-gray-500 hover:text-gray-700 py-1"
              >
                Cancel
              </button>
            )}

            {mustChange && (
              <button
                type="button"
                onClick={() => { logout(); nav("/login"); }}
                className="w-full text-center text-sm text-gray-400 hover:text-gray-600 py-1"
              >
                Log out instead
              </button>
            )}
          </>
        )}
      </form>
    </div>
  );
}
