"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, Link2 } from "lucide-react";
import { api } from "@/lib/api/client";

function AcceptInvite() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function accept() {
    setBusy(true);
    setError("");
    try {
      const result = await api.post<{ project_id: string; role: string; status: string }>("/auth/invitations/accept", { token });
      router.replace(`/projects/${result.project_id}/team`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not accept this invitation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-[#0a0a0f] px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#11111a] p-7 text-center shadow-2xl">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-400/10 text-indigo-300"><Link2 className="h-5 w-5" /></div>
        <h1 className="mt-4 text-xl font-semibold">Join a NexusFlow project</h1>
        <p className="mt-2 text-sm leading-6 text-slate-400">Accept this invitation to add the shared project to your workspace.</p>
        {error && <p role="alert" className="mt-4 rounded-lg border border-rose-400/20 bg-rose-400/10 p-3 text-xs text-rose-200">{error}</p>}
        <button type="button" onClick={accept} disabled={!token || busy} className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-indigo-500 px-4 text-sm font-semibold hover:bg-indigo-400 disabled:opacity-50">
          {busy ? "Accepting…" : "Accept invitation"}<CheckCircle2 className="h-4 w-4" />
        </button>
        {!token && <p className="mt-3 text-xs text-slate-500">The invitation link is missing its token.</p>}
        <p className="mt-4 text-[11px] text-slate-500">Sign in using the email address the invitation was sent to.</p>
      </div>
    </div>
  );
}

export default function AcceptInvitePage() {
  // useSearchParams requires a Suspense boundary so the rest of the route can prerender.
  return (
    <Suspense>
      <AcceptInvite />
    </Suspense>
  );
}
