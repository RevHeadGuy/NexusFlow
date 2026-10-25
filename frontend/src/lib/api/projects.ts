import { api } from "./client";
import type { Project, ProjectBrief, ProjectCreate } from "@/lib/types/api";

export const projectsApi = {
  list: () => api.get<Project[]>("/projects"),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) => api.post<Project>("/projects", data),
  update: (id: string, data: Partial<ProjectCreate>) =>
    api.patch<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete<{ status: string; id: string }>(`/projects/${id}`),

  analyzeIdea: (id: string) => api.post<ProjectBrief>(`/projects/${id}/idea-analysis`),
  getBrief: (id: string) => api.get<ProjectBrief>(`/projects/${id}/idea-analysis`),
  saveBrief: (id: string, data: Omit<ProjectBrief, "id" | "project_id" | "created_at" | "updated_at">) =>
    api.put<ProjectBrief>(`/projects/${id}/idea-analysis`, data),
};
