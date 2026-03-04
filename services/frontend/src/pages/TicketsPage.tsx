import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatCard } from "@/components/ui/StatCard";
import { useCreateTicket, useTicketCount, useTickets, useUpdateTicket } from "@/features/tickets/hooks";
import { useAuth } from "@/hooks/useAuth";
import { formatDate } from "@/lib/format";
import type { Ticket, TicketStatus } from "@/types";

const statusOptions: Array<TicketStatus | "all"> = [
  "all",
  "open",
  "in_progress",
  "resolved",
  "ignored",
  "false_positive",
];

export function TicketsPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const [status, setStatus] = useState<TicketStatus | "all">("all");
  const [assetId, setAssetId] = useState("");
  const [vulnerabilityId, setVulnerabilityId] = useState("");
  const [notes, setNotes] = useState("");
  const [ticketError, setTicketError] = useState("");
  const createTicket = useCreateTicket();
  const updateTicket = useUpdateTicket();

  const { data: tickets = [], isLoading, error } = useTickets(
    companyId,
    status === "all" ? undefined : status
  );
  const { data: openCount } = useTicketCount(companyId, "open");
  const { data: inProgressCount } = useTicketCount(companyId, "in_progress");
  const { data: resolvedCount } = useTicketCount(companyId, "resolved");

  const columns = useMemo<Array<ColumnDef<Ticket>>>(
    () => [
      { header: "Ticket ID", accessorKey: "_id" },
      { header: "Asset ID", accessorKey: "asset_id" },
      { header: "Vulnerability ID", accessorKey: "vulnerability_id" },
      {
        header: "Priority",
        cell: ({ row }) => <SeverityBadge severity={row.original.priority} />,
      },
      { header: "Status", accessorKey: "status" },
      {
        header: "Detected",
        cell: ({ row }) => formatDate(row.original.detected_at),
      },
      {
        header: "Actions",
        cell: ({ row }) => (
          <button
            type="button"
            disabled={row.original.status === "resolved"}
            onClick={() =>
              updateTicket.mutate({
                ticketId: row.original._id,
                payload: { status: "resolved" },
              })
            }
            className="text-xs text-emerald-300 hover:text-emerald-200 disabled:text-slate-500"
          >
            mark resolved
          </button>
        ),
      },
    ],
    [updateTicket]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Tickets</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Open" value={openCount?.count ?? 0} accent="amber" />
        <StatCard label="In Progress" value={inProgressCount?.count ?? 0} accent="sky" />
        <StatCard label="Resolved" value={resolvedCount?.count ?? 0} accent="sky" />
      </div>

      <SectionCard
        title={`Vulnerability Tickets (${tickets.length})`}
        rightSlot={
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as TicketStatus | "all")}
            className="bg-slate-800/60 border border-slate-600 rounded px-2 py-1 text-xs"
          >
            {statusOptions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        }
      >
        {companyId ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-4 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setTicketError("");
              if (!companyId) return;
              if (!assetId.trim() || !vulnerabilityId.trim()) {
                setTicketError("asset_id and vulnerability_id are required.");
                return;
              }
              createTicket.mutate(
                {
                  company_id: companyId,
                  asset_id: assetId.trim(),
                  vulnerability_id: vulnerabilityId.trim(),
                  notes: notes.trim() || undefined,
                },
                {
                  onSuccess: () => {
                    setAssetId("");
                    setVulnerabilityId("");
                    setNotes("");
                  },
                  onError: (mutationError) =>
                    setTicketError(
                      mutationError instanceof Error ? mutationError.message : "Failed to create ticket."
                    ),
                }
              );
            }}
          >
            <input
              value={assetId}
              onChange={(event) => setAssetId(event.target.value)}
              placeholder="Asset ID"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <input
              value={vulnerabilityId}
              onChange={(event) => setVulnerabilityId(event.target.value)}
              placeholder="Vulnerability ID (CVE-...)"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <input
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Notes (optional)"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createTicket.isPending ? "Creating..." : "Create ticket"}
            </button>
          </form>
        ) : null}
        {ticketError ? <p className="mb-2 text-sm text-red-300">{ticketError}</p> : null}
        {error ? <p className="text-sm text-red-300">{(error as Error).message}</p> : null}
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <DataTable data={tickets} columns={columns} emptyText="No tickets for selected status." />
        )}
      </SectionCard>

      {!companyId ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`, so company-scoped tickets are unavailable.
        </p>
      ) : null}
    </div>
  );
}
