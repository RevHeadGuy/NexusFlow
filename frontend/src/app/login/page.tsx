"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, LockKeyhole, Sparkles } from "lucide-react";
import { useAuth } from "../providers";

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") await register(email, displayName, password);
      else await login(email, password);
      const requestedNext = new URLSearchParams(window.location.search).get("next");
      const safeNext = requestedNext?.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : "/";
      window.location.assign(safeNext);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-[#0a0a0f] px-4 py-10 text-white">
      {/* Ambient backdrop */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute -right-40 top-1/4 h-96 w-96 rounded-full bg-purple-600/15 blur-[120px]" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-teal-500/10 blur-[120px]" />
      </div>

      <div className="relative w-full max-w-[440px] animate-fade-in-up">
        <div className="mb-8 flex items-center justify-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/30"><Sparkles className="h-5 w-5" /></div>
          <div><p className="text-lg font-semibold tracking-tight">NexusFlow</p><p className="text-xs text-slate-400">A workspace for reviewed project decisions</p></div>
        </div>
        <div className="glass-bright rounded-2xl p-7 shadow-2xl shadow-black/40 sm:p-8">
          <div className="mb-6">
            <p className="mb-2 inline-flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-indigo-300"><LockKeyhole className="h-3.5 w-3.5" />Private workspace</p>
            <h1 className="text-2xl font-semibold">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">Sign in to access your projects or join a workspace invitation.</p>
          </div>
          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && <label className="block text-sm text-slate-300">Your name<input required maxLength={120} autoComplete="name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="mt-1.5 h-11 w-full rounded-lg border border-white/10 bg-black/20 px-3 text-sm text-white outline-none transition-all duration-200 placeholder:text-slate-500 focus:border-indigo-400/70 focus:bg-black/30 focus:ring-2 focus:ring-indigo-500/20" /></label>}
            <label className="block text-sm text-slate-300">Email<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1.5 h-11 w-full rounded-lg border border-white/10 bg-black/20 px-3 text-sm text-white outline-none transition-all duration-200 placeholder:text-slate-500 focus:border-indigo-400/70 focus:bg-black/30 focus:ring-2 focus:ring-indigo-500/20" /></label>
            <label className="block text-sm text-slate-300">Password<input required minLength={mode === "register" ? 10 : 1} maxLength={128} type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1.5 h-11 w-full rounded-lg border border-white/10 bg-black/20 px-3 text-sm text-white outline-none transition-all duration-200 placeholder:text-slate-500 focus:border-indigo-400/70 focus:bg-black/30 focus:ring-2 focus:ring-indigo-500/20" />{mode === "register" && <span className="mt-1 block text-[11px] text-slate-500">Use at least 10 characters.</span>}</label>
            {error && <p role="alert" className="rounded-lg border border-rose-400/20 bg-rose-400/10 px-3 py-2.5 text-xs leading-5 text-rose-200">{error}</p>}
            <button disabled={busy} className="group flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-b from-indigo-500 to-indigo-600 px-4 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:from-indigo-400 hover:to-indigo-500 hover:shadow-indigo-500/40 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}<ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-400">
            {mode === "login" ? "New to NexusFlow?" : "Already have an account?"}{" "}
            <button type="button" onClick={() => { setError(""); setMode(mode === "login" ? "register" : "login"); }} className="font-medium text-indigo-300 hover:text-indigo-200">{mode === "login" ? "Create an account" : "Sign in"}</button>
          </p>
        </div>
        <p className="mt-5 text-center text-[11px] leading-5 text-slate-500">Your account can only access projects you own or have been invited to.</p>
      </div>
    </div>
  );
}
