type Props = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({ page, pageSize, total, onPageChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  if (total <= pageSize) return null;

  return (
    <div className="flex items-center justify-between gap-4 px-3 py-2 border-t border-slate-700/50 bg-slate-900/30 text-sm text-slate-400">
      <span>
        Showing {start}–{end} of {total}
      </span>
      <div className="flex gap-1">
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={page <= 1}
          className="px-2 py-1 rounded border border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700/50"
        >
          First
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-2 py-1 rounded border border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700/50"
        >
          Prev
        </button>
        <span className="px-2 py-1">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-2 py-1 rounded border border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700/50"
        >
          Next
        </button>
        <button
          type="button"
          onClick={() => onPageChange(totalPages)}
          disabled={page >= totalPages}
          className="px-2 py-1 rounded border border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-700/50"
        >
          Last
        </button>
      </div>
    </div>
  );
}
