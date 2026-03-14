import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import { DataTable } from "@/components/ui/DataTable";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatCard } from "@/components/ui/StatCard";
import { HelpCircle } from "lucide-react";
import { useAssets, useCreateAsset, useDeleteAsset, useImportAssets, useUpdateAsset } from "@/features/assets/hooks";
import { useAuth } from "@/hooks/useAuth";
import { useCanMutate } from "@/hooks/useRoleGuard";
import { toast } from "@/lib/toast";
import type { Asset } from "@/types";

const SUPPORTED_IMPORT_FILES =
  "package-lock.json, package.json, yarn.lock, pnpm-lock.yaml, requirements.txt, pyproject.toml, poetry.lock, Pipfile, Pipfile.lock, Gemfile.lock, composer.json, composer.lock, pom.xml, build.gradle, pubspec.yaml, Package.swift, Package.resolved, Cargo.toml, Cargo.lock, go.sum, SBOM (CycloneDX, SPDX)";

export function AssetsPage() {
  const { session } = useAuth();
  const companyId = session?.user?.company_id;
  const canMutate = useCanMutate();
  const { data: assets = [], isLoading, error } = useAssets(companyId);
  const createAsset = useCreateAsset();
  const updateAsset = useUpdateAsset();
  const deleteAsset = useDeleteAsset();
  const importAssets = useImportAssets();
  const [name, setName] = useState("");
  const [type, setType] = useState<Asset["type"]>("domain");
  const [version, setVersion] = useState("");
  const [sourceFile, setSourceFile] = useState("");
  const [formError, setFormError] = useState("");
  const [selectedAssets, setSelectedAssets] = useState<Asset[]>([]);

  const columns = useMemo<Array<ColumnDef<Asset>>>(
    () => [
      { header: "Name", accessorKey: "name" },
      { header: "Type", accessorKey: "type" },
      { header: "Version", accessorKey: "version" },
      {
        header: "Status",
        accessorFn: (row) => (row.is_active ? "active" : "inactive"),
        cell: ({ row }) =>
          row.original.is_active ? (
            <span className="text-emerald-300">active</span>
          ) : (
            <span className="text-slate-400">inactive</span>
          ),
      },
      { header: "Source File", accessorKey: "source_file" },
      ...(canMutate
        ? [
            {
              header: "Actions",
              enableSorting: false,
              cell: ({ row }: { row: { original: Asset } }) => (
                <span className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const action = row.original.is_active ? "deactivate" : "activate";
                      if (window.confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} this asset?`)) {
                        updateAsset.mutate({ assetId: row.original._id, payload: { is_active: !row.original.is_active } });
                      }
                    }}
                    className="text-amber-300 hover:text-amber-200 text-xs"
                  >
                    {row.original.is_active ? "deactivate" : "activate"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm("Delete this asset?")) {
                        deleteAsset.mutate(row.original._id);
                      }
                    }}
                    className="text-red-300 hover:text-red-200 text-xs"
                  >
                    delete
                  </button>
                </span>
              ),
            } as ColumnDef<Asset>,
          ]
        : []),
    ],
    [updateAsset, deleteAsset, canMutate]
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
        {companyId && canMutate ? (
          <>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <label className="text-sm text-slate-400">
              Import from file:
            </label>
            <input
              type="file"
              accept=".json,.txt,.toml,.lock,.sum,.yaml,.yml,.xml,.gradle,.swift"
              className="hidden"
              id="asset-import-file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file || !companyId) return;
                importAssets.mutate(
                  { companyId, file },
                  {
                    onSuccess: (res) => {
                      const msg = `Imported ${res.created} assets, ${res.skipped_duplicate} skipped (duplicates)`;
                      toast.success(msg);
                      if (res.errors?.length) {
                        toast.error(res.errors.slice(0, 3).join("; "));
                      }
                    },
                    onError: (err) => toast.error(err instanceof Error ? err.message : "Import failed"),
                  }
                );
                e.target.value = "";
              }}
            />
            <label
              htmlFor="asset-import-file"
              className="cursor-pointer rounded border border-slate-600 bg-slate-800/60 px-3 py-2 text-sm text-slate-200 hover:bg-slate-700/60"
            >
              {importAssets.isPending ? "Importing..." : "Choose file"}
            </label>
            <span
              className="cursor-help text-slate-500 hover:text-slate-400 transition-colors"
              title={SUPPORTED_IMPORT_FILES}
            >
              <HelpCircle className="w-3.5 h-3.5 inline" />
            </span>
          </div>
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
                  version: type === "library" ? version.trim() || undefined : undefined,
                  source_file: type === "library" ? sourceFile.trim() || undefined : undefined,
                },
                {
                  onSuccess: () => {
                    setName("");
                    setVersion("");
                    setSourceFile("");
                    toast.success("Asset created");
                  },
                  onError: (mutationError) => {
                    const msg = mutationError instanceof Error ? mutationError.message : "Failed to create asset.";
                    setFormError(msg);
                    toast.error(msg);
                  },
                }
              );
            }}
          >
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
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Asset name"
              className="bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm"
            />
            {type === "library" ? (
              <>
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
              </>
            ) : null}
            <button
              type="submit"
              className="rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm px-3 py-2"
            >
              {createAsset.isPending ? "Creating..." : "Add asset"}
            </button>
          </form>
          </>
        ) : null}
        {formError ? <p className="mb-2 text-sm text-red-300">{formError}</p> : null}
        {error ? <p className="text-sm text-red-300">{(error as Error).message}</p> : null}
        {canMutate && selectedAssets.length > 0 ? (
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-400">{selectedAssets.length} selected</span>
            <button
              type="button"
              onClick={() => {
                selectedAssets.filter((a) => a.is_active).forEach((a) =>
                  updateAsset.mutate({ assetId: a._id, payload: { is_active: false } })
                );
                setSelectedAssets([]);
              }}
              className="text-xs px-2 py-1 rounded border border-amber-500/50 text-amber-300 hover:bg-amber-500/15"
            >
              Deactivate
            </button>
            <button
              type="button"
              onClick={() => {
                selectedAssets.filter((a) => !a.is_active).forEach((a) =>
                  updateAsset.mutate({ assetId: a._id, payload: { is_active: true } })
                );
                setSelectedAssets([]);
              }}
              className="text-xs px-2 py-1 rounded border border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/15"
            >
              Activate
            </button>
            <button
              type="button"
              onClick={() => {
                if (window.confirm(`Delete ${selectedAssets.length} asset(s)?`)) {
                  selectedAssets.forEach((a) => deleteAsset.mutate(a._id));
                  setSelectedAssets([]);
                }
              }}
              className="text-xs px-2 py-1 rounded border border-red-500/50 text-red-300 hover:bg-red-500/15"
            >
              Delete selected
            </button>
            <button
              type="button"
              onClick={() => setSelectedAssets([])}
              className="text-xs text-slate-400 hover:text-slate-300"
            >
              Clear
            </button>
          </div>
        ) : null}
        {isLoading ? (
          <p className="text-slate-400">Loading...</p>
        ) : (
          <DataTable
            data={assets}
            columns={columns}
            emptyText="No assets for this company."
            enableRowSelection={canMutate}
            getRowId={(row) => row._id}
            rowSelection={Object.fromEntries(selectedAssets.map((a) => [a._id, true]))}
            onRowSelectionChange={setSelectedAssets}
            pageSize={100}
          />
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
