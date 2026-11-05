"use client";

import { useTranslations } from "next-intl";
import { ArrowLeft, Printer } from "lucide-react";

import { Link } from "@/core/i18n/routing";
import { Button } from "@/shared/ui/button";

export function InvoiceDocumentActions() {
  const t = useTranslations("BillingInvoices");

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
      <Button variant="ghost" size="sm" asChild>
        <Link href="/billing/invoices">
          <ArrowLeft className="size-4" />
          {t("backToList")}
        </Link>
      </Button>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => window.print()}
      >
        <Printer className="size-4" />
        {t("printAction")}
      </Button>
    </div>
  );
}
