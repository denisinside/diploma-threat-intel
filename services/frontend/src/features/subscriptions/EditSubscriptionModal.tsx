import { useState, useEffect } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { Subscription } from "@/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  subscription: Subscription | null;
  onSave: (subId: string, payload: { keyword?: string; min_severity?: Subscription["min_severity"] }) => void;
  isPending?: boolean;
};

const SEVERITY_OPTIONS: Subscription["min_severity"][] = ["critical", "high", "medium", "low", "unknown"];

export function EditSubscriptionModal({
  open,
  onOpenChange,
  subscription,
  onSave,
  isPending = false,
}: Props) {
  const [keyword, setKeyword] = useState("");
  const [minSeverity, setMinSeverity] = useState<Subscription["min_severity"]>("low");

  useEffect(() => {
    if (open && subscription) {
      setKeyword(subscription.keyword);
      setMinSeverity(subscription.min_severity ?? "low");
    }
  }, [open, subscription]);

  function handleSave() {
    if (!subscription) return;
    if (!keyword.trim()) return;
    onSave(subscription._id, {
      keyword: keyword.trim(),
      min_severity: subscription.sub_type === "vulnerability" ? minSeverity : undefined,
    });
    onOpenChange(false);
  }

  if (!subscription) return null;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md glass-panel p-6">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-slate-100">Edit subscription</Dialog.Title>
            <Dialog.Close asChild>
              <button type="button" className="p-1 rounded hover:bg-slate-700/50 text-slate-400" aria-label="Close">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Keyword</label>
              <input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200"
                placeholder="Keyword"
              />
            </div>
            {subscription.sub_type === "vulnerability" && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Min severity</label>
                <select
                  value={minSeverity}
                  onChange={(e) => setMinSeverity(e.target.value as Subscription["min_severity"])}
                  className="w-full bg-slate-800/60 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200"
                >
                  {SEVERITY_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Dialog.Close asChild>
              <button
                type="button"
                className="px-3 py-2 rounded border border-slate-600 text-slate-300 hover:bg-slate-700/50 text-sm"
              >
                Cancel
              </button>
            </Dialog.Close>
            <button
              type="button"
              onClick={handleSave}
              disabled={!keyword.trim() || isPending}
              className="px-3 py-2 rounded border border-tactical-sky/40 text-tactical-sky hover:bg-tactical-sky/15 text-sm disabled:opacity-50"
            >
              {isPending ? "Saving..." : "Save"}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
