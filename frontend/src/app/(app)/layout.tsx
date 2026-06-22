"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { LayoutDashboard, Ticket, Users, FileText, CreditCard, Search, LogOut } from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
    if (user?.must_change_password) {
      router.push("/change-password");
    }
  }, [user, loading, router]);

  if (loading || !user) return <div className="min-h-screen bg-slate-900 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="flex h-screen bg-slate-900 text-slate-300">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        <div className="p-4 text-xl font-bold text-white border-b border-slate-700">
          Telecom CRM
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <Link href="/" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <LayoutDashboard size={20} /> Dashboard
          </Link>
          <Link href="/tickets" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <Ticket size={20} /> Tickets
          </Link>
          <Link href="/customers" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <Users size={20} /> Customers
          </Link>
          <Link href="/billing" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <CreditCard size={20} /> Billing
          </Link>
          <Link href="/plans" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <FileText size={20} /> Plans & Addons
          </Link>
          <Link href="/kb" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
            <Search size={20} /> Knowledge Base
          </Link>
          {user.role === "superuser" && (
            <Link href="/users" className="flex items-center gap-3 p-2 hover:bg-slate-700 rounded transition-colors text-slate-200">
              <Users size={20} /> Manage Users
            </Link>
          )}
        </nav>
        <div className="p-4 border-t border-slate-700 flex items-center justify-between">
          <Link href="/profile" className="text-sm hover:text-white transition-colors cursor-pointer group">
            <div className="font-semibold text-slate-200 group-hover:text-white">{user.full_name}</div>
            <div className="text-xs text-slate-400 capitalize">{user.role}</div>
          </Link>
          <button onClick={logout} className="text-slate-400 hover:text-white" title="Log Out">
            <LogOut size={20} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-slate-700 bg-slate-800 flex items-center px-8">
          <div className="flex-1">
            <div className="relative w-96">
              <Search className="absolute left-3 top-2.5 text-slate-400" size={16} />
              <input 
                type="text" 
                placeholder="Global search (customers, tickets)..." 
                className="w-full bg-slate-900 border border-slate-700 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-indigo-500 text-white"
              />
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
