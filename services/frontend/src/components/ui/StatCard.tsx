import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Props = {
  label: string;
  value: string | number;
  accent?: "amber" | "sky";
  hint?: ReactNode;
};

export function StatCard({ label, value, accent = "sky", hint }: Props) {
  return (
    <div
      className={cn(
        "glass-panel p-4 border",
        accent === "amber" ? "border-tactical-amber/35" : "border-tactical-sky/35"
      )}
    >
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-3xl leading-none font-semibold text-slate-100">{value}</p>
      {hint ? <p className="mt-2 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}
