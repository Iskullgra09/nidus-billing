"use client";

import { useTranslations } from "next-intl";

import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { formatMoney, formatPercent } from "../lib/format";
import { CatalogItem } from "../types/item";

interface ItemDetailDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  item: CatalogItem | null;
  onEdit?: (item: CatalogItem) => void;
}

export function ItemDetailDialog({
  isOpen,
  onClose,
  item,
  onEdit,
}: ItemDetailDialogProps) {
  const t = useTranslations("BillingItems");

  if (!item) return null;

  return (
    <ModalWrapper
      isOpen={isOpen}
      onClose={onClose}
      title={item.name}
      description={t("viewDescription")}
      size="md"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {item.is_service && (
            <Badge variant="outline">{t("serviceBadge")}</Badge>
          )}
          {!item.is_active && (
            <Badge variant="outline">{t("inactiveBadge")}</Badge>
          )}
        </div>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">{t("fieldSku")}</dt>
            <dd className="font-medium">{item.sku || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("fieldUnit")}</dt>
            <dd className="font-medium">{item.unit}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("fieldPrice")}</dt>
            <dd className="font-medium tabular-nums">{formatMoney(item.unit_price)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("fieldTaxRate")}</dt>
            <dd className="font-medium tabular-nums">{formatPercent(item.tax_rate)}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-muted-foreground">{t("fieldDescription")}</dt>
            <dd className="font-medium whitespace-pre-wrap">
              {item.description || "—"}
            </dd>
          </div>
        </dl>
        <div className="flex justify-end gap-2">
          {onEdit && (
            <CanAccess scope={NidusScope.ITEM_WRITE}>
              <Button
                type="button"
                onClick={() => {
                  onClose(false);
                  onEdit(item);
                }}
              >
                {t("editAction")}
              </Button>
            </CanAccess>
          )}
          <Button type="button" variant="outline" onClick={() => onClose(false)}>
            {t("closeAction")}
          </Button>
        </div>
      </div>
    </ModalWrapper>
  );
}
