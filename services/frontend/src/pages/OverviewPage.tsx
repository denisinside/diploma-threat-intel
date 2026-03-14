import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { useCompanyRequests } from "@/features/admin/hooks";
import { useAssets } from "@/features/assets/hooks";
import { useLeakAnalytics, useLeakSources } from "@/features/leaks/hooks";
import { useCompanyUsers } from "@/features/team/hooks";
import { useTicketCount } from "@/features/tickets/hooks";
import { useAuth } from "@/hooks/useAuth";
import { useIsAdmin, useIsSuperAdmin } from "@/hooks/useRoleGuard";
import { formatDate, normalizeSeverity } from "@/lib/format";
import { useVulnSearch } from "@/features/vulns/hooks";

const pieColors = ["#38BDF8", "#F59E0B", "#F97316", "#22C55E", "#A78BFA"];
const compactNumberFormatter = new Intl.NumberFormat("en", {
  notation: "compact",
  maximumFractionDigits: 1,
});

function formatCompactNumber(value: number) {
  if (!Number.isFinite(value)) return "0";
  return compactNumberFormatter.format(value);
}

export function OverviewPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const isAdmin = useIsAdmin();
  const isSuperAdmin = useIsSuperAdmin();

  const { data: assets = [], isLoading: isAssetsLoading, error: assetsError } = useAssets(companyId);
  const { data: leakSources = [], isLoading: isLeakSourcesLoading, error: leakSourcesError } = useLeakSources();
  const { data: openTickets, isLoading: isOpenLoading, error: openTicketsError } = useTicketCount(companyId, "open");
  const { data: inProgressTickets, isLoading: isInProgressLoading, error: inProgressError } = useTicketCount(
    companyId,
    "in_progress"
  );
  const { data: resolvedTickets, isLoading: isResolvedLoading, error: resolvedError } = useTicketCount(
    companyId,
    "resolved"
  );
  const { data: vulnSearchResult } = useVulnSearch({ q: "CVE" });
  const {
    data: leakAnalytics,
    isLoading: isLeakAnalyticsLoading,
    error: leakAnalyticsError,
  } = useLeakAnalytics({}, companyId);
  const criticalVulns = vulnSearchResult?.items ?? [];

  const criticalCount = criticalVulns.filter(
    (item: { database_specific?: { severity?: string } }) =>
      normalizeSeverity(item.database_specific?.severity) === "critical"
  ).length;

  const sourceDistribution = useMemo(() => {
    if ((leakAnalytics?.charts.source_distribution?.length ?? 0) > 0) {
      return leakAnalytics?.charts.source_distribution.map((item) => ({
        name: item.label || item.source_id,
        value: item.count,
      }));
    }
    const map = new Map<string, number>();
    leakSources.forEach((source) => {
      const key = source.source_type ?? "other";
      map.set(key, (map.get(key) ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [leakAnalytics?.charts.source_distribution, leakSources]);

  const leakTrend = useMemo(() => {
    const raw = leakAnalytics?.charts.trend ?? [];
    return raw.slice(-14).map((item) => ({
      date: item.date,
      total: item.total,
      company: item.company,
    }));
  }, [leakAnalytics?.charts.trend]);

  const topDomains = useMemo(() => {
    return (leakAnalytics?.charts.top_domains ?? []).slice(0, 6);
  }, [leakAnalytics?.charts.top_domains]);

  const ticketsBreakdown = useMemo(
    () => [
      { status: "open", count: openTickets?.count ?? 0 },
      { status: "in_progress", count: inProgressTickets?.count ?? 0 },
      { status: "resolved", count: resolvedTickets?.count ?? 0 },
    ],
    [openTickets?.count, inProgressTickets?.count, resolvedTickets?.count]
  );

  const hasTicketCountsError = Boolean(openTicketsError || inProgressError || resolvedError);
  const isTicketCountsLoading = isOpenLoading || isInProgressLoading || isResolvedLoading;

  const kpiError = assetsError || leakSourcesError || openTicketsError;

  const leakOverviewKpis = useMemo(() => {
    const kpis = leakAnalytics?.kpis;
    if (!kpis) return [];
    return [
      { label: "Compromised Records", value: kpis.total_compromised_records },
      { label: "New Leaks (24h)", value: kpis.new_leaks_24h },
      { label: "New Leaks (7d)", value: kpis.new_leaks_7d },
      { label: "Critical Alerts", value: kpis.critical_alerts },
    ];
  }, [leakAnalytics?.kpis]);

  const isCompanyScopedRole = session?.user?.role !== "super_admin";

  const hasNoCoreData =
    !isAssetsLoading &&
    !isLeakSourcesLoading &&
    !isOpenLoading &&
    assets.length === 0 &&
    leakSources.length === 0 &&
    (openTickets?.count ?? 0) === 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Assets"
          value={isAssetsLoading ? "..." : assets.length}
          accent="sky"
          hint="Company inventory size"
        />
        <StatCard
          label="Open Tickets"
          value={isOpenLoading ? "..." : openTickets?.count ?? 0}
          accent="amber"
          hint="Unresolved security work"
        />
        <StatCard
          label="Critical Vulnerabilities"
          value={criticalCount}
          accent="amber"
          hint="From vulnerability search index"
        />
        <StatCard
          label="Leak Sources"
          value={isLeakSourcesLoading ? "..." : leakSources.length}
          accent="sky"
          hint="Tracked source entries"
        />
      </div>

      {kpiError ? (
        <p className="text-sm text-red-300">Some KPI data failed to load: {(kpiError as Error).message}</p>
      ) : null}
      {hasNoCoreData ? (
        <p className="text-sm text-slate-400">No security activity data yet. Add assets or ingest sources to populate this dashboard.</p>
      ) : null}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <SectionCard title="Leak Activity Trend">
            {isLeakAnalyticsLoading ? (
              <p className="text-slate-400">Loading leak analytics...</p>
            ) : leakAnalyticsError ? (
              <p className="text-sm text-red-300">{(leakAnalyticsError as Error).message}</p>
            ) : leakTrend.length === 0 ? (
              <p className="text-slate-400">No trend data available for current scope.</p>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                  {leakOverviewKpis.map((item) => (
                    <div
                      key={item.label}
                      className="rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2"
                    >
                      <p className="text-[11px] uppercase tracking-wide text-slate-400">{item.label}</p>
                      <p className="text-lg font-semibold text-slate-100">{item.value}</p>
                    </div>
                  ))}
                </div>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={leakTrend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="date" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" tickFormatter={formatCompactNumber} />
                      <Tooltip formatter={(value: number) => formatCompactNumber(Number(value))} />
                      <Line type="monotone" dataKey="total" stroke="#38BDF8" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="company" stroke="#F59E0B" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </SectionCard>
        </div>
        <SectionCard title="Source Distribution">
          {isLeakAnalyticsLoading && sourceDistribution.length === 0 ? (
            <p className="text-slate-400">Loading source distribution...</p>
          ) : sourceDistribution.length === 0 ? (
            <p className="text-slate-400">No source distribution data.</p>
          ) : (
            <div className="h-[360px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={sourceDistribution} dataKey="value" nameKey="name" outerRadius={110}>
                    {sourceDistribution.map((entry, index) => (
                      <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <SectionCard title="Tickets Breakdown">
            {isTicketCountsLoading ? (
              <p className="text-slate-400">Loading ticket status counts...</p>
            ) : hasTicketCountsError ? (
              <p className="text-sm text-red-300">
                Failed to load ticket counts:{" "}
                {(openTicketsError || inProgressError || resolvedError as Error).message}
              </p>
            ) : (
              <div className="h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ticketsBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="status" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip />
                    <Bar dataKey="count" fill="#38BDF8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </SectionCard>
        </div>
        <SectionCard title="Top Leaked Domains">
          {isLeakAnalyticsLoading ? (
            <p className="text-slate-400">Loading top domains...</p>
          ) : leakAnalyticsError ? (
            <p className="text-sm text-red-300">{(leakAnalyticsError as Error).message}</p>
          ) : topDomains.length === 0 ? (
            <p className="text-slate-400">No domain leak data available.</p>
          ) : (
            <div className="space-y-2">
              {topDomains.map((domain) => (
                <div
                  key={domain.domain}
                  className="flex items-center justify-between rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2"
                >
                  <span className="text-sm text-slate-200">{domain.domain || "unknown"}</span>
                  <span className="text-sm font-semibold text-tactical-amber">{domain.count}</span>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>

      {isAdmin ? <AdminTeamHealthSection /> : null}
      {isSuperAdmin ? <SuperAdminRequestsSection /> : null}

      {!companyId && isCompanyScopedRole ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`. Register user with a company to load scoped data.
        </p>
      ) : null}
    </div>
  );
}

function AdminTeamHealthSection() {
  const { data: users = [], isLoading, error } = useCompanyUsers();

  const roleCounts = useMemo(() => {
    const map = new Map<string, number>();
    users.forEach((user) => {
      const role = user.role || "unknown";
      map.set(role, (map.get(role) ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([role, count]) => ({ role, count }));
  }, [users]);

  const analystsCount = users.filter((user) => user.role === "analyst").length;
  const adminsCount = users.filter((user) => user.role === "admin").length;
  const viewersCount = users.filter((user) => user.role === "viewer").length;

  return (
    <SectionCard title="Team Health (Admin)">
      {isLoading ? (
        <p className="text-slate-400">Loading team members...</p>
      ) : error ? (
        <p className="text-sm text-red-300">{(error as Error).message}</p>
      ) : users.length === 0 ? (
        <p className="text-slate-400">No users found for your company.</p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <StatCard label="Team Members" value={users.length} accent="sky" />
            <StatCard label="Analysts" value={analystsCount} accent="amber" />
            <StatCard label="Admins" value={adminsCount} accent="sky" />
            <StatCard label="Viewers" value={viewersCount} accent="sky" />
          </div>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={roleCounts}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="role" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="count" fill="#A78BFA" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </SectionCard>
  );
}

function SuperAdminRequestsSection() {
  const { data: requests = [], isLoading, error } = useCompanyRequests();

  const statusCounts = useMemo(() => {
    const map = new Map<string, number>();
    requests.forEach((item) => {
      const status = item.status || "unknown";
      map.set(status, (map.get(status) ?? 0) + 1);
    });
    return {
      pending: map.get("pending") ?? 0,
      approved: map.get("approved") ?? 0,
      rejected: map.get("rejected") ?? 0,
    };
  }, [requests]);

  const pendingRequests = useMemo(
    () =>
      requests
        .filter((item) => item.status === "pending")
        .sort((a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime())
        .slice(0, 5),
    [requests]
  );

  return (
    <SectionCard title="Company Requests (Super Admin)">
      {isLoading ? (
        <p className="text-slate-400">Loading company requests...</p>
      ) : error ? (
        <p className="text-sm text-red-300">{(error as Error).message}</p>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <StatCard label="Pending" value={statusCounts.pending} accent="amber" />
            <StatCard label="Approved" value={statusCounts.approved} accent="sky" />
            <StatCard label="Rejected" value={statusCounts.rejected} accent="sky" />
          </div>
          {pendingRequests.length === 0 ? (
            <p className="text-slate-400">No pending requests right now.</p>
          ) : (
            <div className="space-y-2">
              {pendingRequests.map((request) => (
                <div
                  key={request._id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-200">{request.name}</p>
                    <p className="text-xs text-slate-400">{request.domain}</p>
                  </div>
                  <span className="text-xs text-slate-400">{formatDate(request.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </SectionCard>
  );
}
