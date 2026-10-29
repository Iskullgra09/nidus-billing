"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useRouter, usePathname } from "@/core/i18n/routing";
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
import { CatalogItem } from "../types/item";
import { PageInfo } from "../types/party";
import {
  createItemAction,
  deleteItemAction,
  updateItemAction,
} from "../actions/items";
import { ItemFormDialog } from "./item-form-dialog";

interface ItemsTableProps {
  items: CatalogItem[];
  pageInfo: PageInfo;
  searchQuery: string;
  pageSize: number;
}

export function ItemsTable({
  items,
  pageInfo,
  searchQuery,
  pageSize,
}: ItemsTableProps) {
  const t = useTranslations("BillingItems");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [selected, setSelected] = React.useState<CatalogItem | null>(null);

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

  const openEdit = (item: CatalogItem) => {
    setSelected(item);
    setDialogOpen(true);
  };

  const handleDelete = async (item: CatalogItem) => {
    if (!confirm(t("deleteConfirm", { name: item.name }))) return;
    const result = await deleteItemAction(item.id);
    if (result.status === "success") toast.success(result.message);
    else toast.error(result.message);
  };

  const columns: ColumnDef<CatalogItem>[] = [
    {
      header: t("tableName"),
      cell: (item) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{item.name}</span>
            {item.is_service && (
              <Badge variant="outline" className="text-[10px] uppercase">
                {t("serviceBadge")}
              </Badge>
            )}
            {!item.is_active && (
              <Badge variant="outline" className="text-[10px] uppercase">
                {t("inactiveBadge")}
              </Badge>
            )}
          </div>
          {item.sku && (
            <p className="text-xs text-muted-foreground">{item.sku}</p>
          )}
        </div>
      ),
    },
    {
      header: t("tableUnit"),
      cell: (item) => item.unit,
    },
    {
      header: t("tablePrice"),
      cell: (item) => item.unit_price,
    },
    {
      header: t("tableTax"),
      cell: (item) => (item.tax_rate != null ? `${item.tax_rate}%` : "—"),
    },
    {
      header: "",
      className: "w-12",
      cell: (item) => (
        <CanAccess scope={NidusScope.ITEM_WRITE}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="size-8">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => openEdit(item)}>
                <Pencil className="size-4" />
                {t("editAction")}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => void handleDelete(item)}
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
        <CanAccess scope={NidusScope.ITEM_WRITE}>
          <Button type="button" onClick={openCreate}>
            <Plus className="size-4" />
            {t("createButton")}
          </Button>
        </CanAccess>
      </div>

      <DataTable
        mode="cursor"
        columns={columns}
        data={items}
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

      <ItemFormDialog
        isOpen={dialogOpen}
        onClose={setDialogOpen}
        item={selected}
        onCreate={createItemAction}
        onUpdate={updateItemAction}
      />
    </div>
  );
}
