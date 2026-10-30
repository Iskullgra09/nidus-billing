"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Info } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";

type HaciendaStatusValue =
  | "pending"
  | "submitted"
  | "processing"
  | "accepted"
  | "rejected"
  | "error";

interface HaciendaStatusBadgeProps {
  status: HaciendaStatusValue | string;
  message?: string | null;
  className?: string;
}

function badgeVariant(status: string) {
  if (status === "rejected" || status === "error") return "destructive" as const;
  if (status === "accepted") return "default" as const;
  return "secondary" as const;
}

export function HaciendaStatusBadge({
  status,
  message,
  className,
}: HaciendaStatusBadgeProps) {
  const t = useTranslations("BillingInvoices");
  const [open, setOpen] = React.useState(false);
  const hasDetail = Boolean(message?.trim());
  const labelKey = `haciendaStatus.${status}` as const;

  const badge = (
    <Badge variant={badgeVariant(status)} className={className}>
      <span>{t(labelKey)}</span>
      {hasDetail && <Info className="ml-1 size-3 opacity-80" aria-hidden />}
    </Badge>
  );

  if (!hasDetail) {
    return badge;
  }

  return (
    <>
      <button
        type="button"
        className="inline-flex rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onClick={(event) => {
          event.stopPropagation();
          setOpen(true);
        }}
        aria-label={t("haciendaDetailTitle")}
      >
        {badge}
      </button>
      <ModalWrapper
        isOpen={open}
        onClose={setOpen}
        title={t("haciendaDetailTitle")}
        description={t("haciendaDetailDescription")}
        size="sm"
      >
        <div className="space-y-4 text-sm">
          <p className="max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed wrap-anywhere">
            {message}
          </p>
          <div className="flex justify-end">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              {t("closeAction")}
            </Button>
          </div>
        </div>
      </ModalWrapper>
    </>
  );
}
