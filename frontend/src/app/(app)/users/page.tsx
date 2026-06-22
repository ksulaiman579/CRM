"use client";

import { useAuth } from "@/lib/auth";
import { fetchWithAuth } from "@/lib/api";
import { useEffect, useState } from "react";

type CrmUser = {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  must_change_password: boolean;
};

const ROLES = ["agent", "supervisor", "superuser"];

export default function UsersPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<CrmUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    const res = await fetchWithAuth("/users");
    if (res.ok) setUsers(await res.json());
    setLoading(false);
  };

  useEffect(() => {
    if (user?.role === "superuser") load();
  }, [user]);

  if (user?.role !== "superuser") {
    return <div className="text-red-400 p-8">Unauthorized. Superuser access only.</div>;
  }

  const toggleActive = async (u: CrmUser) => {
    setError("");
    const res = await fetchWithAuth(`/users/${u.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !u.is_active }),
    });
    if (res.ok) load();
    else setError((await res.json()).error?.message || "Update failed");
  };

  const resetPassword = async (u: CrmUser) => {
    const pw = prompt(`New temporary password for ${u.username}:`);
    if (!pw) return;
    const res = await fetchWithAuth(`/users/${u.id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ new_password: pw }),
    });
    if (res.ok) alert("Password reset. User must change it on next login.");
    else setError((await res.json()).error?.message || "Reset failed");
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Manage Users</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors"
        >
          + Provision User
        </button>
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading…</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-400 border-b border-slate-700">
              <tr>
                <th className="p-3">Name</th>
                <th className="p-3">Username</th>
                <th className="p-3">Email</th>
                <th className="p-3">Role</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-700/50 text-slate-200">
                  <td className="p-3">{u.full_name}</td>
                  <td className="p-3">{u.username}</td>
                  <td className="p-3 text-slate-400">{u.email}</td>
                  <td className="p-3 capitalize">{u.role}</td>
                  <td className="p-3">
                    <span className={u.is_active ? "text-emerald-400" : "text-red-400"}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="p-3 text-right space-x-3">
                    <button onClick={() => resetPassword(u)} className="text-indigo-400 hover:underline">
                      Reset PW
                    </button>
                    <button onClick={() => toggleActive(u)} className="text-amber-400 hover:underline">
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            load();
          }}
          onError={setError}
        />
      )}
    </div>
  );
}

function CreateUserModal({
  onClose,
  onCreated,
  onError,
}: {
  onClose: () => void;
  onCreated: () => void;
  onError: (m: string) => void;
}) {
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    role: "agent",
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetchWithAuth("/users", {
      method: "POST",
      body: JSON.stringify(form),
    });
    if (res.ok) onCreated();
    else onError((await res.json()).error?.message || "Create failed");
  };

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <form onSubmit={submit} className="bg-slate-800 p-6 rounded-lg w-96 space-y-3 border border-slate-700">
        <h2 className="text-xl font-bold text-white">Provision User</h2>
        {["full_name", "username", "email", "password"].map((f) => (
          <input
            key={f}
            type={f === "password" ? "password" : "text"}
            placeholder={f.replace("_", " ")}
            value={(form as any)[f]}
            onChange={set(f)}
            required
            className="w-full bg-slate-700 text-white rounded p-2 border border-slate-600 focus:border-indigo-500 outline-none capitalize"
          />
        ))}
        <select
          value={form.role}
          onChange={set("role")}
          className="w-full bg-slate-700 text-white rounded p-2 border border-slate-600 outline-none"
        >
          {ROLES.map((r) => (
            <option key={r} value={r} className="capitalize">
              {r}
            </option>
          ))}
        </select>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-slate-300 hover:text-white">
            Cancel
          </button>
          <button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold">
            Create
          </button>
        </div>
      </form>
    </div>
  );
}
