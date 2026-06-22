"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { fetchWithAuth } from "@/lib/api";

export default function ProfilePage() {
  const { user } = useAuth();
  const [form, setForm] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
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
        throw new Error(err.error?.message || "Failed to change password.");
      }

      setSuccess("Password updated successfully!");
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return <div className="text-white">Loading profile...</div>;

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-3xl font-bold text-white">My Profile</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Profile Info Card */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
          <h2 className="text-xl font-semibold text-white">Account Details</h2>
          
          <div className="space-y-3">
            <div>
              <span className="text-xs text-slate-400 block uppercase">Full Name</span>
              <span className="text-lg text-slate-100 font-medium">{user.full_name}</span>
            </div>
            
            <div>
              <span className="text-xs text-slate-400 block uppercase">Username</span>
              <span className="text-lg text-slate-100 font-medium">{user.username}</span>
            </div>

            <div>
              <span className="text-xs text-slate-400 block uppercase">Email Address</span>
              <span className="text-lg text-slate-100 font-medium">{user.email}</span>
            </div>

            <div>
              <span className="text-xs text-slate-400 block uppercase">Role</span>
              <span className="inline-block bg-indigo-900/60 text-indigo-300 border border-indigo-700/50 px-2 py-0.5 rounded text-sm capitalize font-medium">
                {user.role}
              </span>
            </div>

            <div>
              <span className="text-xs text-slate-400 block uppercase">Member Since</span>
              <span className="text-slate-300 text-sm">
                {new Date(user.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </span>
            </div>
          </div>
        </div>

        {/* Change Password Card */}
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
          <h2 className="text-xl font-semibold text-white">Update Password</h2>
          
          {error && <div className="text-red-500 text-sm">{error}</div>}
          {success && <div className="text-green-500 text-sm font-semibold">{success}</div>}

          <form onSubmit={handlePasswordChange} className="space-y-3">
            <div>
              <label className="text-sm text-slate-300 block mb-1">Current Password</label>
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
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-2 rounded transition-colors"
            >
              {loading ? "Updating..." : "Change Password"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
