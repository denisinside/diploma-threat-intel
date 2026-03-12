import { useState, useEffect, useRef } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { vulnsApi, type VulnSearchParams } from "./api";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  filters: Omit<VulnSearchParams, "skip" | "limit" | "sort_by" | "sort_order">;
  onApply: (filters: Omit<VulnSearchParams, "skip" | "limit" | "sort_by" | "sort_order">) => void;
  ecosystems: string[];
};

const SEVERITY_OPTIONS = ["LOW", "MODERATE", "HIGH", "CRITICAL"];

export function VulnAdvancedSearchModal({
  open,
  onOpenChange,
  filters,
  onApply,
  ecosystems,
}: Props) {
  const [q, setQ] = useState(filters.q ?? "");
  const [ecosystem, setEcosystem] = useState(filters.ecosystem ?? "");
  const [packageName, setPackageName] = useState(filters.package ?? "");
  const [cvssMin, setCvssMin] = useState(filters.cvss_min != null ? String(filters.cvss_min) : "");
  const [cvssMax, setCvssMax] = useState(filters.cvss_max != null ? String(filters.cvss_max) : "");
  const [publishedFrom, setPublishedFrom] = useState(filters.published_from ?? "");
  const [publishedTo, setPublishedTo] = useState(filters.published_to ?? "");
  const [cweId, setCweId] = useState(filters.cwe_id ?? "");
  const [severity, setSeverity] = useState(filters.severity ?? "");
  const [packageSuggestions, setPackageSuggestions] = useState<Array<{ name: string; count: number }>>([]);
  const [showPackageSuggestions, setShowPackageSuggestions] = useState(false);
  const packageDebounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (open) {
      setQ(filters.q ?? "");
      setEcosystem(filters.ecosystem ?? "");
      setPackageName(filters.package ?? "");
      setCvssMin(filters.cvss_min != null ? String(filters.cvss_min) : "");
      setCvssMax(filters.cvss_max != null ? String(filters.cvss_max) : "");
      setPublishedFrom(filters.published_from ?? "");
      setPublishedTo(filters.published_to ?? "");
      setCweId(filters.cwe_id ?? "");
      setSeverity(filters.severity ?? "");
    }
  }, [open, filters]);

  // Debounced package autocomplete (300ms idle)
  useEffect(() => {
    if (!packageName.trim() || packageName.length < 2) {
      setPackageSuggestions([]);
      setShowPackageSuggestions(false);
      return;
    }
    if (packageDebounceRef.current) clearTimeout(packageDebounceRef.current);
    packageDebounceRef.current = setTimeout(() => {
      vulnsApi.searchPackages(packageName.trim(), 20).then(setPackageSuggestions).catch(() => setPackageSuggestions([]));
      setShowPackageSuggestions(true);
    }, 300);
    return () => {
      if (packageDebounceRef.current) clearTimeout(packageDebounceRef.current);
    };
  }, [packageName]);

  function handleApply() {
    onApply({
      q: q.trim() || undefined,
      ecosystem: ecosystem || undefined,
      package: packageName || undefined,
      cvss_min: cvssMin ? parseFloat(cvssMin) : undefined,
      cvss_max: cvssMax ? parseFloat(cvssMax) : undefined,
      published_from: publishedFrom || undefined,
      published_to: publishedTo || undefined,
      cwe_id: cweId || undefined,
      severity: severity || undefined,
    });
    onOpenChange(false);
  }

  function handleReset() {
    setQ("");
    setEcosystem("");
    setPackageName("");
    setCvssMin("");
    setCvssMax("");
    setPublishedFrom("");
    setPublishedTo("");
    setCweId("");
    setSeverity("");
  }

  const inputClass =
    "w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200";

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-y-auto glass-panel p-6">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-semibold text-slate-100">
              Advanced Search
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                className="p-1 rounded hover:bg-slate-700/50 text-slate-400"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Search (CVE, summary, details)</label>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className={inputClass}
                placeholder="e.g. CVE-2024 or buffer overflow"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Ecosystem</label>
              <select
                value={ecosystem}
                onChange={(e) => setEcosystem(e.target.value)}
                className={inputClass}
              >
                <option value="">All</option>
                {ecosystems.map((e) => (
                  <option key={e} value={e}>
                    {e}
                  </option>
                ))}
              </select>
            </div>
            <div className="relative">
              <label className="block text-xs text-slate-400 mb-1">Package</label>
              <input
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                onFocus={() => packageSuggestions.length > 0 && setShowPackageSuggestions(true)}
                onBlur={() => setTimeout(() => setShowPackageSuggestions(false), 150)}
                className={inputClass}
                placeholder="e.g. linux_kernel (type to see suggestions)"
              />
              {showPackageSuggestions && packageSuggestions.length > 0 ? (
                <ul className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto bg-slate-800 border border-slate-600 rounded shadow-lg">
                  {packageSuggestions.map((p) => (
                    <li
                      key={p.name}
                      className="px-3 py-2 text-sm text-slate-200 hover:bg-slate-700 cursor-pointer flex justify-between"
                      onMouseDown={() => {
                        setPackageName(p.name);
                        setShowPackageSuggestions(false);
                      }}
                    >
                      <span>{p.name}</span>
                      <span className="text-slate-500 text-xs">{p.count} vulns</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">CWE ID</label>
              <input
                value={cweId}
                onChange={(e) => setCweId(e.target.value)}
                className={inputClass}
                placeholder="e.g. 89 (exact match)"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">CVSS Min</label>
              <input
                type="number"
                min={0}
                max={10}
                step={0.1}
                value={cvssMin}
                onChange={(e) => setCvssMin(e.target.value)}
                className={inputClass}
                placeholder="0"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">CVSS Max</label>
              <input
                type="number"
                min={0}
                max={10}
                step={0.1}
                value={cvssMax}
                onChange={(e) => setCvssMax(e.target.value)}
                className={inputClass}
                placeholder="10"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Published From</label>
              <input
                type="date"
                value={publishedFrom}
                onChange={(e) => setPublishedFrom(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Published To</label>
              <input
                type="date"
                value={publishedTo}
                onChange={(e) => setPublishedTo(e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className={inputClass}
              >
                <option value="">All</option>
                {SEVERITY_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={handleApply}
              className="px-4 py-2 rounded bg-tactical-sky/30 border border-tactical-sky/50 text-tactical-sky hover:bg-tactical-sky/40"
            >
              Apply
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 rounded border border-slate-600 text-slate-400 hover:bg-slate-700/50"
            >
              Reset
            </button>
            <Dialog.Close asChild>
              <button
                type="button"
                className="px-4 py-2 rounded border border-slate-600 text-slate-400 hover:bg-slate-700/50"
              >
                Cancel
              </button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
