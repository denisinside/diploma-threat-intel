import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useAuth } from "@/hooks/useAuth";
import { leaksApi } from "@/features/leaks/api";
import { getLeakAnalyticsQueryKey } from "@/features/leaks/hooks";
import { vulnsApi } from "@/features/vulns/api";
import { getVulnStatsQueryKey } from "@/features/vulns/hooks";

export function Layout() {
  const queryClient = useQueryClient();
  const { session } = useAuth();
  const companyId = session?.user?.company_id;

  useEffect(() => {
    if (!session?.token) return;

    const vulnStatsParams = { all: true, company_id: companyId };
    const leakAnalyticsParams = {};

    void queryClient.prefetchQuery({
      queryKey: getVulnStatsQueryKey(vulnStatsParams),
      queryFn: () => vulnsApi.getStats(vulnStatsParams),
    });
    void queryClient.prefetchQuery({
      queryKey: getLeakAnalyticsQueryKey(leakAnalyticsParams, companyId),
      queryFn: () => leaksApi.getAnalytics({ company_id: companyId }),
    });
  }, [queryClient, session?.token, companyId]);

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
