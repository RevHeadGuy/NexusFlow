"use client";

import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Crown, MailPlus, ShieldCheck, Trash2, Users, X } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api/client";
import { useAuth } from "@/app/providers";

type Role = "owner" | "editor" | "reviewer" | "viewer";
interface Member { user_id: string; email: string; display_name: string; role: Role; created_at: string }
interface Invitation { id: string; project_id: string; email: string; role: Role; expires_at: string; invite_token?: string | null }
const roles: Role[] = ["editor", "reviewer", "viewer"];

export default function ProjectTeamPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("reviewer");
  const [inviteUrl, setInviteUrl] = useState("");
  const [error, setError] = useState("");
  const key = ["project-members", projectId];
  const members = useQuery({ queryKey: key, queryFn: () => api.get<Member[]>(`/projects/${projectId}/members`) });
  const canManageTeam = members.data?.some((member) => member.user_id === user?.id && member.role === "owner") ?? false;
  const invitations = useQuery({ queryKey: ["project-invitations", projectId], queryFn: () => api.get<Invitation[]>(`/projects/${projectId}/invitations`), enabled: canManageTeam });

  const invite = useMutation({
    mutationFn: () => api.post<Invitation>(`/projects/${projectId}/invitations`, { email, role }),
    onSuccess: (result) => {
      const url = `${window.location.origin}/invite?token=${encodeURIComponent(result.invite_token ?? "")}`;
      setInviteUrl(url);
      setEmail("");
      queryClient.invalidateQueries({ queryKey: ["project-invitations", projectId] });
    },
    onError: (caught) => setError(caught instanceof Error ? caught.message : "Could not create invitation."),
  });
  const changeRole = useMutation({
    mutationFn: ({ userId, nextRole }: { userId: string; nextRole: Role }) =>
      api.patch<Member>(`/projects/${projectId}/members/${userId}`, { role: nextRole }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });
  const remove = useMutation({
    mutationFn: (userId: string) => api.delete<void>(`/projects/${projectId}/members/${userId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });
  const transferOwnership = useMutation({
    mutationFn: (userId: string) => api.post<Member>(`/projects/${projectId}/members/${userId}/transfer-ownership`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });
  const revokeInvite = useMutation({
    mutationFn: (inviteId: string) => api.delete<void>(`/projects/${projectId}/invitations/${inviteId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["project-invitations", projectId] }),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setInviteUrl("");
    invite.mutate();
  }

  async function copyInvite() {
    if (inviteUrl) await navigator.clipboard.writeText(inviteUrl);
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-5 sm:p-8">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border border-indigo-400/15 bg-indigo-500/10 p-2.5 text-indigo-300"><Users className="h-5 w-5" /></div>
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-indigo-300">Project access</p><h1 className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">Team</h1><p className="mt-1 text-sm text-[var(--text-secondary)]">Invite collaborators and choose what they can do in this project.</p></div>
      </div>

      {canManageTeam && <Card className="p-5 sm:p-6">
        <div className="mb-4 flex items-center gap-2"><MailPlus className="h-4 w-4 text-indigo-300" /><h2 className="text-sm font-semibold text-[var(--text-primary)]">Invite someone</h2></div>
        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[1fr_170px_auto]">
          <label className="text-xs text-[var(--text-secondary)]">Email address<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="teammate@example.com" className="mt-1.5 h-10 w-full rounded-lg border border-white/[0.09] bg-black/20 px-3 text-sm text-[var(--text-primary)] outline-none focus:border-indigo-400" /></label>
          <label className="text-xs text-[var(--text-secondary)]">Project role<select value={role} onChange={(event) => setRole(event.target.value as Role)} className="mt-1.5 h-10 w-full rounded-lg border border-white/[0.09] bg-[#101018] px-3 text-sm text-[var(--text-primary)] outline-none focus:border-indigo-400">{roles.map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select></label>
          <button disabled={invite.isPending} className="mt-auto inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-indigo-500 px-4 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60">{invite.isPending ? "Creating…" : "Create invite"}</button>
        </form>
        <p className="mt-3 text-[11px] leading-5 text-[var(--text-muted)]">NexusFlow creates a single-use, seven-day invite link. Copy and send it to the teammate; email delivery is not configured.</p>
        {error && <p role="alert" className="mt-3 rounded-lg border border-rose-400/20 bg-rose-400/10 p-3 text-xs text-rose-200">{error}</p>}
        {inviteUrl && <div className="mt-4 rounded-lg border border-emerald-400/20 bg-emerald-400/[0.06] p-4"><p className="text-xs font-medium text-emerald-200">Invitation created · copy this link now</p><div className="mt-2 flex flex-col gap-2 sm:flex-row"><input readOnly value={inviteUrl} aria-label="Invitation link" className="h-10 min-w-0 flex-1 rounded-md border border-white/10 bg-black/20 px-3 text-xs text-slate-200" /><button type="button" onClick={copyInvite} className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-white/10 px-3 text-xs text-slate-200 hover:bg-white/5"><Copy className="h-3.5 w-3.5" />Copy link</button></div></div>}
      </Card>}

      <Card className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4"><div><h2 className="text-sm font-semibold text-[var(--text-primary)]">Members</h2><p className="mt-1 text-xs text-[var(--text-muted)]">{members.data?.length ?? 0} people with access</p></div><ShieldCheck className="h-4 w-4 text-emerald-300" /></div>
        {members.isLoading ? <p className="p-5 text-sm text-[var(--text-muted)]">Loading team…</p> : members.isError ? <p className="p-5 text-sm text-rose-300">Could not load project members.</p> : <div className="divide-y divide-white/[0.05]">{members.data?.map((member) => <div key={member.user_id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center"><div className="flex min-w-0 flex-1 items-center gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-xs font-semibold text-slate-200">{member.display_name.slice(0, 1).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-sm font-medium text-[var(--text-primary)]">{member.display_name}</p><p className="truncate text-xs text-[var(--text-muted)]">{member.email}</p></div></div><div className="flex items-center gap-2"><select aria-label={`Role for ${member.display_name}`} value={member.role} disabled={!canManageTeam || member.role === "owner" || changeRole.isPending} onChange={(event) => changeRole.mutate({ userId: member.user_id, nextRole: event.target.value as Role })} className="h-9 rounded-md border border-white/[0.08] bg-[#101018] px-2.5 text-xs text-slate-200 disabled:opacity-70">{member.role === "owner" && <option value="owner">Owner</option>}{roles.map((item) => <option key={item} value={item}>{item[0].toUpperCase() + item.slice(1)}</option>)}</select>{canManageTeam && member.role !== "owner" && <><button type="button" aria-label={`Transfer ownership to ${member.display_name}`} title="Transfer ownership" onClick={() => { if (window.confirm(`Transfer project ownership to ${member.display_name}? Your role will become editor.`)) transferOwnership.mutate(member.user_id); }} className="rounded-md p-2 text-slate-500 hover:bg-amber-400/10 hover:text-amber-200"><Crown className="h-4 w-4" /></button><button type="button" aria-label={`Remove ${member.display_name}`} title="Remove member" onClick={() => { if (window.confirm(`Remove ${member.display_name} from this project?`)) remove.mutate(member.user_id); }} className="rounded-md p-2 text-slate-500 hover:bg-rose-400/10 hover:text-rose-300"><Trash2 className="h-4 w-4" /></button></>}</div></div>)}</div>}
      </Card>

      {canManageTeam && <Card className="p-5">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">Pending invitations</h2>
        {invitations.data?.length ? <div className="mt-3 space-y-2">{invitations.data.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white/[0.03] px-3 py-2.5"><div><p className="text-xs text-slate-200">{item.email}</p><p className="mt-1 text-[10px] text-slate-500">{item.role} · expires {new Date(item.expires_at).toLocaleDateString()}</p></div><div className="flex items-center gap-2"><span className="rounded-full border border-amber-300/15 bg-amber-300/[0.06] px-2.5 py-1 text-[10px] text-amber-200">Awaiting acceptance</span><button type="button" title="Revoke invitation" aria-label={`Revoke invitation for ${item.email}`} onClick={() => revokeInvite.mutate(item.id)} className="rounded-md p-1.5 text-slate-500 hover:bg-rose-400/10 hover:text-rose-300"><X className="h-3.5 w-3.5" /></button></div></div>)}</div> : <p className="mt-2 text-xs text-[var(--text-muted)]">No pending invitations.</p>}
      </Card>}
    </div>
  );
}
