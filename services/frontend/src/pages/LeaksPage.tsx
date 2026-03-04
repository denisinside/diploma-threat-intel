import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { useLeakSearch, useLeakSources } from "@/features/leaks/hooks";
import type { LeakRecord } from "@/types";

const pieColors = ["#38BDF8", "#F59E0B", "#F97316", "#A78BFA", "#22C55E"];

type QueryType = "domain" | "email" | "email_pattern" | "q";

export function LeaksPage() {
  const [queryType, setQueryType] = useState<QueryType>("domain");
  const [searchValue, setSearchValue] = useState("");
  const [params, setParams] = useState<{ q?: string; domain?: string; email?: string; email_pattern?: string }>({});

  const { data: leaks = [], isLoading, error } = useLeakSearch(params);
  const { data: sources = [] } = useLeakSources();

  const columns = useMemo<Array<ColumnDef<LeakRecord>>>(
    () => [
      { header: "Email", accessorKey: "email" },
      { header: "Username", accessorKey: "username" },
      { header: "Domain", accessorKey: "domain" },
      { header: "Type", accessorKey: "leaktype" },
      {
        header: "Tags",
        cell: ({ row }) => (row.original.tags?.length ? row.original.tags.join(", ") : "—"),
      },
    ],
    []
  );

  const leaksByType = useMemo(() => {
    const map = new Map<string, number>();
    leaks.forEach((item) => map.set(item.leaktype ?? "other", (map.get(item.leaktype ?? "other") ?? 0) + 1));
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [leaks]);

  function onSearch() {
    if (!searchValue.trim()) return;
    setParams({ [queryType]: searchValue.trim() });
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Leaks</h1>

      <SectionCard title="Leak Filters">
        <div className="flex flex-wrap gap-3">
          <select
            value={queryType}
            onChange={(e) => setQueryType(e.target.value as QueryType)}
            className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
          >
            <option value="domain">Domain</option>
            <option value="email">Email</option>
            <option value="email_pattern">Email Pattern</option>
            <option value="q">Fulltext</option>
          </select>
          <input
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Type query..."
            className="min-w-[280px] flex-1 bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
          />
          <button
            type="button"
            onClick={onSearch}
            className="px-4 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15"
          >
            Search
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{(error as Error).message}</p> : null}
      </SectionCard>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <SectionCard title={`Compromised Data (${leaks.length})`}>
            {isLoading ? (
              <p className="text-slate-400">Loading...</p>
            ) : (
              <DataTable data={leaks} columns={columns} emptyText="Run a search to get leak records." />
            )}
          </SectionCard>
        </div>
        <div className="space-y-4">
          <SectionCard title="Leak Source Types">
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={leaksByType} dataKey="value" nameKey="name" outerRadius={75}>
                    {leaksByType.map((entry, index) => (
                      <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>
          <SectionCard title="Registered Sources">
            <p className="text-3xl font-semibold text-slate-100">{sources.length}</p>
            <p className="text-xs text-slate-500 mt-1">From Telegram/forum ingestion pipeline</p>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
