import { useState } from "react";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  useCompanyRequests,
  useApproveRequest,
  useRejectRequest,
} from "@/features/admin/hooks";

export function AdminCompanyRequestsPage() {
  const { data: requests = [], isLoading } = useCompanyRequests();
  const approveRequest = useApproveRequest();
  const rejectRequest = useRejectRequest();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Company registration requests</h1>
      <SectionCard title="Pending requests">
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : requests.length === 0 ? (
          <p className="text-slate-400">No pending requests</p>
        ) : (
          <div className="space-y-3">
            {requests.map((req) => (
              <div
                key={req._id}
                className="flex flex-wrap items-center justify-between gap-3 p-3 rounded border border-slate-700/50 bg-slate-800/30"
              >
                <div>
                  <p className="font-medium text-slate-200">{req.name}</p>
                  <p className="text-sm text-slate-400">
                    {req.domain} · {req.admin_email} · {req.admin_full_name}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => approveRequest.mutate(req._id)}
                    disabled={approveRequest.isPending || rejectRequest.isPending}
                    className="px-3 py-1.5 rounded border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 text-sm disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => rejectRequest.mutate(req._id)}
                    disabled={approveRequest.isPending || rejectRequest.isPending}
                    className="px-3 py-1.5 rounded border border-red-500/40 text-red-300 hover:bg-red-500/15 text-sm disabled:opacity-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
