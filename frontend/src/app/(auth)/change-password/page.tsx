"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { API_BASE, fetchWithAuth } from "@/lib/api";

export default function ChangePasswordPage() {
  const router = useRouter();
  const { logout } = useAuth();
  const [form, setForm] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (form.newPassword !== form.confirmPassword) {
      setError("New passwords do not match.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetchWithAuth("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: form.currentPassword,
          new_password: form.newPassword
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error?.message || "Failed to update password.");
      }

      setSuccess(true);
      setTimeout(() => {
        // Log out so they can log in with their new password
        logout();
      }, 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900">
      <div className="p-8 bg-slate-800 rounded-lg shadow-xl w-96 space-y-4">
        <h1 className="text-2xl font-bold text-white text-center">Change Password</h1>
        <p className="text-sm text-slate-400 text-center">
          You must change your password before continuing, as requested by the administrator.
        </p>

        {error && <div className="text-red-500 text-sm text-center">{error}</div>}
        {success && (
          <div className="text-green-500 text-sm text-center font-semibold">
            Password updated successfully! Logging you out to sign in again...
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-300 block mb-1">Temporary/Current Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-slate-700 text-white rounded p-2 outline-none border border-slate-600 focus:border-indigo-500" 
              value={form.currentPassword}
              onChange={e => setForm({...form, currentPassword: e.target.value})}
            />
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">New Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-slate-700 text-white rounded p-2 outline-none border border-slate-600 focus:border-indigo-500" 
              value={form.newPassword}
              onChange={e => setForm({...form, newPassword: e.target.value})}
            />
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">Confirm New Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-slate-700 text-white rounded p-2 outline-none border border-slate-600 focus:border-indigo-500" 
              value={form.confirmPassword}
              onChange={e => setForm({...form, confirmPassword: e.target.value})}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading || success}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-2 rounded transition-colors"
          >
            {loading ? "Updating..." : "Update Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
