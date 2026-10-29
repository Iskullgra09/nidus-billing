"use client";

import * as React from "react";
import { Search, ChevronLeft, ChevronRight, Inbox } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { useDebounce } from "@/core/hooks/use-debounce";

export interface ColumnDef<TData> {
  header: string | React.ReactNode;
  accessorKey?: keyof TData;
  cell?: (item: TData) => React.ReactNode;
  className?: string;
  /** Default left. Use right for money; center for short codes/units. */
  align?: "left" | "center" | "right";
}

interface BaseDataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  searchPlaceholder?: string;
  pageSize?: number;
  emptyMessage?: string;
  paginationText?: (start: number, end: number, total: number) => string;
  onRowClick?: (item: TData) => void;
  /** Primary action (e.g. Add) — rendered inside the panel toolbar with search. */
  toolbarAction?: React.ReactNode;
}

interface ClientDataTableProps<TData> extends BaseDataTableProps<TData> {
  mode?: "client";
  searchKey?: keyof TData;
}

interface ServerDataTableProps<TData> extends BaseDataTableProps<TData> {
  mode: "server";
  pageCount: number;
  rowCount: number;
  pageIndex: number;
  onPageChange: (page: number) => void;
  onSearchChange?: (query: string) => void;
}

interface CursorDataTableProps<TData> extends BaseDataTableProps<TData> {
  mode: "cursor";
  hasNextPage: boolean;
  isFirstPage: boolean;
  onNextPage: () => void;
  onFirstPage: () => void;
  onSearchChange?: (query: string) => void;
  initialSearch?: string;
  rowCountLabel?: string;
}

type DataTableProps<TData> =
  | ClientDataTableProps<TData>
  | ServerDataTableProps<TData>
  | CursorDataTableProps<TData>;

