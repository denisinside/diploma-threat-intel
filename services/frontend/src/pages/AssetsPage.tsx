import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { useAssets, useCreateAsset, useDeleteAsset } from "@/features/assets/hooks";
import { useAuth } from "@/hooks/useAuth";
import type { Asset } from "@/types";

export function AssetsPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const { data: assets = [], isLoading, error } = useAssets(companyId);
  const createAsset = useCreateAsset();
  const deleteAsset = useDeleteAsset();
  const [name, setName] = useState("");
  const [type, setType] = useState<Asset["type"]>("domain");
  const [version, setVersion] = useState("");
  const [sourceFile, setSourceFile] = useState("");
  const [formError, setFormError] = useState("");

  const columns = useMemo<Array<ColumnDef<Asset>>>(
    () => [
      { header: "Name", accessorKey: "name" },
      { header: "Type", accessorKey: "type" },
      { header: "Version", accessorKey: "version" },
      {
        header: "Status",
        cell: ({ row }) =>
          row.original.is_active ? (
            <span className="text-emerald-300">active</span>
          ) : (
            <span className="text-slate-400">inactive</span>
          ),
      },
      { header: "Source File", accessorKey: "source_file" },
      {
        header: "Actions",
        cell: ({ row }) => (
          <button
            type="button"
            onClick={() => deleteAsset.mutate(row.original._id)}
            className="text-red-300 hover:text-red-200 text-xs"
          >
            delete
          </button>
        ),
      },
    ],
    [deleteAsset]
  );

  const activeCount = assets.filter((asset) => asset.is_active).length;
  const libraryCount = assets.filter((asset) => asset.type === "library").length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-100">Assets</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Total Assets" value={assets.length} accent="sky" />
        <StatCard label="Active Assets" value={activeCount} accent="sky" />
        <StatCard label="Libraries" value={libraryCount} accent="amber" />
      </div>

      <SectionCard title="Asset Inventory">
        {companyId ? (
          <form
            className="mb-4 grid grid-cols-1 md:grid-cols-5 gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setFormError("");
              if (!companyId) return;
              if (!name.trim()) {
                setFormError("Asset name is required.");
                return;
              }
              createAsset.mutate(
                {
                  company_id: companyId,
                  name: name.trim(),
                  type,
                  version: version.trim() || undefined,
                  source_file: sourceFile.trim() || undefined,
                },
                {
                  onSuccess: () => {
                    setName("");
                    setVersion("");
                    setSourceFile("");
                  },
                  onError: (mutationError) =>
                    setFormError(mutationError instanceof Error ? mutationError.message : "Failed to create asset."),
                }
              );
            }}
          >
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Asset name"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <select
              value={type}
              onChange={(event) => setType(event.target.value as Asset["type"])}
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            >
              <option value="domain">domain</option>
              <option value="ip_address">ip_address</option>
              <option value="repository">repository</option>
              <option value="library">library</option>
            </select>
            <input
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              placeholder="Version"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <input
              value={sourceFile}
              onChange={(event) => setSourceFile(event.target.value)}
              placeholder="Source file"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createAsset.isPending ? "Creating..." : "Add asset"}
            </button>
          </form>
        ) : null}
        {formError ? <p className="mb-2 text-sm text-red-300">{formError}</p> : null}
        {error ? <p className="text-sm text-red-300">{(error as Error).message}</p> : null}
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <DataTable data={assets} columns={columns} emptyText="No assets for this company." />
        )}
      </SectionCard>

      {!companyId ? (
        <p className="text-sm text-amber-300">
          Your account has no `company_id`, so company-scoped assets are unavailable.
        </p>
      ) : null}
    </div>
  );
}
