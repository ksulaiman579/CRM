"use client";

import { useAuth } from "@/lib/auth";
import { fetchWithAuth, API_BASE } from "@/lib/api";
import { useEffect, useState, useCallback } from "react";
import { format } from "date-fns";
import {
  PhoneIncoming, PhoneCall, PhoneOff, User2, Ticket as TicketIcon,
  Clock, Users, CheckCircle2,
} from "lucide-react";

const INTENT_LABEL: Record<string, string> = {
  billing: "Billing", outage: "Outage / Technical", upgrade: "Upgrade / Sales",
  complaint: "Complaint", general: "General",
};

const WRAP_CODES = [
  { code: "resolved", label: "Resolved", disposition: "completed" },
  { code: "callback", label: "Callback needed", disposition: "completed" },
  { code: "escalated", label: "Escalated", disposition: "completed" },
  { code: "wrong_number", label: "Wrong number", disposition: "abandoned" },
  { code: "other", label: "Other", disposition: "completed" },
];

function StatTile({ icon: Icon, label, value, tint }: any) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm">
      <div className={`mb-3 inline-grid h-9 w-9 place-items-center rounded-xl ${tint}`}>
        <Icon size={18} />
      </div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

export default function ContactCenterPage() {
  const { user } = useAuth();
  const [incoming, setIncoming] = useState<any>(null);
  const [active, setActive] = useState<any>(null);
  const [customer, setCustomer] = useState<any>(null);
  const [myCalls, setMyCalls] = useState<any[]>([]);
  const [queueCount, setQueueCount] = useState(0);
  const [notes, setNotes] = useState("");
  const [wrap, setWrap] = useState("resolved");
  const [raiseTicket, setRaiseTicket] = useState(false);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const [mineRes, queueRes, ringRes] = await Promise.all([
      fetchWithAuth("/calls?scope=mine"),
      fetchWithAuth("/calls?scope=queue"),
      fetchWithAuth("/calls?scope=mine&status=ringing"),
    ]);
    if (mineRes.ok) setMyCalls(await mineRes.json());
    if (queueRes.ok) setQueueCount((await queueRes.json()).length);
    if (ringRes.ok) {
      const r = await ringRes.json();
      if (r.length) setIncoming(r[0]);
    }
    // Resume an in-progress active call if the page was reloaded.
    const activeRes = await fetchWithAuth("/calls?scope=mine&status=active");
    if (activeRes.ok) {
      const a = await activeRes.json();
      if (a.length) { setActive(a[0]); loadCustomer(a[0].customer_id); }
    }
  }, []);

  const loadCustomer = async (cid: number) => {
    const [base, overview] = await Promise.all([
      fetchWithAuth(`/customers/${cid}`),
      fetchWithAuth(`/customers/${cid}/overview`).catch(() => null),
    ]);
    const data: any = base.ok ? await base.json() : {};
    if (overview && overview.ok) data.overview = await overview.json();
    setCustomer(data);
  };

  useEffect(() => { if (user?.id) refresh(); }, [user?.id, refresh]);

  // Live call events.
  useEffect(() => {
    if (!user?.id) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const es = new EventSource(`${API_BASE}/events/stream?token=${token}`);
    es.onmessage = (e) => {
      try {
        const m = JSON.parse(e.data);
        if (m.event === "call_offered" && m.data?.agent_id === user.id) {
          setIncoming(m.data);
        } else if (m.event === "call_queued") {
          setQueueCount((c) => c + 1);
        } else if (m.event === "call_completed") {
          refresh();
        }
      } catch {}
    };
    return () => es.close();
  }, [user?.id, refresh]);

  const answer = async () => {
    if (!incoming) return;
    setBusy(true);
    try {
      const res = await fetchWithAuth(`/calls/${incoming.id}/answer`, { method: "POST" });
      if (res.ok) {
        const call = await res.json();
        setActive(call);
        setIncoming(null);
        setNotes(""); setWrap("resolved"); setRaiseTicket(false);
        loadCustomer(call.customer_id);
      }
    } finally { setBusy(false); }
  };

  const complete = async () => {
    if (!active) return;
    setBusy(true);
    const wc = WRAP_CODES.find((w) => w.code === wrap)!;
    try {
      const res = await fetchWithAuth(`/calls/${active.id}/complete`, {
        method: "POST",
        body: JSON.stringify({
          disposition: wc.disposition,
          raise_ticket: raiseTicket,
          notes: `[${wc.label}] ${notes}`.trim(),
        }),
      });
      if (res.ok) {
        setActive(null); setCustomer(null);
        refresh();
      }
    } finally { setBusy(false); }
  };

  const completedToday = myCalls.filter((c) => c.status === "completed").length;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Contact Center</h1>
          <p className="text-sm text-muted-foreground">
            Set your status to <span className="font-medium text-emerald-700">Ready</span> (top-right) to receive calls.
          </p>
        </div>
        <button
          onClick={async () => { await fetchWithAuth("/calls/generate?mine=true", { method: "POST" }); }}
          className="shrink-0 rounded-xl border border-border bg-card px-4 py-2 text-sm font-medium shadow-sm hover:bg-secondary transition-colors"
          title="Inject a test call into your team's queue"
        >
          Simulate call to me
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile icon={Users} label="Waiting in your team queue" value={queueCount} tint="bg-amber-100 text-amber-700" />
        <StatTile icon={PhoneCall} label="My calls (recent)" value={myCalls.length} tint="bg-blue-100 text-blue-700" />
        <StatTile icon={CheckCircle2} label="Completed" value={completedToday} tint="bg-emerald-100 text-emerald-700" />
        <StatTile icon={Clock} label="Status" value={active ? "On Call" : incoming ? "Ringing" : "Idle"} tint="bg-violet-100 text-violet-700" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Live call column */}
        <div className="lg:col-span-2 space-y-6">
          {incoming && !active && (
            <div className="rounded-2xl border-2 border-emerald-400 bg-emerald-50 p-6 shadow-sm animate-pulse-once">
              <div className="flex items-center gap-3 text-emerald-700">
                <PhoneIncoming className="animate-bounce" />
                <span className="font-semibold">Incoming call</span>
                <span className="ml-auto rounded-full bg-emerald-600 px-2.5 py-0.5 text-xs font-medium text-white">
                  {INTENT_LABEL[incoming.intent] || incoming.intent}
                </span>
              </div>
              <p className="mt-4 text-lg italic text-foreground">“{incoming.opening_line}”</p>
              <p className="mt-2 text-xs text-muted-foreground">
                This call may be recorded for quality and training purposes.
              </p>
              <div className="mt-5 flex gap-3">
                <button onClick={answer} disabled={busy}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 font-medium text-white hover:bg-emerald-700 disabled:opacity-60">
                  <PhoneCall size={18} /> Answer
                </button>
              </div>
            </div>
          )}

          {active && (
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-full bg-blue-100 text-blue-700">
                  <PhoneCall size={18} />
                </span>
                <div>
                  <div className="font-semibold">Active call · {active.call_number}</div>
                  <div className="text-xs text-muted-foreground">
                    {INTENT_LABEL[active.intent] || active.intent} · answered {active.answered_at ? format(new Date(active.answered_at), "p") : "now"}
                  </div>
                </div>
              </div>
              <p className="mt-4 italic text-foreground">“{active.opening_line}”</p>

              <div className="mt-5 space-y-3">
                <div>
                  <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Wrap-up code</label>
                  <div className="flex flex-wrap gap-2">
                    {WRAP_CODES.map((w) => (
                      <button key={w.code} onClick={() => setWrap(w.code)}
                        className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                          wrap === w.code ? "border-accent bg-accent/10 text-accent" : "border-border hover:bg-secondary"
                        }`}>
                        {w.label}
                      </button>
                    ))}
                  </div>
                </div>
                <textarea
                  value={notes} onChange={(e) => setNotes(e.target.value)}
                  placeholder="Call notes…"
                  className="min-h-[90px] w-full rounded-xl border border-border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
                />
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input type="checkbox" checked={raiseTicket} onChange={(e) => setRaiseTicket(e.target.checked)} />
                  Raise a ticket from this call
                </label>
              </div>

              <div className="mt-5 flex gap-3">
                <button onClick={complete} disabled={busy}
                  className="inline-flex items-center gap-2 rounded-xl bg-foreground px-5 py-2.5 font-medium text-background hover:opacity-90 disabled:opacity-60">
                  <PhoneOff size={18} /> Complete call
                </button>
              </div>
            </div>
          )}

          {!incoming && !active && (
            <div className="grid place-items-center rounded-2xl border border-dashed border-border bg-card p-12 text-center">
              <PhoneCall className="mb-3 text-muted-foreground" />
              <div className="font-medium">No active call</div>
              <p className="text-sm text-muted-foreground">Go <span className="text-emerald-700 font-medium">Ready</span> to pull the next call from your team queue.</p>
            </div>
          )}

          {/* Recent calls */}
          <div className="rounded-2xl border border-border bg-card shadow-sm">
            <div className="border-b border-border px-5 py-3 text-sm font-semibold">My recent calls</div>
            <div className="divide-y divide-border">
              {myCalls.length === 0 && <div className="px-5 py-6 text-sm text-muted-foreground">No calls yet.</div>}
              {myCalls.slice(0, 12).map((c) => (
                <div key={c.id} className="flex items-center gap-3 px-5 py-3 text-sm">
                  <span className="font-mono text-xs text-muted-foreground">{c.call_number}</span>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-xs">{INTENT_LABEL[c.intent] || c.intent}</span>
                  <span className="ml-auto capitalize text-muted-foreground">{c.status.replace("_", " ")}</span>
                  {c.ticket_id && <span className="inline-flex items-center gap-1 text-xs text-accent"><TicketIcon size={12} /> #{c.ticket_id}</span>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Screen-pop: Customer 360 */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <User2 size={16} /> Customer
            </div>
            {!customer ? (
              <p className="text-sm text-muted-foreground">Answer a call to screen-pop the customer’s profile.</p>
            ) : (
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-base font-semibold">{customer.first_name} {customer.last_name}</div>
                  <div className="text-xs text-muted-foreground">Acct {customer.account_number}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {customer.segment && (
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      customer.segment === "vip" ? "bg-violet-100 text-violet-700" : "bg-secondary text-foreground/70"
                    }`}>
                      {customer.segment === "vip" ? "★ VIP" : customer.segment}
                    </span>
                  )}
                  {customer.status && <span className="rounded-full bg-secondary px-2 py-0.5 text-xs capitalize">{customer.status}</span>}
                </div>
                <div className="grid grid-cols-2 gap-2 pt-2">
                  <Field label="Phone" value={customer.phone_primary} />
                  <Field label="Email" value={customer.email} />
                </div>
                {customer.overview && (
                  <div className="grid grid-cols-2 gap-2 border-t border-border pt-3">
                    <Field label="Open tickets" value={customer.overview.open_tickets_count ?? customer.overview.open_tickets ?? "—"} />
                    <Field label="Balance" value={customer.overview.outstanding_balance ?? customer.overview.balance ?? "—"} />
                  </div>
                )}
                {customer.id && (
                  <a href={`/customers/${customer.id}`} target="_blank"
                    className="inline-block pt-1 text-xs font-medium text-accent hover:underline">
                    Open full Customer 360 →
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: any }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="truncate font-medium">{value ?? "—"}</div>
    </div>
  );
}
