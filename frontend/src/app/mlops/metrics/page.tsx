"use client";

import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useCostSummary, useMetrics } from "@/lib/hooks/useMlops";
import { Card, CardContent } from "@/components/ui/Card";
import { BarChart2 } from "lucide-react";

const AGENTS = ["idea_analyst","market_research","technical_feasibility","prd_generator","architecture_agent","quality_evaluator"];
const COLORS = ["#6366f1","#a855f7","#14b8a6","#f59e0b","#ef4444","#22c55e"];

const selectCls = "rounded-lg bg-white/[0.04] border border-white/[0.08] px-3 py-1.5 text-xs text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all";

export default function MetricsPage() {
  const [agent, setAgent] = useState("");
  const { data: cost } = useCostSummary();
  const { data: metrics } = useMetrics(agent || undefined);

  const chartData = metrics?.metrics
    ? Object.entries(metrics.metrics as Record<string, { avg: number }>).map(([name, v]) => ({
        name, avg: +(v.avg * 100).toFixed(1),
      }))
    : [];

  const byAgent = (cost?.by_agent ?? {}) as Record<string, { input_tokens: number; output_tokens: number; estimated_cost_usd: number | null; run_count: number }>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-teal-500/10"><BarChart2 className="h-4 w-4 text-teal-400" /></div>
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Metrics & Cost</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Token usage, cost breakdown, and quality scores</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: "Total Runs",     value: String(cost?.run_count ?? 0),      color: "text-indigo-300" },
          { label: "Input Tokens",   value: Number(cost?.total_input_tokens ?? 0).toLocaleString(), color: "text-purple-300" },
          { label: "Output Tokens",  value: Number(cost?.total_output_tokens ?? 0).toLocaleString(), color: "text-teal-300" },
          { label: "Est. Bedrock Cost", value: `$${Number(cost?.total_estimated_cost_usd ?? 0).toFixed(4)}`, color: "text-emerald-300" },
        ].map(({ label, value, color }) => (
          <Card key={label}>
            <CardContent className="pt-5">
              <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-widest">{label}</p>
              <p className={`mt-2 text-2xl font-bold ${color}`}>{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Cost by agent table */}
      {Object.keys(byAgent).length > 0 && (
        <Card>
          <div className="px-5 pt-5 pb-4 border-b border-white/[0.05]">
            <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-widest">Cost by Agent</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.05]">
                  {["Agent","Runs","Input","Output","Est. Cost"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {Object.entries(byAgent).map(([name, d]) => (
                  <tr key={name} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3 font-mono text-indigo-300">{name}</td>
                    <td className="px-5 py-3 text-[var(--text-muted)]">{d.run_count}</td>
                    <td className="px-5 py-3 text-[var(--text-muted)] font-mono">{d.input_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3 text-[var(--text-muted)] font-mono">{d.output_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3 text-emerald-400 font-mono">{d.estimated_cost_usd == null ? "—" : `$${d.estimated_cost_usd.toFixed(6)}`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Quality chart */}
      <Card>
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-white/[0.05]">
          <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-widest">Quality Scores</p>
          <select className={selectCls} value={agent} onChange={(e) => setAgent(e.target.value)}>
            <option value="">All agents</option>
            {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <CardContent className="pt-4">
          {chartData.length === 0 ? (
            <div className="py-12 text-center text-sm text-[var(--text-muted)]">No evaluation scores yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData} margin={{ top: 4, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 10, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1a1a24", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "12px", color: "#f0f0f8" }}
                  formatter={(v: number) => [`${v}%`, "Avg Score"]}
                />
                <Bar dataKey="avg" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
