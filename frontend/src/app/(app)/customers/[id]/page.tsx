"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";
import { useAuth } from "@/lib/auth";

export default function Customer360Page({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");

  const { data: overview, isLoading } = useQuery({
    queryKey: ["customer", params.id, "overview"],
    queryFn: async () => {
      const res = await fetchWithAuth(`/customers/${params.id}/overview`);
      if (!res.ok) throw new Error("Failed to load customer overview");
      return res.json();
    }
  });

  const { data: tickets, isLoading: ticketsLoading } = useQuery({
    queryKey: ["customer", params.id, "tickets"],
    queryFn: async () => {
      const res = await fetchWithAuth(`/customers/${params.id}/tickets`);
      if (!res.ok) throw new Error("Failed to load tickets");
      return res.json();
    },
    enabled: activeTab === "tickets"
  });

  const { data: billing, isLoading: billingLoading } = useQuery({
    queryKey: ["customer", params.id, "billing"],
    queryFn: async () => {
      const res = await fetchWithAuth(`/customers/${params.id}/billing`);
      if (!res.ok) throw new Error("Failed to load billing");
      return res.json();
    },
    enabled: activeTab === "billing"
  });

  if (isLoading) return <div className="p-8 text-slate-400">Loading Customer 360...</div>;
  if (!overview) return <div className="p-8 text-slate-400">Customer not found.</div>;

  const { profile, billing_summary, active_subscriptions, recent_interactions, open_tickets_count } = overview;

  return (
    <div className="flex gap-6 h-full">
      {/* Sidebar Profile */}
      <div className="w-80 space-y-6 flex flex-col">
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">{profile.first_name} {profile.last_name}</h2>
            <span className={`px-2 py-1 rounded text-xs capitalize font-semibold ${
               profile.status === 'active' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800' :
               profile.status === 'suspended' ? 'bg-orange-900/50 text-orange-400 border border-orange-800' :
               profile.status === 'terminated' ? 'bg-red-900/50 text-red-400 border border-red-800' :
               'bg-slate-700 text-slate-300 border border-slate-600'
            }`}>
              {profile.status}
            </span>
          </div>
          
          <div className="text-slate-400 text-sm mb-6 flex flex-col space-y-1">
            <span className="font-mono text-slate-300">{profile.account_number}</span>
            <span className="capitalize">{profile.customer_type} • {profile.segment}</span>
          </div>

          <div className="space-y-4 text-sm">
            <div>
              <div className="text-slate-500 mb-1">Email</div>
              <div className="text-slate-300">{profile.email || "N/A"}</div>
            </div>
            <div>
              <div className="text-slate-500 mb-1">Primary Phone</div>
              <div className="text-slate-300">{profile.phone_primary}</div>
            </div>
            {profile.phone_secondary && (
              <div>
                <div className="text-slate-500 mb-1">Secondary Phone</div>
                <div className="text-slate-300">{profile.phone_secondary}</div>
              </div>
            )}
            <div>
              <div className="text-slate-500 mb-1">Customer Since</div>
              <div className="text-slate-300">{format(new Date(profile.created_at), "PPP")}</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 flex-1">
          <h3 className="font-semibold text-white mb-4">Quick Actions</h3>
          <div className="space-y-3">
             <button className="w-full text-left px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors text-sm font-semibold">
               + Create New Ticket
             </button>
             <button className="w-full text-left px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors text-sm font-semibold border border-slate-600">
               + Log Interaction
             </button>
             <button className="w-full text-left px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors text-sm font-semibold border border-slate-600">
               Edit Profile
             </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex gap-1 border-b border-slate-700 mb-6">
          {["overview", "subscriptions", "billing", "interactions", "tickets"].map(tab => (
            <button 
              key={tab}
              className={`px-6 py-3 font-medium capitalize ${activeTab === tab ? 'text-indigo-400 border-b-2 border-indigo-400 bg-slate-800/50' : 'text-slate-400 hover:text-white hover:bg-slate-800/30'}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeTab === "overview" && (
            <div className="grid grid-cols-2 gap-6">
               {/* Active Plans Widget */}
               <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                 <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-white">Active Subscriptions</h3>
                    <button className="text-indigo-400 text-sm hover:underline" onClick={() => setActiveTab('subscriptions')}>View All</button>
                 </div>
                 {active_subscriptions.length === 0 ? (
                    <div className="text-slate-400 text-sm">No active subscriptions.</div>
                 ) : (
                    <div className="space-y-4">
                      {active_subscriptions.map((sub: any) => (
                        <div key={sub.id} className="flex justify-between items-center bg-slate-900 p-3 rounded border border-slate-700">
                           <div>
                              <div className="text-white font-medium">{sub.plan_name}</div>
                              <div className="text-slate-500 text-xs mt-1">Since {format(new Date(sub.start_date), "MMM d, yyyy")}</div>
                           </div>
                           <div className="text-right">
                              <div className="text-emerald-400 font-semibold">${sub.monthly_charge}/mo</div>
                           </div>
                        </div>
                      ))}
                    </div>
                 )}
               </div>

               {/* Billing Summary Widget */}
               <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                 <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-white">Billing Summary</h3>
                    <button className="text-indigo-400 text-sm hover:underline" onClick={() => setActiveTab('billing')}>View Invoices</button>
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900 p-4 rounded border border-slate-700">
                       <div className="text-slate-400 text-xs mb-1">Current Balance</div>
                       <div className={`text-2xl font-bold ${billing_summary.current_balance > 0 ? 'text-orange-400' : 'text-emerald-400'}`}>
                          ${billing_summary.current_balance.toFixed(2)}
                       </div>
                    </div>
                    <div className="bg-slate-900 p-4 rounded border border-slate-700">
                       <div className="text-slate-400 text-xs mb-1">Overdue Invoices</div>
                       <div className={`text-2xl font-bold ${billing_summary.overdue_invoices_count > 0 ? 'text-red-400' : 'text-slate-300'}`}>
                          {billing_summary.overdue_invoices_count}
                       </div>
                    </div>
                    <div className="col-span-2 bg-slate-900 p-4 rounded border border-slate-700 flex justify-between items-center">
                       <div>
                         <div className="text-slate-400 text-xs mb-1">Last Invoice</div>
                         <div className="text-slate-300 font-medium">
                            {billing_summary.last_invoice_date ? format(new Date(billing_summary.last_invoice_date), "MMM d, yyyy") : "N/A"}
                         </div>
                       </div>
                       <div className="text-white font-semibold">
                          {billing_summary.last_invoice_amount ? `$${billing_summary.last_invoice_amount.toFixed(2)}` : "-"}
                       </div>
                    </div>
                 </div>
               </div>

               {/* Recent Interactions Widget */}
               <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 col-span-2">
                 <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-white">Recent Interactions</h3>
                    <button className="text-indigo-400 text-sm hover:underline" onClick={() => setActiveTab('interactions')}>View All</button>
                 </div>
                 {recent_interactions.length === 0 ? (
                    <div className="text-slate-400 text-sm">No recent interactions.</div>
                 ) : (
                    <div className="space-y-4">
                      {recent_interactions.map((interaction: any) => (
                        <div key={interaction.id} className="border-l-2 border-indigo-500 pl-4 py-1">
                           <div className="flex justify-between items-start mb-1">
                              <div className="text-white font-medium">{interaction.subject}</div>
                              <div className="text-slate-500 text-xs">{format(new Date(interaction.created_at), "MMM d, h:mm a")}</div>
                           </div>
                           <div className="text-slate-400 text-sm flex items-center gap-2">
                             <span className="uppercase text-[10px] tracking-wider bg-slate-700 px-1.5 py-0.5 rounded text-slate-300">{interaction.channel}</span>
                             <span className="truncate">{interaction.notes}</span>
                           </div>
                        </div>
                      ))}
                    </div>
                 )}
               </div>
            </div>
          )}

          {activeTab === "subscriptions" && (
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 text-center text-slate-400">
               Full subscription list and device management would render here.
            </div>
          )}

          {activeTab === "billing" && (
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
               {billingLoading ? (
                  <div className="p-8 text-center text-slate-400">Loading billing history...</div>
               ) : (
                  <table className="w-full text-left text-sm text-slate-400">
                     <thead className="text-xs uppercase bg-slate-700 text-slate-300">
                        <tr>
                           <th className="px-6 py-3">Invoice #</th>
                           <th className="px-6 py-3">Date</th>
                           <th className="px-6 py-3">Amount</th>
                           <th className="px-6 py-3">Status</th>
                           <th className="px-6 py-3">Due Date</th>
                        </tr>
                     </thead>
                     <tbody>
                        {billing?.map((inv: any) => (
                           <tr key={inv.id} className="border-b border-slate-700">
                              <td className="px-6 py-4 text-white font-medium">{inv.invoice_number}</td>
                              <td className="px-6 py-4">{format(new Date(inv.created_at), "MMM d, yyyy")}</td>
                              <td className="px-6 py-4">${inv.total_amount}</td>
                              <td className="px-6 py-4">
                                 <span className={`px-2 py-1 rounded text-xs capitalize ${
                                    inv.status === 'paid' ? 'bg-emerald-900 text-emerald-300' :
                                    inv.status === 'overdue' ? 'bg-red-900 text-red-300' :
                                    'bg-slate-700 text-slate-300'
                                 }`}>{inv.status}</span>
                              </td>
                              <td className="px-6 py-4">{format(new Date(inv.due_date), "MMM d, yyyy")}</td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               )}
            </div>
          )}

          {activeTab === "interactions" && (
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 text-center text-slate-400">
               Full interaction timeline would render here.
            </div>
          )}

          {activeTab === "tickets" && (
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
               {ticketsLoading ? (
                  <div className="p-8 text-center text-slate-400">Loading tickets...</div>
               ) : (
                  <table className="w-full text-left text-sm text-slate-400">
                     <thead className="text-xs uppercase bg-slate-700 text-slate-300">
                        <tr>
                           <th className="px-6 py-3">Ticket #</th>
                           <th className="px-6 py-3">Subject</th>
                           <th className="px-6 py-3">Status</th>
                           <th className="px-6 py-3">Created</th>
                        </tr>
                     </thead>
                     <tbody>
                        {tickets?.map((tkt: any) => (
                           <tr key={tkt.id} className="border-b border-slate-700">
                              <td className="px-6 py-4 text-indigo-400 font-medium">
                                 <Link href={`/tickets/${tkt.id}`} className="hover:underline">{tkt.ticket_number}</Link>
                              </td>
                              <td className="px-6 py-4 text-white">{tkt.subject}</td>
                              <td className="px-6 py-4 capitalize">{tkt.status.replace("_", " ")}</td>
                              <td className="px-6 py-4">{format(new Date(tkt.created_at), "MMM d, yyyy")}</td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
