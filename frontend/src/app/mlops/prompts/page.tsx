"use client";

import { useState } from "react";
import { usePromptVersions, useCreatePrompt, useActivatePrompt } from "@/lib/hooks/useMlops";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { FlaskConical } from "lucide-react";
import { formatDate, cn } from "@/lib/utils";

const AGENTS = ["idea_analyst","market_research","technical_feasibility","prd_generator","architecture_agent","ux_spec_agent","quality_evaluator"];
const inputCls = "w-full rounded-lg bg-white/[0.04] border border-white/[0.08] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all";

function AgentPrompts({ agentName }: { agentName: string }) {
  const { data: versions, isLoading } = usePromptVersions(agentName);
  const createMutation = useCreatePrompt(agentName);
  const activateMutation = useActivatePrompt(agentName);
  const [adding, setAdding] = useState(false);
  const [content, setContent] = useState("");
  const [note, setNote] = useState("");

  function handleCreate() {
    if (!content.trim()) return;
    createMutation.mutate({ content, change_note: note || undefined, activate: false }, {
      onSuccess: () => { setAdding(false); setContent(""); setNote(""); }
    });
  }

  return (
    <Card>
      <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-white/[0.05]">
        <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-lg">{agentName}</span>
        <Button size="xs" variant="secondary" onClick={() => setAdding((v) => !v)}>
          {adding ? "Cancel" : "+ Version"}
        </Button>
      </div>
      <CardContent className="space-y-3">
        {adding && (
          <div className="rounded-lg border border-indigo-500/20 bg-indigo-500/[0.04] p-3 space-y-2">
            <textarea className={cn(inputCls, "font-mono resize-none")} rows={4} placeholder="Prompt content…" value={content} onChange={(e) => setContent(e.target.value)} />
            <input className={inputCls} placeholder="Change note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
            <Button size="sm" onClick={handleCreate} loading={createMutation.isPending}>Save</Button>
          </div>
        )}

        {isLoading && <p className="text-xs text-[var(--text-muted)]">Loading…</p>}
        {!isLoading && (!versions || versions.length === 0) && (
          <p className="text-xs text-[var(--text-muted)] py-2">No versions yet.</p>
        )}

        {versions?.map((v) => (
          <div key={v.id} className="rounded-lg border border-white/[0.06] p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-[var(--text-secondary)]">v{v.version}</span>
                {v.is_active && (
                  <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full">active</span>
                )}
                {v.change_note && <span className="text-[10px] text-[var(--text-muted)]">{v.change_note}</span>}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[var(--text-muted)]">{formatDate(v.created_at)}</span>
                {!v.is_active && (
                  <Button size="xs" variant="ghost" onClick={() => activateMutation.mutate(v.version)} loading={activateMutation.isPending}>
                    Activate
                  </Button>
                )}
              </div>
            </div>
            <pre className="rounded-lg bg-white/[0.03] border border-white/[0.05] p-3 text-xs text-[var(--text-muted)] font-mono whitespace-pre-wrap overflow-auto max-h-28">
              {v.content}
            </pre>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export default function PromptsPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-indigo-500/10"><FlaskConical className="h-4 w-4 text-indigo-400" /></div>
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Prompt Registry</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Version and switch agent prompts without redeploying</p>
        </div>
      </div>
      <div className="space-y-4">
        {AGENTS.map((a) => <AgentPrompts key={a} agentName={a} />)}
      </div>
    </div>
  );
}
