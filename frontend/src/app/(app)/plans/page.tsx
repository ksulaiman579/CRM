"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";

export default function PlansPage() {
  const { data: plans, isLoading } = useQuery({
    queryKey: ["plans"],
    queryFn: async () => {
      const res = await fetchWithAuth("/plans");
      if (!res.ok) throw new Error("Failed to load plans");
      return res.json();
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Service Plans</h1>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded font-semibold transition-colors">
          Add New Plan
        </button>
      </div>

      {isLoading ? (
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 text-center text-slate-400">
          Loading plans...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {plans?.map((plan: any) => (
            <div key={plan.id} className="bg-slate-800 rounded-xl border border-slate-700 flex flex-col overflow-hidden hover:border-indigo-500 transition-colors">
              <div className="p-6 border-b border-slate-700 bg-slate-800/50">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                  <span className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs uppercase font-bold tracking-wider">{plan.plan_type}</span>
                </div>
                <p className="text-slate-400 text-sm h-10">{plan.description}</p>
                <div className="mt-6 flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">${plan.monthly_price}</span>
                  <span className="text-slate-400">/mo</span>
                </div>
              </div>
              <div className="p-6 flex-1 flex flex-col">
                <div className="space-y-4 flex-1">
                  {plan.speed_mbps && (
                    <div className="flex items-center gap-3 text-slate-300">
                      <span className="text-emerald-400">✓</span>
                      <span>Up to <strong className="text-white">{plan.speed_mbps} Mbps</strong></span>
                    </div>
                  )}
                  {plan.data_cap_gb ? (
                    <div className="flex items-center gap-3 text-slate-300">
                      <span className="text-emerald-400">✓</span>
                      <span><strong className="text-white">{plan.data_cap_gb} GB</strong> Data Cap</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 text-slate-300">
                      <span className="text-emerald-400">✓</span>
                      <span><strong>Unlimited</strong> Data</span>
                    </div>
                  )}
                  {plan.voice_minutes && (
                    <div className="flex items-center gap-3 text-slate-300">
                      <span className="text-emerald-400">✓</span>
                      <span><strong className="text-white">{plan.voice_minutes}</strong> Voice Minutes</span>
                    </div>
                  )}
                  <div className="flex items-center gap-3 text-slate-300">
                    <span className="text-emerald-400">✓</span>
                    <span>{plan.contract_months}-month contract</span>
                  </div>
                </div>
                <button className="mt-8 w-full py-2 bg-slate-700 hover:bg-slate-600 text-white rounded font-semibold transition-colors">
                  Edit Plan
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
