import ForceGraph2D from "react-force-graph-2d";
import { useMemo } from "react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { useAssets } from "@/features/assets/hooks";
import { useLeakSources } from "@/features/leaks/hooks";
import { useTicketCount } from "@/features/tickets/hooks";
import { useAuth } from "@/hooks/useAuth";
import { normalizeSeverity } from "@/lib/format";
import { useVulnSearch } from "@/features/vulns/hooks";

const pieColors = ["#38BDF8", "#F59E0B", "#F97316", "#22C55E", "#A78BFA"];

export function OverviewPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;

  const { data: assets = [] } = useAssets(companyId);
  const { data: leakSources = [] } = useLeakSources();
  const { data: openTickets } = useTicketCount(companyId, "open");
  const { data: vulnSearchResult } = useVulnSearch({ q: "CVE" });
  const criticalVulns = vulnSearchResult?.items ?? [];

  const criticalCount = criticalVulns.filter(
    (item: { database_specific?: { severity?: string } }) =>
      normalizeSeverity(item.database_specific?.severity) === "critical"
  ).length;

  const leakSourceDistribution = useMemo(() => {
    const map = new Map<string, number>();
    leakSources.forEach((source) => {
      map.set(source.source_type ?? "other", (map.get(source.source_type ?? "other") ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [leakSources]);

  const assetsByType = useMemo(() => {
    const map = new Map<string, number>();
    assets.forEach((asset) => map.set(asset.type, (map.get(asset.type) ?? 0) + 1));
    return Array.from(map.entries()).map(([type, count]) => ({ type, count }));
  }, [assets]);

  const graphData = useMemo(
    () => ({
      nodes: [
        { id: "company", name: session?.user?.company_id ?? "Company Domain", color: "#38BDF8", val: 14 },
        { id: "source_1", name: "Telegram Source", color: "#F59E0B", val: 10 },
        { id: "source_2", name: "Forum Source", color: "#FB923C", val: 8 },
        { id: "asset_1", name: "portal.company.com", color: "#60A5FA", val: 9 },
        { id: "asset_2", name: "auth-api", color: "#60A5FA", val: 9 },
        { id: "leak", name: "Compromised Credentials", color: "#F97316", val: 12 },
      ],
      links: [
        { source: "source_1", target: "leak" },
        { source: "source_2", target: "leak" },
        { source: "leak", target: "company" },
        { source: "leak", target: "asset_1" },
        { source: "leak", target: "asset_2" },
      ],
    }),
    [session?.user?.company_id]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Overview</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Active Assets" value={assets.length} accent="sky" />
        <StatCard label="Leak Sources" value={leakSources.length} accent="amber" />
        <StatCard label="Critical Vulnerabilities" value={criticalCount} accent="amber" />
        <StatCard label="Open Tickets" value={openTickets?.count ?? 0} accent="sky" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <SectionCard title="Leak Path Analysis">
            <div className="h-[360px] rounded border border-slate-700/40 bg-slate-950/50">
              <ForceGraph2D
                graphData={graphData}
                nodeLabel="name"
                nodeRelSize={5}
                linkColor={() => "rgba(148,163,184,0.5)"}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = String(node.name ?? "");
                  const fontSize = 13 / globalScale;
                  ctx.font = `${fontSize}px Roboto Condensed`;
                  ctx.fillStyle = String(node.color ?? "#38BDF8");
                  ctx.beginPath();
                  ctx.arc(node.x ?? 0, node.y ?? 0, Number(node.val ?? 8), 0, 2 * Math.PI, false);
                  ctx.fill();
                  ctx.fillStyle = "#e2e8f0";
                  ctx.fillText(label, (node.x ?? 0) + 10, (node.y ?? 0) + 4);
                }}
              />
            </div>
          </SectionCard>
        </div>
        <SectionCard title="Source Distribution">
          <div className="h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={leakSourceDistribution} dataKey="value" nameKey="name" outerRadius={110}>
                  {leakSourceDistribution.map((entry, index) => (
                    <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Assets by Type">
        <div className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={assetsByType}>
              <XAxis dataKey="type" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Bar dataKey="count" fill="#38BDF8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </SectionCard>

      {!companyId ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`. Register user with a company to load scoped data.
        </p>
      ) : null}
    </div>
  );
}
