"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";

export default function BillingPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data: invoices, isLoading } = useQuery({
    queryKey: ["invoices", statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20"
      });
      if (statusFilter) params.append("status", statusFilter);

      const res = await fetchWithAuth(`/invoices?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to load invoices");
      return res.json();
    }
  });

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Billing & Invoices</h1>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors">
          Generate Invoice
        </button>
      </div>

      <div className="flex gap-4 items-center bg-slate-800 p-4 rounded-lg border border-slate-700">
        <div className="text-white font-medium mr-4">Filter by Status:</div>
        <select
          className="bg-slate-900 border border-slate-700 text-white rounded px-4 py-2 focus:outline-none focus:border-indigo-500 w-48"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Invoices</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
        </select>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 flex-1 flex flex-col overflow-hidden">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="text-xs uppercase bg-slate-700 text-slate-300 sticky top-0">
              <tr>
                <th className="px-6 py-3">Invoice #</th>
                <th className="px-6 py-3">Customer ID</th>
                <th className="px-6 py-3">Amount</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Billing Period</th>
                <th className="px-6 py-3">Due Date</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-300">Loading invoices...</td>
                </tr>
              ) : invoices?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-400">No invoices found.</td>
                </tr>
              ) : (
                invoices?.map((inv: any) => (
                  <tr key={inv.id} className="border-b border-slate-700 hover:bg-slate-700/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">{inv.invoice_number}</td>
                    <td className="px-6 py-4 text-indigo-400">
                      <Link href={`/customers/${inv.customer_id}?tab=billing`} className="hover:underline">
                        Cust #{inv.customer_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 font-semibold text-white">${inv.total_amount}</td>
                    <td className="px-6 py-4">
                       <span className={`px-2 py-1 rounded text-xs capitalize ${
                          inv.status === 'paid' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800' :
                          inv.status === 'overdue' ? 'bg-red-900/50 text-red-400 border border-red-800' :
                          'bg-orange-900/50 text-orange-400 border border-orange-800'
                       }`}>
                         {inv.status}
                       </span>
                    </td>
                    <td className="px-6 py-4">
                       {format(new Date(inv.billing_period_start), "MMM d, yyyy")} - {format(new Date(inv.billing_period_end), "MMM d, yyyy")}
                    </td>
                    <td className="px-6 py-4">
                       {format(new Date(inv.due_date), "MMM d, yyyy")}
                    </td>
                    <td className="px-6 py-4">
                       <button className="text-slate-300 hover:text-white transition-colors">View Details</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-slate-700 flex justify-between items-center bg-slate-800 mt-auto">
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
            disabled={!invoices || invoices.length < 20}
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
