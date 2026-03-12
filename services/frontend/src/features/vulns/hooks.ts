import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { vulnsApi, type VulnSearchParams, type VulnStatsParams } from "./api";

export function useVulnSearch(params: VulnSearchParams) {
  return useQuery({
    queryKey: ["vulns", "search", params],
    queryFn: () => vulnsApi.search(params),
    enabled: true,
  });
}

export function getVulnStatsQueryKey(params: VulnStatsParams) {
  return ["vulns", "stats", params] as const;
}

export function useVulnStats(params: VulnStatsParams) {
  return useQuery({
    queryKey: getVulnStatsQueryKey(params),
    queryFn: () => vulnsApi.getStats(params),
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
  });
}

export function useVulnById(id: string | null) {
  return useQuery({
    queryKey: ["vulns", id],
    queryFn: () => vulnsApi.getById(id!),
    enabled: Boolean(id),
  });
}

export function useEcosystems() {
  return useQuery({
    queryKey: ["ecosystems"],
    queryFn: () => vulnsApi.getEcosystems(0, 200),
  });
}
