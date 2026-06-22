"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";
import { useDebounce } from "use-debounce";

export default function CustomersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch] = useDebounce(searchTerm, 500);
  const [statusFilter, setStatusFilter] = useState("");
  const [segmentFilter, setSegmentFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers", debouncedSearch, statusFilter, segmentFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20"
      });
      if (debouncedSearch) params.append("q", debouncedSearch);
      if (statusFilter) params.append("status", statusFilter);
      if (segmentFilter) params.append("segment", segmentFilter);

      const res = await fetchWithAuth(`/customers?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to load customers");
      return res.json();
    }
  });

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Customers</h1>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors">
          Add Customer
        </button>
      </div>

      <div className="flex gap-4 items-center bg-slate-800 p-4 rounded-lg border border-slate-700">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by name, account #, phone, email..."
            className="w-full bg-slate-900 border border-slate-700 text-white rounded px-4 py-2 focus:outline-none focus:border-indigo-500"
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
          />
        </div>
        <select
          className="bg-slate-900 border border-slate-700 text-white rounded px-4 py-2 focus:outline-none focus:border-indigo-500"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="terminated">Terminated</option>
          <option value="pending">Pending</option>
        </select>
        <select
          className="bg-slate-900 border border-slate-700 text-white rounded px-4 py-2 focus:outline-none focus:border-indigo-500"
          value={segmentFilter}
          onChange={(e) => { setSegmentFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Segments</option>
          <option value="standard">Standard</option>
          <option value="premium">Premium</option>
          <option value="vip">VIP</option>
        </select>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 flex-1 flex flex-col overflow-hidden">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="text-xs uppercase bg-slate-700 text-slate-300 sticky top-0">
              <tr>
                <th className="px-6 py-3">Account #</th>
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Phone</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Segment</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-300">Loading customers...</td>
                </tr>
              ) : customers?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">No customers found.</td>
                </tr>
              ) : (
                customers?.map((customer: any) => (
                  <tr key={customer.id} className="border-b border-slate-700 hover:bg-slate-700/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">
                      <Link href={`/customers/${customer.id}`} className="text-indigo-400 hover:underline">
                        {customer.account_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-white">
                      {customer.first_name} {customer.last_name}
                    </td>
                    <td className="px-6 py-4">{customer.email}</td>
                    <td className="px-6 py-4">{customer.phone_primary}</td>
                    <td className="px-6 py-4">
                       <span className={`px-2 py-1 rounded text-xs capitalize ${
                          customer.status === 'active' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800' :
                          customer.status === 'suspended' ? 'bg-orange-900/50 text-orange-400 border border-orange-800' :
                          customer.status === 'terminated' ? 'bg-red-900/50 text-red-400 border border-red-800' :
                          'bg-slate-700 text-slate-300 border border-slate-600'
                       }`}>
                         {customer.status}
                       </span>
                    </td>
                    <td className="px-6 py-4 capitalize">
                      {customer.segment}
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
            disabled={!customers || customers.length < 20}
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
