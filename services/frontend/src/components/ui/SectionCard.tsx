import type { PropsWithChildren, ReactNode } from "react";

type Props = PropsWithChildren<{
  title: ReactNode;
  rightSlot?: ReactNode;
}>;

export function SectionCard({ title, rightSlot, children }: Props) {
  return (
    <section className="glass-panel p-4 md:p-5">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h3 className="text-sm uppercase tracking-wide text-slate-300 font-semibold">
          {title}
        </h3>
        {rightSlot}
      </div>
      {children}
    </section>
  );
}
