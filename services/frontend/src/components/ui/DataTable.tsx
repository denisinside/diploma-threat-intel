import {
  type ColumnDef,
  type RowSelectionState,
  type SortingState,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Pagination } from "./Pagination";

type Props<TData> = {
  data: TData[];
  columns: Array<ColumnDef<TData>>;
  emptyText?: string;
  enableRowSelection?: boolean;
  getRowId?: (row: TData) => string;
  rowSelection?: RowSelectionState;
  onRowSelectionChange?: (selected: TData[]) => void;
  pageSize?: number;
};

export function DataTable<TData>({
  data,
  columns,
  emptyText = "No data found.",
  enableRowSelection = false,
  getRowId,
  rowSelection: controlledSelection,
  onRowSelectionChange,
  pageSize = 0,
}: Props<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [page, setPage] = useState(1);
  const [internalSelection, setInternalSelection] = useState<RowSelectionState>({});
  const selection = controlledSelection ?? internalSelection;
  const usePagination = pageSize > 0;

  const colsWithCheckbox: Array<ColumnDef<TData>> =
    enableRowSelection && getRowId
      ? [
          {
            id: "select",
            enableSorting: false,
            header: ({ table: t }) => (
              <input
                type="checkbox"
                checked={t.getIsAllRowsSelected()}
                ref={(el) => el && (el.indeterminate = t.getIsSomeRowsSelected())}
                onChange={t.getToggleAllRowsSelectedHandler()}
                className="rounded border-slate-600"
              />
            ),
            cell: ({ row }) => (
              <input
                type="checkbox"
                checked={row.getIsSelected()}
                disabled={!row.getCanSelect()}
                onChange={row.getToggleSelectedHandler()}
                className="rounded border-slate-600"
              />
            ),
          },
          ...columns,
        ]
      : columns;

  const table = useReactTable({
    data,
    columns: colsWithCheckbox,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: usePagination ? getPaginationRowModel() : undefined,
    onSortingChange: setSorting,
    onRowSelectionChange: (updater) => {
      const next = typeof updater === "function" ? updater(selection) : {};
      if (!controlledSelection) setInternalSelection(next);
      if (onRowSelectionChange && getRowId) {
        const ids = Object.keys(next).filter((id) => next[id]);
        const selected = data.filter((row) => ids.includes(getRowId(row)));
        onRowSelectionChange(selected);
      }
    },
    state: {
      sorting,
      rowSelection: enableRowSelection ? selection : undefined,
      pagination: usePagination ? { pageIndex: page - 1, pageSize } : undefined,
    },
    onPaginationChange: usePagination
      ? (updater) => {
          const next = typeof updater === "function" ? updater({ pageIndex: page - 1, pageSize }) : {};
          if (next.pageIndex != null) setPage(next.pageIndex + 1);
        }
      : undefined,
    enableRowSelection,
    getRowId: getRowId ?? undefined,
  });

  return (
    <div className="overflow-hidden rounded border border-slate-700/50">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/70">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort();
                  const sortDir = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      className="px-3 py-2 text-left text-xs uppercase text-slate-400 border-b border-slate-700/40"
                    >
                      {header.isPlaceholder ? null : canSort ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className="flex items-center gap-1 hover:text-slate-300 w-full text-left"
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sortDir === "asc" && <ChevronUp className="w-3.5 h-3.5" />}
                          {sortDir === "desc" && <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-800/70 hover:bg-slate-800/40">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2 text-slate-200 align-top">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-3 py-6 text-center text-slate-400" colSpan={colsWithCheckbox.length}>
                  {emptyText}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {usePagination && data.length > pageSize ? (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={data.length}
          onPageChange={setPage}
        />
      ) : null}
    </div>
  );
}
