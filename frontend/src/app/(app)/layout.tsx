"use client";

import { useAuth } from "@/lib/auth";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import {
  LayoutDashboard, Headphones, Ticket, Users, FileText, CreditCard,
  Search, LogOut, BookOpen, ShieldCheck,
} from "lucide-react";
import AgentStatusControl from "@/components/AgentStatusControl";

const NAV = [
  {
    group: "Workspace",
    items: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/contact-center", label: "Contact Center", icon: Headphones },
      { href: "/tickets", label: "Tickets", icon: Ticket },
      { href: "/customers", label: "Customers", icon: Users },
    ],
  },
  {
    group: "Catalog",
    items: [
      { href: "/billing", label: "Billing", icon: CreditCard },
      { href: "/plans", label: "Plans & Addons", icon: FileText },
      { href: "/kb", label: "Knowledge Base", icon: BookOpen },
    ],
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user?.must_change_password) router.push("/change-password");
  }, [user, loading, router]);

  if (loading || !user)
    return (
      <div className="min-h-screen bg-background flex items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const showStatus = user.role === "agent" || user.role === "supervisor";

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 bg-card border-r border-border flex flex-col">
        <div className="px-5 h-16 flex items-center gap-2 border-b border-border">
          <div className="h-8 w-8 rounded-lg bg-foreground text-background grid place-items-center font-bold">T</div>
          <span className="font-semibold tracking-tight">Telecom CRM</span>
        </div>
        <nav className="flex-1 overflow-y-auto scrollbar-thin px-3 py-4 space-y-6">
          {NAV.map((section) => (
            <div key={section.group}>
              <div className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {section.group}
              </div>
              <div className="space-y-0.5">
                {section.items.map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive(href)
                        ? "bg-accent/10 text-accent"
                        : "text-foreground/70 hover:bg-secondary hover:text-foreground"
                    }`}
                  >
                    <Icon size={18} />
                    {label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
          {user.role === "superuser" && (
            <div>
              <div className="px-3 mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Admin
              </div>
              <Link
                href="/users"
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive("/users") ? "bg-accent/10 text-accent" : "text-foreground/70 hover:bg-secondary hover:text-foreground"
                }`}
              >
                <ShieldCheck size={18} /> Manage Users
              </Link>
            </div>
          )}
        </nav>
        <div className="border-t border-border p-3">
          <Link href="/profile" className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-secondary transition-colors">
            <div className="h-9 w-9 rounded-full bg-accent/15 text-accent grid place-items-center text-sm font-semibold">
              {user.full_name?.[0] || "U"}
            </div>
            <div className="min-w-0">
              <div className="truncate text-sm font-medium">{user.full_name}</div>
              <div className="text-xs capitalize text-muted-foreground">{user.role}</div>
            </div>
          </Link>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 shrink-0 border-b border-border bg-card/80 backdrop-blur flex items-center gap-4 px-6">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-2.5 text-muted-foreground" size={16} />
            <input
              type="text"
              placeholder="Search customers, tickets…"
              className="w-full rounded-full border border-border bg-background py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
            />
          </div>
          <div className="ml-auto flex items-center gap-3">
            {showStatus && <AgentStatusControl initial={user.status} />}
            <button
              onClick={logout}
              title="Log out"
              className="rounded-lg p-2 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            >
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-auto scrollbar-thin p-6">{children}</div>
      </main>
    </div>
  );
}
