"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter, usePathname, Link } from "@/core/i18n/routing";
import { useSearchParams } from "next/navigation";
import {
  FileInput,
  MoreHorizontal,
  Pencil,
  Plus,
  Send,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { ConfirmDialog } from "@/shared/components/layout/confirm-dialog";
import { DataTable, ColumnDef } from "@/shared/components/layout/data-table";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { formatMoney } from "../lib/format";
import { Party, PageInfo } from "../types/party";
import { Quote, QuoteListItem } from "../types/quote";
import { QuoteFormDialog } from "./quote-form-dialog";
import {
  convertQuoteAction,
  createQuoteAction,
  deleteQuoteAction,
  getQuoteAction,
  markQuoteSentAction,
  updateQuoteAction,
} from "../actions/quotes";

interface QuotesTableProps {
  quotes: QuoteListItem[];
  pageInfo: PageInfo;
  searchQuery: string;
  pageSize: number;
  customers: Party[];
}

export function QuotesTable({
  quotes,
  pageInfo,
  searchQuery,
  pageSize,
  customers,
}: QuotesTableProps) {
  const t = useTranslations("BillingQuotes");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<Quote | null>(null);
  const [confirmTarget, setConfirmTarget] = React.useState<QuoteListItem | null>(
    null,
  );

  const replaceQuery = (mutate: (params: URLSearchParams) => void) => {
    const params = new URLSearchParams(searchParams.toString());
    mutate(params);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  };

  React.useEffect(() => {
    if (searchParams.get("create") !== "1") return;
    setSelected(null);
    setDialogOpen(true);
    replaceQuery((params) => {
      params.delete("create");
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- open once when create=1 lands
  }, [searchParams]);

  const loadQuote = async (row: QuoteListItem) => {
    const full = await getQuoteAction(row.id);
    if (!full) {
      toast.error(t("loadError"));
      return null;
    }
    return full;
  };

  const openCreate = () => {
    setSelected(null);
    setDialogOpen(true);
  };

  const openEdit = async (row: QuoteListItem) => {
    if (row.status === "converted") return;
    const full = await loadQuote(row);
    if (!full) return;
    setSelected(full);
    setDialogOpen(true);
  };

  const handleMarkSent = async (row: QuoteListItem) => {
    const result = await markQuoteSentAction(row.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
  };

  const handleConvert = async (row: QuoteListItem) => {
    const result = await convertQuoteAction(row.id);
    if (result.status === "success") {
      toast.success(
        result.invoiceId
          ? t("convertSuccess", { id: result.invoiceId.slice(0, 8) })
          : result.message,
        {
          action: result.invoiceId
            ? {
                label: t("viewInvoice"),
                onClick: () => router.push("/billing/invoices"),
              }
            : undefined,
        },
      );
      router.refresh();
    } else toast.error(result.message);
  };

  const runConfirm = async () => {
    if (!confirmTarget) return;
    const result = await deleteQuoteAction(confirmTarget.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
    setConfirmTarget(null);
  };

  const statusVariant = (status: string) => {
    if (status === "converted" || status === "accepted") return "default";
    if (status === "rejected") return "destructive";
    return "secondary";
  };

  const canConvert = (status: string) =>
    status === "draft" || status === "sent" || status === "accepted";

  const columns: ColumnDef<QuoteListItem>[] = [
    {
      header: t("tableReference"),
      cell: (row) => row.reference_number || row.id.slice(0, 8),
    },
    {
      header: t("tableCustomer"),
      cell: (row) => row.customer_name || "—",
    },
    {
      header: t("tableStatus"),
      align: "center",
      cell: (row) => (
        <Badge variant={statusVariant(row.status)}>
          {t(`status.${row.status}`)}
        </Badge>
      ),
    },
    {
      header: t("tableValidUntil"),
      cell: (row) => row.valid_until || "—",
    },
    {
      header: t("tableTotal"),
      align: "right",
      cell: (row) =>
        formatMoney(row.total, { currency: row.currency, withCurrency: true }),
    },
    {
      header: "",
      className: "w-12",
      align: "right",
      cell: (row) => (
        <div
          onClick={(event) => event.stopPropagation()}
          onKeyDown={(event) => event.stopPropagation()}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <CanAccess scope={NidusScope.INVOICE_WRITE}>
                {row.status !== "converted" && (
                  <DropdownMenuItem onClick={() => void openEdit(row)}>
                    <Pencil className="size-4" />
                    {t("editAction")}
                  </DropdownMenuItem>
                )}
                {row.status === "draft" && (
                  <>
                    <DropdownMenuItem onClick={() => void handleMarkSent(row)}>
                      <Send className="size-4" />
                      {t("markSentAction")}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => setConfirmTarget(row)}
                    >
                      <Trash2 className="size-4" />
                      {t("deleteAction")}
                    </DropdownMenuItem>
                  </>
                )}
                {canConvert(row.status) && (
                  <DropdownMenuItem onClick={() => void handleConvert(row)}>
                    <FileInput className="size-4" />
                    {t("convertAction")}
                  </DropdownMenuItem>
                )}
                {row.status === "converted" && row.converted_invoice_id && (
                  <DropdownMenuItem asChild>
                    <Link href="/billing/invoices">{t("viewInvoice")}</Link>
                  </DropdownMenuItem>
                )}
              </CanAccess>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <DataTable
        mode="cursor"
        columns={columns}
        data={quotes}
        searchPlaceholder={t("searchPlaceholder")}
        emptyMessage={t("empty")}
        pageSize={pageSize}
        hasNextPage={pageInfo.has_next_page}
        isFirstPage={!searchParams.get("cursor")}
        initialSearch={searchQuery}
        onRowClick={(row) => {
          if (row.status !== "converted") void openEdit(row);
        }}
        toolbarAction={
          <CanAccess scope={NidusScope.INVOICE_WRITE}>
            <Button type="button" size="sm" onClick={openCreate}>
              <Plus className="size-4" />
              {t("createButton")}
            </Button>
          </CanAccess>
        }
        onSearchChange={(query) => {
          const next = query.trim();
          if (next === searchQuery) return;
          replaceQuery((params) => {
            if (next) params.set("q", next);
            else params.delete("q");
            params.delete("cursor");
          });
        }}
        onFirstPage={() => {
          replaceQuery((params) => {
            params.delete("cursor");
          });
        }}
        onNextPage={() => {
          if (!pageInfo.end_cursor) return;
          replaceQuery((params) => {
            params.set("cursor", pageInfo.end_cursor!);
          });
        }}
      />

      <QuoteFormDialog
        isOpen={dialogOpen}
        onClose={setDialogOpen}
        quote={selected}
        customers={customers}
        onCreate={createQuoteAction}
        onUpdate={updateQuoteAction}
      />

      <ConfirmDialog
        open={confirmTarget !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmTarget(null);
        }}
        title={t("deleteDialogTitle")}
        description={t("deleteConfirm")}
        confirmLabel={t("deleteAction")}
        variant="destructive"
        onConfirm={runConfirm}
      />
    </div>
  );
}
