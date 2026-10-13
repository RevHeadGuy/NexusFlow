"use client";

import { Database, FileSearch, Link2, ShieldCheck, TerminalSquare } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";

const TOOLS = [
  { name: "get_project_context", description: "Read the project idea, brief, current workflow stage, and recorded decisions.", icon: Database },
  { name: "list_project_artifacts", description: "List artifact names, versions, types, and update times for a project.", icon: FileSearch },
  { name: "read_project_artifact", description: "Read the latest content for an artifact after checking project ownership.", icon: FileSearch },
];

export default function ToolsPage() {
  return (
    <div className="mx-auto w-full max-w-5xl p-4 sm:p-6 lg:p-8 space-y-7 animate-fade-in-up">
      <div>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-indigo-500/10 p-2"><Link2 className="h-5 w-5 text-indigo-400" /></div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">MCP Tool Access</h1>
          <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-300">Read only</span>
        </div>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[var(--text-muted)]">
          NexusFlow exposes project context and saved artifacts to compatible MCP clients over Streamable HTTP. Tools can read project data but cannot change it.
        </p>
      </div>

      <Card>
        <div className="flex items-center gap-2 border-b border-white/[0.05] px-5 py-4">
          <TerminalSquare className="h-4 w-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Start the local MCP server</h2>
        </div>
        <CardContent className="space-y-4">
          <p className="text-xs leading-relaxed text-[var(--text-muted)]">Keep the backend running, then open another terminal in the backend folder and run:</p>
          <pre className="overflow-x-auto rounded-lg border border-white/[0.06] bg-black/20 p-4 text-xs leading-relaxed text-indigo-200">{`cd backend
source .venv/bin/activate
python -m app.mcp_server`}</pre>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="min-w-0 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">MCP endpoint</p>
              <code className="mt-1 block break-all text-xs text-[var(--text-primary)]">http://127.0.0.1:8001/mcp</code>
            </div>
            <div className="min-w-0 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">Transport</p>
              <p className="mt-1 break-words text-xs text-[var(--text-primary)]">Streamable HTTP · loopback only</p>
            </div>
          </div>
          <p className="flex items-start gap-2 text-xs text-[var(--text-muted)]"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />The server binds to this computer only. MCP clients must run on the same machine. Requests include project IDs; artifact reads are checked against the selected project.</p>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Available tools</h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">A client can discover these through the standard MCP tools/list operation.</p>
        </div>
        <div className="grid gap-3">
          {TOOLS.map(({ name, description, icon: Icon }) => (
            <Card key={name}>
              <CardContent className="flex items-start gap-3 py-4">
                <div className="rounded-lg bg-white/[0.04] p-2"><Icon className="h-4 w-4 text-indigo-300" /></div>
                <div className="min-w-0">
                  <code className="text-xs font-semibold text-[var(--text-primary)]">{name}</code>
                  <p className="mt-1 text-xs leading-relaxed text-[var(--text-muted)]">{description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
      <p className="text-[11px] leading-relaxed text-[var(--text-muted)]">MCP currently provides local project context to compatible clients. It does not perform web research or trigger NexusFlow workflow actions.</p>
    </div>
  );
}
