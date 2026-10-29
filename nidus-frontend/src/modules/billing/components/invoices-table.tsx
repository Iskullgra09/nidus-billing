"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/core/i18n/routing";
import { useSearchParams } from "next/navigation";
import {
  Ban,
  Banknote,
  Eye,
  FileDown,
  Mail,
  MoreHorizontal,
  Pencil,
  Plus,
  RefreshCw,
  Send,
  Stamp,
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
import { PromptDialog } from "@/shared/components/layout/prompt-dialog";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { formatMoney } from "../lib/format";
import { Party, PageInfo } from "../types/party";
import {
  Invoice,
  InvoiceEmailDelivery,
  InvoiceFiscal,
  InvoiceListItem,
} from "../types/invoice";
import { InvoiceDetailDialog } from "./invoice-detail-dialog";
import { InvoiceFormDialog } from "./invoice-form-dialog";
import {
  createInvoiceAction,
  createInvoicePaymentAction,
  deleteInvoiceAction,
  downloadInvoicePdfAction,
  emitInvoiceFiscalAction,
  getInvoiceAction,
  getInvoiceEmailsAction,
  getInvoiceFiscalAction,
  issueInvoiceAction,
  sendInvoiceEmailAction,
  updateInvoiceAction,
  verifyInvoiceFiscalAction,
  voidInvoiceAction,
} from "../actions/invoices";

interface InvoicesTableProps {
  invoices: InvoiceListItem[];
  pageInfo: PageInfo;
  searchQuery: string;
  pageSize: number;
  customers: Party[];
}

export function InvoicesTable({
  invoices,
  pageInfo,
  searchQuery,
  pageSize,
  customers,
}: InvoicesTableProps) {
  const t = useTranslations("BillingInvoices");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [detailOpen, setDetailOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<Invoice | null>(null);
  const [emailDeliveries, setEmailDeliveries] = React.useState<InvoiceEmailDelivery[]>(
    [],
  );
  const [fiscal, setFiscal] = React.useState<InvoiceFiscal | null>(null);
  const [confirmTarget, setConfirmTarget] = React.useState<{
    kind: "delete" | "void";
    row: InvoiceListItem;
  } | null>(null);
  const [promptTarget, setPromptTarget] = React.useState<{
    kind: "email" | "payment";
    row: InvoiceListItem;
  } | null>(null);

  const replaceQuery = (mutate: (params: URLSearchParams) => void) => {
    const params = new URLSearchParams(searchParams.toString());
    mutate(params);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  };

  const loadInvoice = async (row: InvoiceListItem) => {
    const full = await getInvoiceAction(row.id);
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

  const openView = async (row: InvoiceListItem) => {
    const full = await loadInvoice(row);
    if (!full) return;
    const [emails, fiscalResult] = await Promise.all([
      getInvoiceEmailsAction(row.id),
      getInvoiceFiscalAction(row.id),
    ]);
    setSelected(full);
    setEmailDeliveries(emails);
    setFiscal(fiscalResult.status === "success" ? fiscalResult.data ?? null : null);
    setDetailOpen(true);
  };

  const refreshFiscal = async (invoiceId: string) => {
    const fiscalResult = await getInvoiceFiscalAction(invoiceId);
    setFiscal(fiscalResult.status === "success" ? fiscalResult.data ?? null : null);
  };

  const handleEmitHacienda = async (row: InvoiceListItem) => {
    const result = await emitInvoiceFiscalAction(row.id);
    if (result.status === "success") {
      toast.success(result.message);
      if (detailOpen && selected?.id === row.id) await refreshFiscal(row.id);
    } else toast.error(result.message);
  };

  const handleVerifyHacienda = async (row: InvoiceListItem) => {
    const result = await verifyInvoiceFiscalAction(row.id);
    if (result.status === "success") {
      toast.success(result.message);
      if (detailOpen && selected?.id === row.id) await refreshFiscal(row.id);
    } else toast.error(result.message);
  };

  const openEdit = async (row: InvoiceListItem) => {
    if (row.status !== "draft") return;
    const full = await loadInvoice(row);
    if (!full) return;
    setSelected(full);
    setDialogOpen(true);
  };

  const openEditFromDetail = (invoice: Invoice) => {
    if (invoice.status !== "draft") return;
    setDetailOpen(false);
    setSelected(invoice);
    setDialogOpen(true);
  };

  const handleIssue = async (row: InvoiceListItem) => {
    const result = await issueInvoiceAction(row.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
  };

  const handlePdf = async (row: InvoiceListItem) => {
    const result = await downloadInvoicePdfAction(row.id);
    if (result.status !== "success" || !result.pdfBase64) {
      toast.error(result.message);
      return;
    }
    const binary = atob(result.pdfBase64);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const runConfirm = async () => {
    if (!confirmTarget) return;
    const { kind, row } = confirmTarget;
    const result =
      kind === "delete"
        ? await deleteInvoiceAction(row.id)
        : await voidInvoiceAction(row.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
    setConfirmTarget(null);
  };

  const runPrompt = async (value: string) => {
    if (!promptTarget) return;
    const { kind, row } = promptTarget;
    if (kind === "email") {
      const result = await sendInvoiceEmailAction(row.id, {
        to_email: value.trim() || null,
      });
      if (result.status === "success") {
        toast.success(result.message);
        if (detailOpen && selected?.id === row.id) {
          setEmailDeliveries(await getInvoiceEmailsAction(row.id));
        }
      } else toast.error(result.message);
    } else {
      const result = await createInvoicePaymentAction(row.id, {
        amount: value.trim(),
        method: "transfer",
      });
      if (result.status === "success") toast.success(result.message);
      else toast.error(result.message);
    }
    setPromptTarget(null);
  };

  const statusVariant = (status: string) => {
    if (status === "issued" || status === "paid") return "default";
    if (status === "void") return "destructive";
    return "secondary";
  };

  const columns: ColumnDef<InvoiceListItem>[] = [
    {
      header: t("tableReference"),
      cell: (row) => row.document_number || row.reference_number || row.id.slice(0, 8),
    },
    {
      header: t("tableCustomer"),
      cell: (row) => row.customer_name || "—",
    },
    {
      header: t("tableStatus"),
      align: "center",
      cell: (row) => (
        <div className="flex flex-wrap justify-center gap-1">
          <Badge variant={statusVariant(row.status)}>{t(`status.${row.status}`)}</Badge>
          {row.is_overdue && <Badge variant="destructive">{t("overdueBadge")}</Badge>}
        </div>
      ),
    },
    {
      header: t("tableCondition"),
      align: "center",
      cell: (row) => t(row.payment_condition),
    },
    {
      header: t("tableTotal"),
      align: "right",
      cell: (row) => formatMoney(row.total, { currency: row.currency, withCurrency: true }),
    },
    {
      header: t("tableBalance"),
      align: "right",
      cell: (row) => formatMoney(row.balance_due, { currency: row.currency, withCurrency: true }),
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
              <DropdownMenuItem onClick={() => void openView(row)}>
                <Eye className="size-4" />
                {t("viewAction")}
              </DropdownMenuItem>
              <CanAccess scope={NidusScope.INVOICE_WRITE}>
                {row.status === "draft" && (
                  <DropdownMenuItem onClick={() => void openEdit(row)}>
                    <Pencil className="size-4" />
                    {t("editAction")}
                  </DropdownMenuItem>
                )}
              </CanAccess>
              <DropdownMenuItem onClick={() => void handlePdf(row)}>
                <FileDown className="size-4" />
                {t("pdfAction")}
              </DropdownMenuItem>
              <CanAccess scope={NidusScope.INVOICE_WRITE}>
                {row.status === "draft" && (
                  <>
                    <DropdownMenuItem onClick={() => void handleIssue(row)}>
                      <Send className="size-4" />
                      {t("issueAction")}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => setConfirmTarget({ kind: "delete", row })}
                    >
                      <Trash2 className="size-4" />
                      {t("deleteAction")}
                    </DropdownMenuItem>
                  </>
                )}
                {(row.status === "issued" ||
                  row.status === "partial" ||
                  row.status === "paid") && (
                  <>
                    <DropdownMenuItem onClick={() => void handleEmitHacienda(row)}>
                      <Stamp className="size-4" />
                      {t("emitHaciendaAction")}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => void handleVerifyHacienda(row)}
                    >
                      <RefreshCw className="size-4" />
                      {t("verifyHaciendaAction")}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setPromptTarget({ kind: "email", row })}
                    >
                      <Mail className="size-4" />
                      {t("emailAction")}
                    </DropdownMenuItem>
                  </>
                )}
                {(row.status === "issued" || row.status === "partial") && (
                  <>
                    <DropdownMenuItem
                      onClick={() => setPromptTarget({ kind: "payment", row })}
                    >
                      <Banknote className="size-4" />
                      {t("paymentAction")}
                    </DropdownMenuItem>
                    {Number(row.amount_paid) === 0 && (
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onClick={() => setConfirmTarget({ kind: "void", row })}
                      >
                        <Ban className="size-4" />
                        {t("voidAction")}
                      </DropdownMenuItem>
                    )}
                  </>
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
        data={invoices}
        searchPlaceholder={t("searchPlaceholder")}
        emptyMessage={t("empty")}
        pageSize={pageSize}
        hasNextPage={pageInfo.has_next_page}
        isFirstPage={!searchParams.get("cursor")}
        initialSearch={searchQuery}
        onRowClick={(row) => void openView(row)}
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

      <InvoiceDetailDialog
        isOpen={detailOpen}
        onClose={setDetailOpen}
        invoice={selected}
        emailDeliveries={emailDeliveries}
        fiscal={fiscal}
        onEditDraft={openEditFromDetail}
        onEmitHacienda={
          selected
            ? () => void handleEmitHacienda(selected)
            : undefined
        }
        onVerifyHacienda={
          selected
            ? () => void handleVerifyHacienda(selected)
            : undefined
        }
        onSendEmail={
          selected &&
          (selected.status === "issued" ||
            selected.status === "partial" ||
            selected.status === "paid")
            ? () =>
                setPromptTarget({
                  kind: "email",
                  row: selected,
                })
            : undefined
        }
      />

      <InvoiceFormDialog
        isOpen={dialogOpen}
        onClose={setDialogOpen}
        invoice={selected}
        customers={customers}
        onCreate={createInvoiceAction}
        onUpdate={updateInvoiceAction}
      />

      <ConfirmDialog
        open={confirmTarget !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmTarget(null);
        }}
        title={
          confirmTarget?.kind === "void"
            ? t("voidDialogTitle")
            : t("deleteDialogTitle")
        }
        description={
          confirmTarget?.kind === "void" ? t("voidConfirm") : t("deleteConfirm")
        }
        confirmLabel={
          confirmTarget?.kind === "void"
            ? t("voidConfirmAction")
            : t("deleteAction")
        }
        variant="destructive"
        onConfirm={runConfirm}
      />

      <PromptDialog
        open={promptTarget !== null}
        onOpenChange={(open) => {
          if (!open) setPromptTarget(null);
        }}
        title={
          promptTarget?.kind === "payment"
            ? t("paymentDialogTitle")
            : t("emailDialogTitle")
        }
        description={
          promptTarget?.kind === "payment"
            ? t("paymentDialogDescription", {
                balance: promptTarget.row.balance_due,
              })
            : t("emailDialogDescription")
        }
        label={
          promptTarget?.kind === "payment" ? t("paymentLabel") : t("emailLabel")
        }
        defaultValue={
          promptTarget?.kind === "payment" ? promptTarget.row.balance_due : ""
        }
        inputType={promptTarget?.kind === "payment" ? "text" : "email"}
        allowEmpty={promptTarget?.kind === "email"}
        confirmLabel={
          promptTarget?.kind === "payment"
            ? t("paymentConfirm")
            : t("emailSend")
        }
        onConfirm={runPrompt}
      />
    </div>
  );
}
