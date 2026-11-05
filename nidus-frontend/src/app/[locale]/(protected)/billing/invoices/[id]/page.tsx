import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import {
  getInvoiceAction,
  getInvoiceFiscalAction,
} from "@/modules/billing/actions/invoices";
import { InvoiceDocument } from "@/modules/billing/components/invoice-document";
import { InvoiceDocumentActions } from "@/modules/billing/components/invoice-document-actions";

type Params = Promise<{ id: string }>;

export default async function InvoiceDocumentPage({
  params,
}: {
  params: Params;
}) {
  const { id } = await params;
  const t = await getTranslations("BillingInvoices");
  const invoice = await getInvoiceAction(id);
  if (!invoice) notFound();

  const fiscalResult = await getInvoiceFiscalAction(id);
  const fiscal =
    fiscalResult.status === "success" ? fiscalResult.data ?? null : null;

  return (
    <div className="space-y-6 print:space-y-0">
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          .invoice-print-root,
          .invoice-print-root * { visibility: visible !important; }
          .invoice-print-root {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            padding: 0;
            margin: 0;
          }
          .print\\:hidden { display: none !important; }
        }
      `}</style>

      <div className="print:hidden space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">{t("documentPageTitle")}</h1>
        <p className="text-sm text-muted-foreground">{t("documentPageDescription")}</p>
      </div>

      <InvoiceDocumentActions />

      <div className="invoice-print-root">
        <InvoiceDocument invoice={invoice} fiscal={fiscal} />
      </div>
    </div>
  );
}