export function DataTable<TData>(props: DataTableProps<TData>) {
  const {
    data,
    columns,
    searchPlaceholder = "Search...",
    pageSize = 5,
    emptyMessage = "No results found.",
    paginationText,
    mode = "client",
    onRowClick,
    toolbarAction,
  } = props;

  const isServer = mode === "server";
  const isCursor = mode === "cursor";

  const initialSearch =
    isCursor && "initialSearch" in props ? (props.initialSearch ?? "") : "";
  const [localSearchQuery, setLocalSearchQuery] = React.useState(initialSearch);
  const debouncedSearchQuery = useDebounce(localSearchQuery, 300);
  const [clientCurrentPage, setClientCurrentPage] = React.useState(1);

  React.useEffect(() => {
    if (isCursor) {
      setLocalSearchQuery(initialSearch);
    }
  }, [initialSearch, isCursor]);

  React.useEffect(() => {
    if (
      (isServer || isCursor) &&
      "onSearchChange" in props &&
      props.onSearchChange
    ) {
      props.onSearchChange(debouncedSearchQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- parent onSearchChange identity is unstable
  }, [debouncedSearchQuery, isServer, isCursor]);

  const processedData = React.useMemo(() => {
    if (isServer || isCursor) return data;

    const clientProps = props as ClientDataTableProps<TData>;
    let filtered = data;

    if (clientProps.searchKey && localSearchQuery) {
      filtered = data.filter((item) => {
        const value = item[clientProps.searchKey!];
        if (typeof value === "string") {
          return value.toLowerCase().includes(localSearchQuery.toLowerCase());
        }
        return false;
      });
    }

    const startIndex = (clientCurrentPage - 1) * pageSize;
    return filtered.slice(startIndex, startIndex + pageSize);
  }, [
    data,
    isServer,
    isCursor,
    props,
    localSearchQuery,
    clientCurrentPage,
    pageSize,
  ]);

  const currentPage = isServer
    ? (props as ServerDataTableProps<TData>).pageIndex
    : clientCurrentPage;

  const totalPages = isServer
    ? (props as ServerDataTableProps<TData>).pageCount
    : Math.max(
        1,
        Math.ceil(
          (props as ClientDataTableProps<TData>).searchKey && localSearchQuery
            ? processedData.length
            : data.length / pageSize,
        ),
      );

  const totalEntries = isServer
    ? (props as ServerDataTableProps<TData>).rowCount
    : data.length;
  const currentStart =
    totalEntries === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const currentEnd = isServer
    ? Math.min(currentPage * pageSize, totalEntries)
    : Math.min(currentStart + processedData.length - 1, totalEntries);

  const handlePageChange = (newPage: number) => {
    if (isServer && "onPageChange" in props) {
      props.onPageChange(newPage);
    } else {
      setClientCurrentPage(newPage);
    }
  };

  React.useEffect(() => {
    if (!isServer && !isCursor) setClientCurrentPage(1);
  }, [localSearchQuery, isServer, isCursor]);

  const showSearch =
    isServer || isCursor
      ? "onSearchChange" in props
      : "searchKey" in props;

  const showToolbar = showSearch || Boolean(toolbarAction);
  const containerHeight = `calc(48px + (${pageSize} * 64px) + 2px)`;
  const cursorProps = isCursor ? (props as CursorDataTableProps<TData>) : null;

  return (
    <div className="w-full space-y-4">
      <div className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-md ring-1 ring-foreground/5 backdrop-blur-sm">
        {showToolbar ? (
          <div className="flex flex-col gap-3 border-b border-border/70 p-3 sm:flex-row sm:items-center sm:justify-end sm:gap-3">
            {showSearch ? (
              <div className="relative w-full sm:w-80">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder={searchPlaceholder}
                  value={localSearchQuery}
                  onChange={(e) => setLocalSearchQuery(e.target.value)}
                  className="bg-background/50 pl-9 transition-all focus-visible:ring-1 focus-visible:ring-primary/50"
                />
              </div>
            ) : null}
            {toolbarAction ? (
              <div className="shrink-0">{toolbarAction}</div>
            ) : null}
          </div>
        ) : null}

        <div
          className="relative flex flex-col overflow-hidden [&>div]:overflow-hidden"
          style={{ height: containerHeight }}
        >
          <Table className="w-full flex-1">
            <TableHeader className="sticky top-0 z-10 border-b border-border/70 bg-muted/55">
              <TableRow className="h-12 hover:bg-transparent">
                {columns.map((col, index) => {
                  const align = col.align ?? "left";
                  const alignClass =
                    align === "right"
                      ? "text-right"
                      : align === "center"
                        ? "text-center"
                        : "text-left";
                  return (
                    <TableHead
                      key={index}
                      className={`font-medium ${alignClass} ${col.className || ""}`}
                    >
                      {col.header}
                    </TableHead>
                  );
                })}
              </TableRow>
            </TableHeader>
            <TableBody className="align-top">
              {processedData.length === 0 ? (
                <TableRow className="border-0 hover:bg-transparent">
                  <TableCell
                    colSpan={columns.length}
                    className="h-full text-center align-middle text-muted-foreground"
                  >
                    <div className="mt-12 flex flex-col items-center justify-center space-y-2">
                      <Inbox className="h-8 w-8 text-muted-foreground/30" />
                      <p>{emptyMessage}</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                processedData.map((item, rowIndex) => (
                  <TableRow
                    key={rowIndex}
                    className={`h-16 border-b-border/40 transition-colors last:border-b hover:bg-muted/40 ${
                      onRowClick ? "cursor-pointer" : ""
                    }`}
                    onClick={onRowClick ? () => onRowClick(item) : undefined}
                  >
                    {columns.map((col, colIndex) => {
                      const align = col.align ?? "left";
                      const alignClass =
                        align === "right"
                          ? "text-right tabular-nums"
                          : align === "center"
                            ? "text-center"
                            : "text-left";
                      return (
                        <TableCell
                          key={colIndex}
                          className={`${alignClass} ${col.className || ""}`}
                        >
                          {col.cell
                            ? col.cell(item)
                            : col.accessorKey
                              ? String(item[col.accessorKey] ?? "")
                              : null}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <div className="flex items-center justify-between px-1">
        <div className="text-sm text-muted-foreground font-medium">
          {isCursor
            ? (cursorProps?.rowCountLabel ??
              `${processedData.length} on this page`)
            : paginationText
              ? paginationText(currentStart, currentEnd, totalEntries)
              : `Showing ${currentStart} to ${currentEnd} of ${totalEntries} entries`}
        </div>
        <div className="flex items-center space-x-2">
          {isCursor && cursorProps ? (
            <>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-lg border-border/60 shadow-sm"
                onClick={cursorProps.onFirstPage}
                disabled={cursorProps.isFirstPage}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-lg border-border/60 shadow-sm"
                onClick={cursorProps.onNextPage}
                disabled={!cursorProps.hasNextPage}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-lg border-border/60 shadow-sm"
                onClick={() => handlePageChange(Math.max(currentPage - 1, 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="text-sm font-medium w-12 text-center text-foreground tabular-nums">
                {currentPage} / {totalPages}
              </div>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-lg border-border/60 shadow-sm"
                onClick={() =>
                  handlePageChange(Math.min(currentPage + 1, totalPages))
                }
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
