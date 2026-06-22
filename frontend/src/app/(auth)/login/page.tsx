"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { API_BASE } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error?.message || "Login failed");
      }
      const data = await res.json();
      login(data);
      router.push("/");
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900">
      <form onSubmit={handleSubmit} className="p-8 bg-slate-800 rounded-lg shadow-xl w-96 space-y-4">
        <h1 className="text-2xl font-bold text-white text-center">Telecom CRM</h1>
        {error && <div className="text-red-500 text-sm">{error}</div>}
        <div>
          <label className="text-sm text-slate-300 block mb-1">Username</label>
          <input 
            type="text" 
            className="w-full bg-slate-700 text-white rounded p-2 outline-none border border-slate-600 focus:border-indigo-500" 
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="text-sm text-slate-300 block mb-1">Password</label>
          <input 
            type="password" 
            className="w-full bg-slate-700 text-white rounded p-2 outline-none border border-slate-600 focus:border-indigo-500" 
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>
        <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 rounded transition-colors">
          Log In
        </button>
        <div className="text-center text-xs text-slate-500">
          Accounts are provisioned by an administrator.
        </div>
      </form>
    </div>
  );
}
