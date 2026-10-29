"use client";

import { useTranslations } from "next-intl";

import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Party } from "../types/party";

interface PartyDetailDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  party: Party | null;
  namespace: "BillingCustomers" | "BillingSuppliers";
  writeScope: NidusScope;
  onEdit?: (party: Party) => void;
}

export function PartyDetailDialog({
  isOpen,
  onClose,
  party,
  namespace,
  writeScope,
  onEdit,
}: PartyDetailDialogProps) {
  const t = useTranslations(namespace);

  if (!party) return null;

  return (
    <ModalWrapper
      isOpen={isOpen}
      onClose={onClose}
      title={party.name}
      description={t("viewDescription")}
      size="md"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {!party.is_active && (
            <Badge variant="outline">{t("inactiveBadge")}</Badge>
          )}
        </div>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">{t("fieldEmail")}</dt>
            <dd className="font-medium">{party.email || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("fieldPhone")}</dt>
            <dd className="font-medium">{party.phone || "—"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("fieldTaxId")}</dt>
            <dd className="font-medium">{party.tax_id || "—"}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-muted-foreground">{t("fieldNotes")}</dt>
            <dd className="font-medium whitespace-pre-wrap">{party.notes || "—"}</dd>
          </div>
        </dl>
        <div className="flex justify-end gap-2">
          {onEdit && (
            <CanAccess scope={writeScope}>
              <Button
                type="button"
                onClick={() => {
                  onClose(false);
                  onEdit(party);
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
