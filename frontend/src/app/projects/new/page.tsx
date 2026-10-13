"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { ArrowLeft, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useCreateProject } from "@/lib/hooks/useProjects";
import { PROJECT_TEMPLATES } from "@/lib/templates";

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  description: z.string().optional(),
  idea: z.string().min(20, "Describe your idea in at least 20 characters"),
});

type FormData = z.infer<typeof schema>;

function Field({ id, label, hint, error, children }: { id: string; label: string; hint?: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="text-sm font-medium text-[var(--text-primary)]">{label}</label>
        {hint && <span className="text-xs text-[var(--text-muted)]">{hint}</span>}
      </div>
      {children}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

const inputCls = "w-full rounded-lg bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all";

export default function NewProjectPage() {
  const router = useRouter();
  const createMutation = useCreateProject();
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  function onSubmit(data: FormData) {
    createMutation.mutate(data, {
      onSuccess: (project) => router.push(`/projects/${project.id}`),
    });
  }

  return (
    <div className="mx-auto w-full max-w-3xl p-4 sm:p-6 lg:p-8 animate-fade-in-up">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors mb-8"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back
      </button>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-indigo-500/10">
            <Sparkles className="h-5 w-5 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">New Project</h1>
        </div>
        <p className="text-sm text-[var(--text-muted)] leading-relaxed">
          Capture the idea first. Next, generate its structured brief and move through research planning, feasibility, requirements, and review with an approval at each stage.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-[var(--text-primary)]">Start from a project template</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Templates prefill a starting idea. You can edit everything before creating the project.</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            {PROJECT_TEMPLATES.map((template) => (
              <button
                key={template.key}
                type="button"
                onClick={() => {
                  setSelectedTemplate(template.key);
                  setValue("name", template.projectName, { shouldValidate: true });
                  setValue("description", template.description, { shouldValidate: true });
                  setValue("idea", template.idea, { shouldValidate: true });
                }}
                aria-pressed={selectedTemplate === template.key}
                className={`rounded-xl border p-3 text-left transition-colors ${selectedTemplate === template.key ? "border-indigo-400/35 bg-indigo-500/10" : "border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.05]"}`}
              >
                <span className="block text-xs font-semibold text-[var(--text-primary)]">{template.name}</span>
                <span className="mt-1 block text-[11px] leading-relaxed text-[var(--text-muted)]">{template.description}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl surface p-6 space-y-5">
          <Field id="project-name" label="Project Name" error={errors.name?.message}>
            <input
              id="project-name"
              {...register("name")}
              className={inputCls}
              placeholder="e.g. Clinical Insights Platform"
              autoFocus
            />
          </Field>

          <Field id="project-description" label="Description" hint="Optional" error={errors.description?.message}>
            <input
              id="project-description"
              {...register("description")}
              className={inputCls}
              placeholder="One-line summary"
            />
          </Field>

          <Field
            id="project-idea"
            label="Your Idea"
            hint="Be specific — the more detail, the better the output"
            error={errors.idea?.message}
          >
            <textarea
              id="project-idea"
              {...register("idea")}
              rows={7}
              className={inputCls}
              placeholder="Describe your product idea in detail. What problem does it solve? Who are the users? What does success look like? What constraints exist?"
            />
          </Field>
        </div>

        {createMutation.isError && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3">
            <p className="text-xs text-red-400">{String(createMutation.error)}</p>
          </div>
        )}

        <div className="flex flex-col gap-3 sm:flex-row">
          <Button type="submit" size="lg" loading={createMutation.isPending} disabled={createMutation.isPending}>
            <Sparkles className="h-4 w-4" />
            Create Project
          </Button>
          <Button type="button" variant="ghost" size="lg" onClick={() => router.back()}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
