"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/core/i18n/routing";
import { useSearchParams } from "next/navigation";
import { MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
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
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { ActionResponse } from "@/core/types/api";
import { Party, PartyPayload, PageInfo } from "../types/party";
import { PartyFormDialog } from "./party-form-dialog";

interface PartiesTableProps {
  parties: Party[];
  pageInfo: PageInfo;
  searchQuery: string;
  pageSize: number;
  namespace: "BillingCustomers" | "BillingSuppliers";
  writeScope: NidusScope;
  onCreate: (payload: PartyPayload) => Promise<ActionResponse>;
  onUpdate: (id: string, payload: Partial<PartyPayload>) => Promise<ActionResponse>;
  onDelete: (id: string) => Promise<ActionResponse>;
}

export function PartiesTable({
  parties,
  pageInfo,
  searchQuery,
  pageSize,
  namespace,
  writeScope,
  onCreate,
  onUpdate,
  onDelete,
}: PartiesTableProps) {
  const t = useTranslations(namespace);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<Party | null>(null);

  const replaceQuery = (mutate: (params: URLSearchParams) => void) => {
    const params = new URLSearchParams(searchParams.toString());
    mutate(params);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  };

  const openCreate = () => {
    setSelected(null);
    setDialogOpen(true);
  };

  const openEdit = (party: Party) => {
    setSelected(party);
    setDialogOpen(true);
  };

  const handleDelete = async (party: Party) => {
    if (!confirm(t("deleteConfirm", { name: party.name }))) return;
    const result = await onDelete(party.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
  };

  const columns: ColumnDef<Party>[] = [
    {
      header: t("tableName"),
      cell: (party) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{party.name}</span>
            {!party.is_active && (
              <Badge variant="outline" className="text-[10px] uppercase">
                {t("inactiveBadge")}
              </Badge>
            )}
          </div>
          {party.email && (
            <p className="text-xs text-muted-foreground">{party.email}</p>
          )}
        </div>
      ),
    },
    {
      header: t("tableTaxId"),
      cell: (party) => party.tax_id || "—",
    },
    {
      header: t("tablePhone"),
      cell: (party) => party.phone || "—",
    },
    {
      header: "",
      className: "w-12",
      cell: (party) => (
        <CanAccess scope={writeScope}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openEdit(party)}>
                <Pencil className="size-4" />
                {t("editAction")}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => void handleDelete(party)}
              >
                <Trash2 className="size-4" />
                {t("deleteAction")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CanAccess>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <CanAccess scope={writeScope}>
          <Button type="button" onClick={openCreate}>
            <Plus className="size-4" />
            {t("createButton")}
          </Button>
        </CanAccess>
      </div>

      <DataTable
        mode="cursor"
        columns={columns}
        data={parties}
        searchPlaceholder={t("searchPlaceholder")}
        emptyMessage={t("empty")}
        pageSize={pageSize}
        hasNextPage={pageInfo.has_next_page}
        isFirstPage={!searchParams.get("cursor")}
        initialSearch={searchQuery}
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

      <PartyFormDialog
        isOpen={dialogOpen}
        onClose={setDialogOpen}
        party={selected}
        namespace={namespace}
        onCreate={onCreate}
        onUpdate={onUpdate}
      />
    </div>
  );
}
