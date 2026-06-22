"use client";

import { useAuth } from "@/lib/auth";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import { useState, useEffect } from "react";
import { format } from "date-fns";
import { Star, Eye } from "lucide-react";

interface KbArticle {
  id: number;
  title: string;
  slug: string;
  category_id: number | null;
  body: string | null;
  tags: string[] | null;
  status: string;
  author_id: number | null;
  view_count: number;
  created_at: string;
  updated_at: string;
}

interface TicketComment {
  id: number;
  ticket_id: number;
  author_id: number | null;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export default function TicketDetailPage({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [commentBody, setCommentBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<KbArticle | null>(null);
  
  const [showCsatModal, setShowCsatModal] = useState(false);
  const [csatRating, setCsatRating] = useState(5);
  const [csatFeedback, setCsatFeedback] = useState("");
  const [pendingStatus, setPendingStatus] = useState<"resolved" | "closed" | null>(null);
  const [otherViewers, setOtherViewers] = useState<{ id: number; full_name: string }[]>([]);
  const [conflict, setConflict] = useState(false);

  // 1. Fetch ticket details
  const { data: ticket, isLoading: isTicketLoading } = useQuery({
    queryKey: ["tickets", params.id],
    queryFn: async () => {
      const res = await fetchWithAuth(`/tickets/${params.id}`);
      if (!res.ok) throw new Error("Failed to load ticket");
      return res.json();
    }
  });

  // 2. Fetch ticket comments
  const { data: comments = [], isLoading: isCommentsLoading } = useQuery<TicketComment[]>({
    queryKey: ["tickets", params.id, "comments"],
    queryFn: async () => {
      const res = await fetchWithAuth(`/tickets/${params.id}/comments`);
      if (!res.ok) throw new Error("Failed to load comments");
      return res.json();
    }
  });

  // 3. Fetch suggested KB articles
  const { data: suggestedKb = [], isLoading: isKbLoading } = useQuery<KbArticle[]>({
    queryKey: ["tickets", params.id, "suggested-kb"],
    queryFn: async () => {
      const res = await fetchWithAuth(`/tickets/${params.id}/suggested-kb`);
      if (!res.ok) throw new Error("Failed to load suggested articles");
      return res.json();
    }
  });

  // 4. Claim ticket — atomic, concurrency-safe (dedicated /claim endpoint).
  const claimTicketMutation = useMutation({
    mutationFn: async () => {
      const res = await fetchWithAuth(`/tickets/${params.id}/claim`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error?.message || "Failed to claim ticket");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets", params.id] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
    onError: (e: any) => alert(e.message),
  });

  // Release ticket back to the queue.
  const releaseTicketMutation = useMutation({
    mutationFn: async () => {
      const res = await fetchWithAuth(`/tickets/${params.id}/release`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to release ticket");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets", params.id] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  // Update ticket mutation (status changes & CSAT). Sends the version token so
  // a stale tab can't silently overwrite a newer change (409 -> conflict banner).
  const updateTicketMutation = useMutation({
    mutationFn: async (payload: { status?: string; csat_rating?: number; csat_feedback?: string }) => {
      const res = await fetchWithAuth(`/tickets/${params.id}`, {
        method: "PATCH",
        body: JSON.stringify({ ...payload, version: ticket?.version }),
      });
      if (res.status === 409) {
        setConflict(true);
        queryClient.invalidateQueries({ queryKey: ["tickets", params.id] });
        throw new Error("Conflict");
      }
      if (!res.ok) throw new Error("Failed to update ticket");
      return res.json();
    },
    onSuccess: () => {
      setConflict(false);
      queryClient.invalidateQueries({ queryKey: ["tickets", params.id] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  // 5. Add comment mutation
  const addCommentMutation = useMutation({
    mutationFn: async (payload: { body: string; is_internal: boolean }) => {
      const res = await fetchWithAuth(`/tickets/${params.id}/comments`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to add comment");
      return res.json();
    },
    onSuccess: () => {
      setCommentBody("");
      setIsInternal(false);
      queryClient.invalidateQueries({ queryKey: ["tickets", params.id, "comments"] });
    }
  });

  // 6. Link KB Article mutation (posts a link comment to the ticket)
  const linkArticleMutation = useMutation({
    mutationFn: async (article: KbArticle) => {
      const res = await fetchWithAuth(`/tickets/${params.id}/comments`, {
        method: "POST",
        body: JSON.stringify({
          body: `Linked KB Article: [${article.title}](/kb/${article.id})`,
          is_internal: false
        })
      });
      if (!res.ok) throw new Error("Failed to link article");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets", params.id, "comments"] });
    }
  });

  // Presence: announce that this agent is viewing the ticket, listen for other
  // viewers via SSE, and release on unmount so collisions are visible live.
  useEffect(() => {
    const id = params.id;
    fetchWithAuth(`/tickets/${id}/presence`, { method: "POST" }).catch(() => {});

    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    let es: EventSource | null = null;
    if (token) {
      const base = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      es = new EventSource(`${base}/events/stream?token=${token}`);
      es.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (
            (msg.event === "ticket_viewing" || msg.event === "ticket_released") &&
            String(msg.data?.ticket_id) === String(id)
          ) {
            const viewers = (msg.data?.viewers || []).filter((v: any) => v.id !== user?.id);
            setOtherViewers(viewers);
          }
        } catch {}
      };
    }

    return () => {
      es?.close();
      fetchWithAuth(`/tickets/${id}/presence`, { method: "DELETE" }).catch(() => {});
    };
  }, [params.id, user?.id]);

  if (isTicketLoading) return <div className="p-8 text-slate-400">Loading ticket...</div>;
  if (!ticket) return <div className="p-8 text-slate-400">Ticket not found.</div>;

  return (
    <div className="flex gap-6 h-full">
      <div className="flex-1 flex flex-col space-y-6">
        {/* Collision awareness: other agents currently viewing this ticket */}
        {otherViewers.length > 0 && (
          <div className="bg-amber-950/40 border border-amber-800/60 text-amber-200 rounded-lg px-4 py-2 text-sm flex items-center gap-2">
            <Eye size={16} />
            Also viewing: {otherViewers.map((v) => v.full_name).join(", ")}
          </div>
        )}
        {/* Optimistic-concurrency conflict */}
        {conflict && (
          <div className="bg-red-950/40 border border-red-800/60 text-red-200 rounded-lg px-4 py-2 text-sm">
            This ticket was changed by someone else. The view has been refreshed — please retry your action.
          </div>
        )}
        {/* Ticket Header */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">{ticket.subject}</h1>
            <div className="flex gap-3 text-sm text-slate-400 items-center">
              <span className="bg-slate-700 text-white px-2 py-1 rounded">{ticket.ticket_number}</span>
              <span className="capitalize">Status: {ticket.status.replace("_", " ")}</span>
              <span className={`px-2 py-1 rounded text-xs ${
                ticket.priority === 'critical' ? 'bg-red-900 text-red-300' :
                ticket.priority === 'high' ? 'bg-orange-900 text-orange-300' :
                ticket.priority === 'medium' ? 'bg-blue-900 text-blue-300' :
                'bg-slate-700 text-slate-300'
              }`}>{ticket.priority}</span>
              <span className="capitalize">Category: {ticket.category}</span>
            </div>
          </div>
          <div className="text-right">
             <div className="text-sm font-semibold text-slate-300 mb-1">SLA Resolution Due</div>
             <div className={`text-lg font-bold ${ticket.sla_breached ? 'text-red-400' : 'text-emerald-400'}`}>
                {ticket.sla_resolution_due ? format(new Date(ticket.sla_resolution_due), "PPp") : "N/A"}
             </div>
          </div>
        </div>

        {/* Timeline & Reply Form */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 flex-1 overflow-auto flex flex-col">
          <div className="mb-6">
            <h3 className="text-white font-semibold mb-2">Description</h3>
            <p className="text-slate-300 whitespace-pre-wrap">{ticket.description}</p>
          </div>
          
          <hr className="border-slate-700 my-4" />
          <h3 className="text-white font-semibold mb-4">Timeline & History</h3>
          
          <div className="flex-1 space-y-4 mb-6 max-h-[300px] overflow-y-auto pr-2">
             {isCommentsLoading ? (
               <div className="text-slate-500 italic text-sm text-center">Loading timeline...</div>
             ) : comments.length === 0 ? (
               <div className="text-slate-500 italic text-sm text-center">No comments or activity logged.</div>
             ) : (
               comments.map((comment) => (
                 <div 
                   key={comment.id} 
                   className={`p-4 rounded-lg border ${
                     comment.is_internal 
                       ? "bg-amber-950/30 border-amber-900/50 text-amber-200" 
                       : "bg-slate-900 border-slate-700 text-slate-300"
                   }`}
                 >
                   <div className="flex justify-between items-center text-xs text-slate-400 mb-2">
                     <span className="font-semibold text-slate-300">
                       {comment.author_id === user?.id ? "You" : `Agent #${comment.author_id}`}
                       {comment.is_internal && <span className="ml-2 text-amber-500 uppercase font-bold text-[10px]">Internal Note</span>}
                     </span>
                     <span>{format(new Date(comment.created_at), "PPp")}</span>
                   </div>
                   <p className="text-sm whitespace-pre-wrap">{comment.body}</p>
                 </div>
               ))
             )}
          </div>
          
          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 mt-auto">
            <textarea 
               className="w-full bg-slate-800 text-white border border-slate-700 rounded p-3 min-h-[100px] focus:outline-none focus:border-indigo-500"
               placeholder="Type your reply or internal note here..."
               value={commentBody}
               onChange={e => setCommentBody(e.target.value)}
            />
            <div className="flex justify-between items-center mt-3">
              <label className="flex items-center text-slate-400 text-sm gap-2">
                <input 
                  type="checkbox" 
                  checked={isInternal} 
                  onChange={e => setIsInternal(e.target.checked)} 
                  className="rounded border-slate-600 bg-slate-800 text-indigo-500 focus:ring-indigo-500" 
                />
                Internal Note (hidden from customer)
              </label>
              <button 
                 className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded font-semibold transition-colors disabled:opacity-50"
                 onClick={() => addCommentMutation.mutate({ body: commentBody, is_internal: isInternal })}
                 disabled={!commentBody.trim() || addCommentMutation.isPending}
              >
                {addCommentMutation.isPending ? "Submitting..." : "Submit"}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Right Rail */}
      <div className="w-80 space-y-6">
        {/* Ticket Details Panel */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
           <h3 className="text-white font-semibold mb-4">Ticket Details</h3>
           <div className="space-y-4 text-sm">
              <div>
                <div className="text-slate-500 mb-1">Customer ID</div>
                <div className="text-slate-300 font-medium">{ticket.customer_id}</div>
              </div>
              <div>
                <div className="text-slate-500 mb-1">Assigned To</div>
                <div className="text-slate-300 font-medium flex items-center justify-between">
                  <span>{ticket.assigned_agent_id ? `Agent ${ticket.assigned_agent_id}` : "Unassigned"}</span>
                  {!ticket.assigned_agent_id && (
                     <button 
                       className="text-indigo-400 hover:text-indigo-300 text-xs font-semibold"
                       onClick={() => claimTicketMutation.mutate()}
                       disabled={claimTicketMutation.isPending}
                     >
                       {claimTicketMutation.isPending ? "Claiming..." : "Claim Ticket"}
                     </button>
                  )}
                </div>
              </div>
              <div>
                <div className="text-slate-500 mb-1">Created At</div>
                <div className="text-slate-300 font-medium">{format(new Date(ticket.created_at), "PPp")}</div>
              </div>
            </div>
         </div>

        {/* Quick Actions Panel */}
        {ticket.status !== "closed" && ticket.status !== "resolved" && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 space-y-3">
             <h3 className="text-white font-semibold mb-2">Actions</h3>
             <div className="flex flex-col gap-2">
               {ticket.assigned_agent_id !== user?.id ? (
                 <button 
                   className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded font-semibold text-sm transition-colors"
                   onClick={() => claimTicketMutation.mutate()}
                   disabled={claimTicketMutation.isPending}
                 >
                   Claim Ticket
                 </button>
               ) : (
                 <>
                   <button 
                     className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded font-semibold text-sm transition-colors"
                     onClick={() => {
                       setPendingStatus("resolved");
                       setCsatRating(5);
                       setCsatFeedback("");
                       setShowCsatModal(true);
                     }}
                   >
                     Resolve Ticket
                   </button>
                   <button
                     className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded font-semibold text-sm transition-colors"
                     onClick={() => {
                       setPendingStatus("closed");
                       setCsatRating(5);
                       setCsatFeedback("");
                       setShowCsatModal(true);
                     }}
                   >
                     Close Ticket
                   </button>
                   <button
                     className="w-full bg-slate-700 hover:bg-slate-600 text-white py-2 rounded font-semibold text-sm transition-colors"
                     onClick={() => releaseTicketMutation.mutate()}
                     disabled={releaseTicketMutation.isPending}
                   >
                     Release to Queue
                   </button>
                 </>
               )}
             </div>
          </div>
        )}

        {/* CSAT Rating Panel */}
        {ticket.csat_rating && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 border-l-4 border-l-amber-500 space-y-3">
             <h3 className="text-white font-semibold flex items-center gap-2">
               <Star className="text-amber-400 fill-amber-400" size={18} />
               Customer Satisfaction
             </h3>
             <div className="space-y-3">
               <div className="flex items-center gap-1">
                 {[1, 2, 3, 4, 5].map((star) => (
                   <Star 
                     key={star} 
                     className={`w-5 h-5 ${star <= (ticket.csat_rating || 0) ? "text-amber-400 fill-amber-400" : "text-slate-600"}`} 
                   />
                 ))}
                 <span className="text-white font-bold ml-2">{ticket.csat_rating}.0 / 5.0</span>
               </div>
               {ticket.csat_feedback && (
                 <p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded border border-slate-700/50 italic">
                   "{ticket.csat_feedback}"
                 </p>
               )}
             </div>
          </div>
        )}

         {/* Suggested KB Articles Panel */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 flex flex-col">
          <h3 className="text-white font-semibold mb-3">Suggested Articles</h3>
          {isKbLoading ? (
            <div className="text-slate-500 italic text-sm">Loading suggestions...</div>
          ) : suggestedKb.length === 0 ? (
            <div className="text-slate-500 italic text-sm">No suggested articles found.</div>
          ) : (
            <div className="space-y-3">
              {suggestedKb.map(article => (
                <div key={article.id} className="p-3 bg-slate-900 border border-slate-700 rounded-lg space-y-2">
                  <div 
                    className="text-indigo-400 hover:text-indigo-300 font-medium text-sm cursor-pointer hover:underline"
                    onClick={() => setSelectedArticle(article)}
                  >
                    {article.title}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded uppercase font-semibold">
                      KB Article
                    </span>
                    <button 
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                      onClick={() => linkArticleMutation.mutate(article)}
                    >
                      Link Article
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Suggested Article Detail Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full p-6 space-y-4 max-h-[80vh] overflow-y-auto relative">
            <button 
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl font-bold"
              onClick={() => setSelectedArticle(null)}
            >
              ✕
            </button>
            <h2 className="text-xl font-bold text-white pr-6">{selectedArticle.title}</h2>
            <div className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed border-t border-b border-slate-700 py-4 my-2">
              {selectedArticle.body}
            </div>
            <div className="flex justify-end pt-2">
              <button
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors mr-2"
                onClick={() => {
                  linkArticleMutation.mutate(selectedArticle);
                  setSelectedArticle(null);
                }}
              >
                Link to Ticket
              </button>
              <button
                className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded font-semibold transition-colors"
                onClick={() => setSelectedArticle(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSAT Modal */}
      {showCsatModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-md w-full p-6 space-y-4 relative">
            <button 
              className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl font-bold"
              onClick={() => setShowCsatModal(false)}
            >
              ✕
            </button>
            <h2 className="text-xl font-bold text-white">Customer Satisfaction Survey</h2>
            <p className="text-sm text-slate-400">
              Please collect the customer's satisfaction rating before marking the ticket as <span className="capitalize font-semibold text-white">{pendingStatus}</span>.
            </p>
            
            <div className="flex flex-col items-center py-4 space-y-2">
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className="transition-transform active:scale-95 hover:scale-110"
                    onClick={() => setCsatRating(star)}
                  >
                    <Star 
                      className={`w-10 h-10 ${star <= csatRating ? "text-amber-400 fill-amber-400" : "text-slate-600"}`} 
                    />
                  </button>
                ))}
              </div>
              <span className="text-sm font-semibold text-slate-300">
                {csatRating === 5 ? "Excellent (5/5)" :
                 csatRating === 4 ? "Very Good (4/5)" :
                 csatRating === 3 ? "Good (3/5)" :
                 csatRating === 2 ? "Fair (2/5)" :
                 "Poor (1/5)"}
              </span>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400 uppercase">Customer Feedback (Optional)</label>
              <textarea 
                className="w-full bg-slate-900 text-white border border-slate-700 rounded p-3 min-h-[80px] focus:outline-none focus:border-indigo-500 text-sm"
                placeholder="E.g., Customer was pleased with quick resolution..."
                value={csatFeedback}
                onChange={e => setCsatFeedback(e.target.value)}
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded font-semibold text-sm transition-colors"
                onClick={() => setShowCsatModal(false)}
              >
                Cancel
              </button>
              <button
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded font-semibold text-sm transition-colors flex items-center gap-2"
                onClick={() => {
                  updateTicketMutation.mutate({
                    status: pendingStatus || undefined,
                    csat_rating: csatRating,
                    csat_feedback: csatFeedback || undefined
                  }, {
                    onSuccess: () => {
                      setShowCsatModal(false);
                    }
                  });
                }}
                disabled={updateTicketMutation.isPending}
              >
                {updateTicketMutation.isPending ? "Submitting..." : "Submit & Update"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
