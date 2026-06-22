"use client";

import { useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { ChevronDown } from "lucide-react";

export const STATUS_META: Record<string, { label: string; dot: string; text: string }> = {
  ready:     { label: "Ready",     dot: "bg-emerald-500", text: "text-emerald-700" },
  on_call:   { label: "On Call",   dot: "bg-blue-500",    text: "text-blue-700" },
  wrap_up:   { label: "Wrap-up",   dot: "bg-amber-500",   text: "text-amber-700" },
  break:     { label: "Break",     dot: "bg-orange-500",  text: "text-orange-700" },
  lunch:     { label: "Lunch",     dot: "bg-orange-500",  text: "text-orange-700" },
  restroom:  { label: "Restroom",  dot: "bg-slate-400",   text: "text-slate-600" },
  meeting:   { label: "Meeting",   dot: "bg-violet-500",  text: "text-violet-700" },
  offline:   { label: "Offline",   dot: "bg-slate-300",   text: "text-slate-500" },
};

const OPTIONS = ["ready", "wrap_up", "break", "lunch", "restroom", "meeting", "offline"];

export default function AgentStatusControl({ initial }: { initial?: string }) {
  const [status, setStatus] = useState(initial || "offline");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const meta = STATUS_META[status] || STATUS_META.offline;

  const change = async (next: string) => {
    setOpen(false);
    if (next === status) return;
    setBusy(true);
    try {
      const res = await fetchWithAuth("/users/me/status", {
        method: "POST",
        body: JSON.stringify({ status: next }),
      });
      if (res.ok) setStatus((await res.json()).status);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={busy}
        className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-secondary transition-colors disabled:opacity-60"
      >
        <span className={`h-2.5 w-2.5 rounded-full ${meta.dot}`} />
        <span className={meta.text}>{meta.label}</span>
        <ChevronDown size={14} className="text-muted-foreground" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-44 rounded-xl border border-border bg-popover p-1 shadow-lg">
            {OPTIONS.map((s) => {
              const m = STATUS_META[s];
              return (
                <button
                  key={s}
                  onClick={() => change(s)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-secondary transition-colors"
                >
                  <span className={`h-2.5 w-2.5 rounded-full ${m.dot}`} />
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
