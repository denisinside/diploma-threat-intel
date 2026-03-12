import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { leaksApi } from "./api";

type SearchParams = {
  q?: string;
  domain?: string;
  email?: string;
  email_pattern?: string;
  skip?: number;
  limit?: number;
};

export function useLeakSources() {
  return useQuery({
    queryKey: ["leak-sources"],
    queryFn: () => leaksApi.getSources(0, 300),
  });
}

export function useLeakSearch(params: SearchParams) {
  const enabled = Boolean(params.q || params.domain || params.email || params.email_pattern);
  return useQuery({
    queryKey: ["leak-search", params],
    queryFn: () => leaksApi.search(params),
    enabled,
  });
}

export function useLeakAnalytics(params: SearchParams, companyId?: string) {
  return useQuery({
    queryKey: getLeakAnalyticsQueryKey(params, companyId),
    queryFn: () => leaksApi.getAnalytics({ ...params, company_id: companyId }),
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
  });
}

export function getLeakAnalyticsQueryKey(params: SearchParams, companyId?: string) {
  return ["leak-analytics", params, companyId] as const;
}
