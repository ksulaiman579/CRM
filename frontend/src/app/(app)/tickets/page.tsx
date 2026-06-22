"use client";

import { useAuth } from "@/lib/auth";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";

export default function TicketsPage() {
  const { user } = useAuth();
  const [scope, setScope] = useState("my");
  const [page, setPage] = useState(1);

  const { data: tickets, isLoading } = useQuery({
    queryKey: ["tickets", scope, page],
    queryFn: async () => {
      const res = await fetchWithAuth(`/tickets?scope=${scope}&page=${page}&page_size=20`);
      if (!res.ok) throw new Error("Failed to load tickets");
      return res.json();
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Tickets</h1>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors">
          New Ticket
        </button>
      </div>
      
      <div className="flex gap-4 border-b border-slate-700 pb-2">
        <button 
          className={`px-4 py-2 font-medium ${scope === 'my' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-400 hover:text-white'}`}
          onClick={() => { setScope('my'); setPage(1); }}
        >
          My Tickets
        </button>
        <button 
          className={`px-4 py-2 font-medium ${scope === 'queue' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-400 hover:text-white'}`}
          onClick={() => { setScope('queue'); setPage(1); }}
        >
          Unassigned Queue
        </button>
        {user?.team_id && (
          <button 
            className={`px-4 py-2 font-medium ${scope === 'team' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-400 hover:text-white'}`}
            onClick={() => { setScope('team'); setPage(1); }}
          >
            Team Tickets
          </button>
        )}
        <button 
          className={`px-4 py-2 font-medium ${scope === 'all' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-400 hover:text-white'}`}
          onClick={() => { setScope('all'); setPage(1); }}
        >
          All Tickets
        </button>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="text-xs uppercase bg-slate-700 text-slate-300">
              <tr>
                <th className="px-6 py-3">Ticket</th>
                <th className="px-6 py-3">Subject</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Priority</th>
                <th className="px-6 py-3">SLA Due</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-300">Loading tickets...</td>
                </tr>
              ) : tickets?.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">No tickets found in this view.</td>
                </tr>
              ) : (
                tickets?.map((ticket: any) => (
                  <tr key={ticket.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                    <td className="px-6 py-4 font-medium text-white">
                      <Link href={`/tickets/${ticket.id}`} className="text-indigo-400 hover:underline">
                        {ticket.ticket_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4">{ticket.subject}</td>
                    <td className="px-6 py-4 capitalize">{ticket.status.replace("_", " ")}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        ticket.priority === 'critical' ? 'bg-red-900 text-red-300' :
                        ticket.priority === 'high' ? 'bg-orange-900 text-orange-300' :
                        ticket.priority === 'medium' ? 'bg-blue-900 text-blue-300' :
                        'bg-slate-700 text-slate-300'
                      }`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {ticket.sla_breached ? (
                        <span className="text-red-400 font-semibold">Breached</span>
                      ) : ticket.sla_resolution_due ? (
                        format(new Date(ticket.sla_resolution_due), "PPp")
                      ) : (
                        "N/A"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-slate-700 flex justify-between items-center bg-slate-800">
          <button 
            className="px-4 py-2 bg-slate-700 text-white rounded disabled:opacity-50 hover:bg-slate-600 transition-colors"
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            Previous
          </button>
          <span className="text-slate-400 text-sm">Page {page}</span>
          <button 
            className="px-4 py-2 bg-slate-700 text-white rounded disabled:opacity-50 hover:bg-slate-600 transition-colors"
            disabled={!tickets || tickets.length < 20}
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
