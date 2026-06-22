"use client";

import { useAuth } from "@/lib/auth";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Star, AlertCircle, Users, CheckCircle, BarChart3, MessageSquare, Ticket } from "lucide-react";

const COLORS = ["#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#EC4899", "#6B7280"];

export default function DashboardPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"agent" | "supervisor">("agent");

  // Agent dashboard query
  const { data: dashboard, isLoading: isDashboardLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const res = await fetchWithAuth("/dashboard/agent");
      if (!res.ok) throw new Error("Failed to load dashboard");
      return res.json();
    }
  });

  // Agent queue query
  const { data: myTickets, isLoading: isTicketsLoading } = useQuery({
    queryKey: ["tickets", "my"],
    queryFn: async () => {
      const res = await fetchWithAuth("/tickets?scope=my&page_size=10");
      if (!res.ok) throw new Error("Failed to load tickets");
      return res.json();
    }
  });

  // Supervisor dashboard query
  const { data: supervisorDashboard, isLoading: isSupervisorLoading } = useQuery({
    queryKey: ["supervisor-dashboard"],
    queryFn: async () => {
      const res = await fetchWithAuth("/dashboard/supervisor");
      if (!res.ok) throw new Error("Failed to load supervisor dashboard");
      return res.json();
    },
    enabled: ["admin", "supervisor"].includes(user?.role || "") && activeTab === "supervisor"
  });

  // Supervisor CSAT feedback feed query
  const { data: csatFeedbackList = [], isLoading: isFeedbackLoading } = useQuery({
    queryKey: ["csat-feedback"],
    queryFn: async () => {
      const res = await fetchWithAuth("/dashboard/csat-feedback");
      if (!res.ok) throw new Error("Failed to load CSAT feedback");
      return res.json();
    },
    enabled: ["admin", "supervisor"].includes(user?.role || "") && activeTab === "supervisor"
  });

  // Parse data for Recharts BarChart (CSAT distribution)
  const csatChartData = Object.entries(supervisorDashboard?.csat_rating_counts || {}).map(([rating, count]) => ({
    name: `${rating} Star`,
    count: count as number
  }));

  // Parse data for Recharts PieChart (Status breakdown)
  const statusChartData = Object.entries(supervisorDashboard?.tickets_by_status || {}).map(([status, count]) => ({
    name: status.replace("_", " ").toUpperCase(),
    value: count as number
  }));

  const renderAgentView = () => (
    <div className="space-y-6">
      <p className="text-slate-400">Welcome back, {user?.full_name}. Here is your queue.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-sm text-slate-400 mb-2">My Open Tickets</div>
          <div className="text-3xl font-bold text-white">
            {isDashboardLoading ? "..." : dashboard?.my_open_tickets}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-sm text-amber-400 mb-2">Due Soon</div>
          <div className="text-3xl font-bold text-white">
            {isDashboardLoading ? "..." : dashboard?.tickets_due_soon}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 border-b-4 border-b-red-500">
          <div className="text-sm text-red-400 mb-2">Breached SLA</div>
          <div className="text-3xl font-bold text-white">
            {isDashboardLoading ? "..." : dashboard?.tickets_breached}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 border-b-4 border-b-emerald-500">
          <div className="text-sm text-emerald-400 mb-2">Resolved Today</div>
          <div className="text-3xl font-bold text-white">
            {isDashboardLoading ? "..." : dashboard?.resolved_today}
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden mt-8">
        <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
          <h2 className="text-lg font-semibold text-white">My Queue</h2>
        </div>
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
              {isTicketsLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center">Loading...</td>
                </tr>
              ) : myTickets?.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center">No open tickets assigned to you.</td>
                </tr>
              ) : (
                myTickets?.map((ticket: any) => (
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
      </div>
    </div>
  );

  const renderSupervisorView = () => (
    <div className="space-y-6">
      <p className="text-slate-400">Team performance, SLA health, and customer satisfaction aggregates.</p>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-sm text-slate-400 mb-2 flex items-center gap-2">
            <Ticket size={16} className="text-indigo-400" />
            Team Queue Depth
          </div>
          <div className="text-3xl font-bold text-white">
            {isSupervisorLoading ? "..." : supervisorDashboard?.team_queue_depth}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <div className="text-sm text-slate-400 mb-2 flex items-center gap-2">
            <Users size={16} className="text-amber-400" />
            Unassigned Tickets
          </div>
          <div className="text-3xl font-bold text-white">
            {isSupervisorLoading ? "..." : supervisorDashboard?.unassigned_count}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 border-b-4 border-b-red-500">
          <div className="text-sm text-red-400 mb-2 flex items-center gap-2">
            <AlertCircle size={16} />
            SLA Breach Rate
          </div>
          <div className="text-3xl font-bold text-white">
            {isSupervisorLoading ? "..." : `${supervisorDashboard?.sla_breach_rate_pct}%`}
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 border-b-4 border-b-amber-500">
          <div className="text-sm text-amber-400 mb-2 flex items-center gap-2">
            <Star size={16} className="fill-amber-400" />
            Average CSAT
          </div>
          <div className="text-3xl font-bold text-white flex items-baseline gap-2">
            {isSupervisorLoading ? (
              "..."
            ) : supervisorDashboard?.average_csat ? (
              <>
                <span>{supervisorDashboard.average_csat}</span>
                <span className="text-sm text-slate-400 font-normal">/ 5.0</span>
              </>
            ) : (
              <span className="text-lg text-slate-500 font-normal">No ratings</span>
            )}
          </div>
        </div>
      </div>

      {/* Charts row */}
      {!isSupervisorLoading && supervisorDashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* CSAT Distribution Chart */}
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <BarChart3 size={18} className="text-indigo-400" />
              CSAT Rating Distribution
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={csatChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569" }}
                    labelStyle={{ color: "#ffffff" }}
                    itemStyle={{ color: "#f59e0b" }}
                  />
                  <Bar dataKey="count" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Status Breakdown Chart */}
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <CheckCircle size={18} className="text-emerald-400" />
              Queue Breakdown by Status
            </h3>
            <div className="h-64 w-full flex flex-col md:flex-row items-center justify-around">
              <div className="h-48 w-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {statusChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: "#1e293b", borderColor: "#475569" }}
                      itemStyle={{ color: "#ffffff" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2 text-sm max-h-56 overflow-y-auto pr-2">
                {statusChartData.map((item, index) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                    <span className="text-slate-300 font-semibold">{item.value}</span>
                    <span className="text-slate-400 text-xs capitalize">{item.name.toLowerCase()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CSAT Customer Comments Feed */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mt-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <MessageSquare size={18} className="text-indigo-400" />
          Recent Customer CSAT Feedback
        </h3>
        
        <div className="space-y-4">
          {isFeedbackLoading ? (
            <div className="text-slate-500 italic text-sm text-center py-4">Loading comments...</div>
          ) : csatFeedbackList.length === 0 ? (
            <div className="text-slate-500 italic text-sm text-center py-4">No customer satisfaction comments recorded yet.</div>
          ) : (
            csatFeedbackList.map((feedback: any) => (
              <div key={feedback.id} className="p-4 bg-slate-900 border border-slate-700 rounded-lg space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-300 flex items-center gap-2">
                    <Link href={`/tickets/${feedback.id}`} className="text-indigo-400 hover:underline">
                      {feedback.ticket_number}
                    </Link>
                    <span className="text-slate-500">•</span>
                    <span className="capitalize">{feedback.category}</span>
                  </span>
                  <span className="text-slate-400">
                    {format(new Date(feedback.updated_at), "PPp")}
                  </span>
                </div>
                
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star 
                      key={star} 
                      className={`w-4 h-4 ${star <= (feedback.csat_rating || 0) ? "text-amber-400 fill-amber-400" : "text-slate-700"}`} 
                    />
                  ))}
                  <span className="text-white text-xs font-semibold ml-2">({feedback.csat_rating}.0)</span>
                </div>
                
                {feedback.csat_feedback && (
                  <p className="text-sm text-slate-300 italic border-l-2 border-slate-700 pl-3">
                    "{feedback.csat_feedback}"
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        </div>
        {/* Tab selection for Admin and Supervisor */}
        {["admin", "supervisor"].includes(user?.role || "") && (
          <div className="flex bg-slate-800 p-1 rounded-lg border border-slate-700">
            <button
              onClick={() => setActiveTab("agent")}
              className={`px-4 py-1.5 text-sm font-semibold rounded transition-all ${
                activeTab === "agent"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Agent View
            </button>
            <button
              onClick={() => setActiveTab("supervisor")}
              className={`px-4 py-1.5 text-sm font-semibold rounded transition-all ${
                activeTab === "supervisor"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Supervisor View
            </button>
          </div>
        )}
      </div>

      {activeTab === "agent" ? renderAgentView() : renderSupervisorView()}
    </div>
  );
}
