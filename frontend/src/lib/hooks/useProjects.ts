import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/lib/api/projects";
import type { ProjectBrief, ProjectCreate } from "@/lib/types/api";

export const projectKeys = {
  all: ["projects"] as const,
  detail: (id: string) => ["projects", id] as const,
  brief: (id: string) => ["projects", id, "brief"] as const,
};

export function useProjects() {
  return useQuery({ queryKey: projectKeys.all, queryFn: projectsApi.list });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: !!id,
  });
}

export function useProjectBrief(id: string) {
  return useQuery({
    queryKey: projectKeys.brief(id),
    queryFn: () => projectsApi.getBrief(id),
    enabled: !!id,
    retry: false,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

export function useAnalyzeIdea(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => projectsApi.analyzeIdea(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: projectKeys.brief(projectId) });
      qc.invalidateQueries({ queryKey: projectKeys.detail(projectId) });
      qc.invalidateQueries({ queryKey: ["artifacts", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow-review-queue"] });
    },
  });
}

export function useSaveProjectBrief(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<ProjectBrief, "id" | "project_id" | "created_at" | "updated_at">) =>
      projectsApi.saveBrief(projectId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: projectKeys.brief(projectId) });
      qc.invalidateQueries({ queryKey: ["artifacts", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow", projectId] });
      qc.invalidateQueries({ queryKey: ["workflow-review-queue"] });
    },
  });
}
