import type { Severity } from "@/types";
import { cn } from "@/lib/utils";

type Props = {
  severity?: Severity;
};

const styles: Record<Severity, string> = {
  critical: "text-red-300 bg-red-950/70 border-red-500/40",
  high: "text-amber-300 bg-amber-950/70 border-amber-500/40",
  medium: "text-yellow-300 bg-yellow-950/70 border-yellow-500/40",
  low: "text-emerald-300 bg-emerald-950/70 border-emerald-500/40",
  unknown: "text-slate-300 bg-slate-800/80 border-slate-600/40",
};

export function SeverityBadge({ severity = "unknown" }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 text-xs uppercase border",
        styles[severity]
      )}
    >
      {severity}
    </span>
  );
}
