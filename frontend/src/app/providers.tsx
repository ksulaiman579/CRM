"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";

interface Toast {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (title: string, message: string, type: Toast["type"]) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  useEffect(() => {
    let eventSource: EventSource | null = null;
    
    // Periodically monitor local storage to establish or destroy EventSource connection dynamically
    const tokenCheckInterval = setInterval(() => {
      const token = localStorage.getItem("access_token");
      if (token && !eventSource) {
        const sseUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1"}/events/stream?token=${token}`;
        eventSource = new EventSource(sseUrl);
        
        eventSource.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            // Only surface events we have a meaningful message for; ignore the rest
            // (call_queued, agent_status_changed, presence, etc.) so we never show a blank toast.
            const KNOWN = ["ticket_created", "ticket_assigned", "sla_breached", "call_offered"];
            if (!KNOWN.includes(payload.event)) return;

            let title = "System Notification";
            let msg = "";
            let type: Toast["type"] = "info";

            if (payload.event === "call_offered") {
              title = "📞 Incoming call";
              msg = `${(payload.data.intent || "general")} enquiry — open Contact Center to answer`;
              type = "warning";
            } else if (payload.event === "ticket_created") {
              title = "🆕 New Ticket Created";
              msg = `Ticket #${payload.data.ticket_number}: ${payload.data.subject}`;
              type = "success";
            } else if (payload.event === "ticket_assigned") {
              title = "🏷️ Ticket Updated";
              const statusName = payload.data.status.replace("_", " ");
              msg = `Ticket #${payload.data.ticket_number} is now ${statusName}`;
              type = "info";
            } else if (payload.event === "sla_breached") {
              title = "⚠️ SLA BREACHED";
              msg = `Ticket #${payload.data.ticket_number} has breached resolution SLA!`;
              type = "error";
            }
            
            addToast(title, msg, type);
            
            // Invalidate TanStack queries to trigger real-time data refreshing
            queryClient.invalidateQueries({ queryKey: ["tickets"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard"] });
          } catch (err) {
            console.error("Failed to parse SSE event data:", err);
          }
        };
        
        eventSource.onerror = () => {
          if (eventSource) {
            eventSource.close();
            eventSource = null;
          }
        };
      } else if (!token && eventSource) {
        // Disconnect immediately if logged out
        eventSource.close();
        eventSource = null;
      }
    }, 2000);
    
    return () => {
      clearInterval(tokenCheckInterval);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      
      {/* Premium Toast Overlay */}
      <div className="fixed top-4 right-4 z-[9999] space-y-2 pointer-events-none max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`p-4 rounded-lg shadow-xl border text-white pointer-events-auto transition-all transform duration-300 translate-x-0 ${
              t.type === "success" ? "bg-emerald-950/95 border-emerald-700" :
              t.type === "error" ? "bg-red-950/95 border-red-800" :
              t.type === "warning" ? "bg-amber-950/95 border-amber-850" :
              "bg-slate-800/95 border-slate-700"
            }`}
          >
            <div className="font-bold text-sm flex justify-between items-center">
              <span>{t.title}</span>
              <button
                className="text-slate-400 hover:text-white ml-2 text-xs"
                onClick={() => setToasts((prev) => prev.filter((toast) => toast.id !== t.id))}
              >
                ✕
              </button>
            </div>
            <div className="text-xs text-slate-200 mt-1">{t.message}</div>
          </div>
        ))}
      </div>
    </QueryClientProvider>
  );
}
