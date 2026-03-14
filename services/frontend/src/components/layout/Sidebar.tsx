import { useCallback } from "react";
import { NavLink } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Server,
  ShieldAlert,
  Bug,
  Ticket,
  Bell,
  Settings,
  Users,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useIsAdmin, useIsSuperAdmin } from "@/hooks/useRoleGuard";
import { leaksApi } from "@/features/leaks/api";
import { getLeakAnalyticsQueryKey } from "@/features/leaks/hooks";
import { vulnsApi } from "@/features/vulns/api";
import { getVulnStatsQueryKey } from "@/features/vulns/hooks";

const baseNavItems = [
  { to: "/overview", icon: LayoutDashboard, label: "OVERVIEW" },
  { to: "/assets", icon: Server, label: "ASSETS" },
  { to: "/leaks", icon: ShieldAlert, label: "LEAKS" },
  { to: "/vulnerabilities", icon: Bug, label: "VULNERABILITIES" },
  { to: "/tickets", icon: Ticket, label: "TICKETS" },
  { to: "/subscriptions", icon: Bell, label: "SUBSCRIPTIONS" },
  { to: "/settings", icon: Settings, label: "SETTINGS" },
];

export function Sidebar() {
  const queryClient = useQueryClient();
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const isSuperAdmin = useIsSuperAdmin();
  const isCompanyAdmin = useIsAdmin();

  const navItems = [
    ...baseNavItems,
    ...(isCompanyAdmin ? [{ to: "/team", icon: Users, label: "TEAM" }] : []),
    ...(isSuperAdmin ? [{ to: "/admin/company-requests", icon: Building2, label: "COMPANY REQUESTS" }] : []),
  ];

  const prefetchByRoute = useCallback(
    (to: string) => {
      if (!session?.token) return;
      if (to === "/vulnerabilities") {
        const params = { all: true, company_id: companyId };
        void queryClient.prefetchQuery({
          queryKey: getVulnStatsQueryKey(params),
          queryFn: () => vulnsApi.getStats(params),
          staleTime: 5 * 60 * 1000,
        });
      }
      if (to === "/leaks") {
        const params = {};
        void queryClient.prefetchQuery({
          queryKey: getLeakAnalyticsQueryKey(params, companyId),
          queryFn: () => leaksApi.getAnalytics({ company_id: companyId }),
          staleTime: 5 * 60 * 1000,
        });
      }
    },
    [queryClient, session?.token, companyId]
  );

  return (
    <aside className="w-56 flex-shrink-0 glass-panel rounded-none border-r border-slate-700/50 flex flex-col">
      <div className="p-4 border-b border-slate-700/50">
        <h1 className="text-xs font-semibold text-tactical-sky tracking-[0.2em]">
          C.L.E.A.R.
        </h1>
        <p className="text-xs text-slate-400 mt-0.5 leading-tight">
          Corporate Leak & Exploit Alert Radar
        </p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onMouseEnter={() => prefetchByRoute(to)}
            onFocus={() => prefetchByRoute(to)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-sky-500/20 text-tactical-sky border-l-2 border-tactical-sky"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              )
            }
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
