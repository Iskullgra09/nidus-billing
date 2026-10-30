"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/core/i18n/routing";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle2,
  Eye,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Upload,
  XCircle,
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
import { DataTable, ColumnDef } from "@/shared/components/layout/data-table";
import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { PromptDialog } from "@/shared/components/layout/prompt-dialog";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { ActionResponse } from "@/core/types/api";
import { formatMoney } from "../lib/format";
import { PageInfo, Party } from "../types/party";
import { InboundDocument } from "../types/inbound";
import {
  acceptInboundDocumentAction,
  createInboundDocumentAction,
  getInboundDocumentAction,
  rejectInboundDocumentAction,
  verifyInboundDocumentAction,
} from "../actions/inbound";

interface InboundDocumentsTableProps {
  documents: InboundDocument[];
  pageInfo: PageInfo;
  searchQuery: string;
  pageSize: number;
  suppliers: Party[];
}

export function InboundDocumentsTable({
  documents,
  pageInfo,
  searchQuery,
  pageSize,
  suppliers,
}: InboundDocumentsTableProps) {
  const t = useTranslations("BillingInbound");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [detailOpen, setDetailOpen] = React.useState(false);
  const [uploadOpen, setUploadOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<InboundDocument | null>(null);
  const [xmlText, setXmlText] = React.useState("");
  const [supplierId, setSupplierId] = React.useState("");
  const [pending, setPending] = React.useState(false);
  const [rejectTarget, setRejectTarget] = React.useState<InboundDocument | null>(null);

  const replaceQuery = (mutate: (params: URLSearchParams) => void) => {
    const params = new URLSearchParams(searchParams.toString());
    mutate(params);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  };

  const openDetail = async (row: InboundDocument) => {
    const full = await getInboundDocumentAction(row.id);
    setSelected(full ?? row);
    setDetailOpen(true);
  };

  const runAction = async (
    action: () => Promise<ActionResponse>,
    okToast?: string,
  ) => {
    setPending(true);
    try {
      const res = await action();
      if (res.status === "success") {
        toast.success(okToast || res.message || undefined);
        router.refresh();
        if (selected) {
          const fresh = await getInboundDocumentAction(selected.id);
          if (fresh) setSelected(fresh);
        }
      } else {
        toast.error(res.message || undefined);
      }
    } finally {
      setPending(false);
    }
  };

  const columns: ColumnDef<InboundDocument>[] = [
    {
      header: t("tableClave"),
      cell: (row) => (
        <span className="font-mono text-xs tabular-nums">{row.clave.slice(0, 20)}…</span>
      ),
    },
    {
      header: t("tableEmitter"),
      cell: (row) => row.emitter_name || row.emitter_identification_number || "—",
    },
    {
      header: t("tableSupplier"),
      cell: (row) => row.supplier_name || "—",
    },
    {
      header: t("tableStatus"),
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          <Badge variant="secondary">{t(`status.${row.status}`)}</Badge>
          {row.mock_mode && <Badge variant="outline">{t("haciendaMock")}</Badge>}
        </div>
      ),
    },
    {
      header: t("tableTotal"),
      align: "right",
      cell: (row) => (
        <span className="tabular-nums">
          {formatMoney(row.total)} {row.currency}
        </span>
      ),
    },
    {
      header: "",
      className: "w-12",
      cell: (row) => {
        const canAnswer = row.status === "pending" || row.status === "error" || row.status === "rejected";
        const canVerify = Boolean(row.mensaje_submitted_at);
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label={t("actions")}>
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openDetail(row)}>
                <Eye className="size-4" />
                {t("viewAction")}
              </DropdownMenuItem>
              <CanAccess scope={NidusScope.INBOUND_WRITE}>
                {canAnswer && (
                  <DropdownMenuItem
                    disabled={pending}
                    onClick={() => runAction(() => acceptInboundDocumentAction(row.id))}
                  >
                    <CheckCircle2 className="size-4" />
                    {t("acceptAction")}
                  </DropdownMenuItem>
                )}
                {canAnswer && (
                  <DropdownMenuItem
                    disabled={pending}
                    onClick={() => setRejectTarget(row)}
                  >
                    <XCircle className="size-4" />
                    {t("rejectAction")}
                  </DropdownMenuItem>
                )}
                {canVerify && (
                  <DropdownMenuItem
                    disabled={pending}
                    onClick={() => runAction(() => verifyInboundDocumentAction(row.id))}
                  >
                    <RefreshCw className="size-4" />
                    {t("verifyAction")}
                  </DropdownMenuItem>
                )}
              </CanAccess>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];

  return (
    <>
      <DataTable
        mode="cursor"
        columns={columns}
        data={documents}
        searchPlaceholder={t("searchPlaceholder")}
        emptyMessage={t("empty")}
        pageSize={pageSize}
        hasNextPage={pageInfo.has_next_page}
        isFirstPage={!searchParams.get("cursor")}
        initialSearch={searchQuery}
        onRowClick={(row) => void openDetail(row)}
        toolbarAction={
          <CanAccess scope={NidusScope.INBOUND_WRITE}>
            <Button type="button" size="sm" onClick={() => setUploadOpen(true)}>
              <Plus className="size-4" />
              {t("uploadButton")}
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

      <ModalWrapper
        isOpen={uploadOpen}
        onClose={setUploadOpen}
        title={t("uploadTitle")}
        description={t("uploadDescription")}
      >
        <div className="space-y-3 p-1">
          <label className="text-sm font-medium">{t("fieldXml")}</label>
          <textarea
            value={xmlText}
            onChange={(e) => setXmlText(e.target.value)}
            rows={10}
            className="border-input bg-background w-full rounded-lg border px-3 py-2 font-mono text-xs"
            placeholder="<FacturaElectronica>...</FacturaElectronica>"
          />
          <label className="text-sm font-medium">{t("fieldSupplier")}</label>
          <select
            className="border-input bg-background h-9 w-full rounded-lg border px-2.5 text-sm"
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
          >
            <option value="">{t("supplierAuto")}</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setUploadOpen(false)}>
              {t("closeAction")}
            </Button>
            <Button
              disabled={pending || xmlText.trim().length < 20}
              onClick={async () => {
                setPending(true);
                try {
                  const res = await createInboundDocumentAction({
                    xml: xmlText,
                    supplier_id: supplierId || null,
                  });
                  if (res.status === "success") {
                    toast.success(res.message);
                    setUploadOpen(false);
                    setXmlText("");
                    setSupplierId("");
                    router.refresh();
                  } else {
                    toast.error(res.message);
                  }
                } finally {
                  setPending(false);
                }
              }}
            >
              <Upload className="size-4" />
              {t("uploadSubmit")}
            </Button>
          </div>
        </div>
      </ModalWrapper>

      <ModalWrapper
        isOpen={detailOpen}
        onClose={setDetailOpen}
        title={t("viewTitle")}
        description={t("viewDescription")}
      >
        {selected && (
          <div className="space-y-3 text-sm">
            <dl className="grid gap-2 sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">{t("fieldClave")}</dt>
                <dd className="font-mono text-xs break-all">{selected.clave}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">{t("tableStatus")}</dt>
                <dd>{t(`status.${selected.status}`)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">{t("tableEmitter")}</dt>
                <dd>{selected.emitter_name || "—"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">{t("tableSupplier")}</dt>
                <dd>{selected.supplier_name || "—"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">{t("tableTotal")}</dt>
                <dd className="tabular-nums">
                  {formatMoney(selected.total)} {selected.currency}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">{t("fieldMessage")}</dt>
                <dd className="whitespace-pre-wrap">{selected.mh_message || "—"}</dd>
              </div>
            </dl>
            {selected.mock_mode && (
              <Badge variant="outline">{t("haciendaMock")}</Badge>
            )}
          </div>
        )}
      </ModalWrapper>

      <PromptDialog
        open={Boolean(rejectTarget)}
        onOpenChange={(open) => {
          if (!open) setRejectTarget(null);
        }}
        title={t("rejectTitle")}
        description={t("rejectDescription")}
        label={t("rejectReason")}
        confirmLabel={t("rejectAction")}
        onConfirm={async (reason) => {
          if (!rejectTarget) return;
          await runAction(() => rejectInboundDocumentAction(rejectTarget.id, reason));
          setRejectTarget(null);
        }}
      />
    </>
  );
}
