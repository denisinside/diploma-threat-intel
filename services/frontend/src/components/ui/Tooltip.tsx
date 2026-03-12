import type { PropsWithChildren } from "react";
import { HelpCircle } from "lucide-react";

type Props = PropsWithChildren<{
  content: string;
}>;

/** Inline (?) icon with tooltip on hover */
export function Tooltip({ content, children }: Props) {
  return (
    <span className="inline-flex items-center gap-1">
      {children}
      <span
        className="cursor-help text-slate-500 hover:text-slate-400 transition-colors"
        title={content}
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </span>
    </span>
  );
}
