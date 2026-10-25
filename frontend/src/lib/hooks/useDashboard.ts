import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api/dashboard";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.stats,
    refetchInterval: 30_000, // refresh every 30s
  });
}

export function useViolations(projectId: string, unresolvedOnly = false) {
  return useQuery({
    queryKey: ["violations", projectId, unresolvedOnly],
    queryFn: () => dashboardApi.violations(projectId, unresolvedOnly),
    enabled: !!projectId,
  });
}
