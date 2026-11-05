"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/shared/ui/badge";
import { formatMoney, formatPercent } from "../lib/format";
import { Invoice, InvoiceFiscal } from "../types/invoice";
import { HaciendaStatusBadge } from "./hacienda-status-badge";

interface InvoiceDocumentProps {
  invoice: Invoice;
  fiscal?: InvoiceFiscal | null;
}

export function InvoiceDocument({
  invoice,
  fiscal = null,
}: InvoiceDocumentProps) {
  const t = useTranslations("BillingInvoices");
  const docLabel =
    invoice.document_number ||
    invoice.reference_number ||
    t("viewTitle");

  return (
    <article className="invoice-document mx-auto max-w-3xl rounded-lg border bg-background text-foreground shadow-sm overflow-hidden print:max-w-none print:rounded-none print:border-0 print:shadow-none">
      <header className="border-b px-6 py-5 flex flex-wrap items-start justify-between gap-4 print:px-0">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {t("documentLabel")}
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">{docLabel}</h1>
          <div className="flex flex-wrap items-center gap-2 pt-1 print:hidden">
            <Badge
              variant={invoice.status === "void" ? "destructive" : "secondary"}
            >
              {t(`status.${invoice.status}`)}
            </Badge>
            {fiscal?.status && (
              <HaciendaStatusBadge
                status={fiscal.status}
                message={fiscal.mh_message}
              />
            )}
            {invoice.is_overdue && (
              <Badge variant="destructive">{t("overdueBadge")}</Badge>
            )}
          </div>
        </div>
        <dl className="text-sm space-y-1 text-right min-w-40">
          <div>
            <dt className="text-muted-foreground inline">{t("fieldCurrency")}: </dt>
            <dd className="inline font-medium">{invoice.currency}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground inline">
              {t("fieldPaymentCondition")}:{" "}
            </dt>
            <dd className="inline font-medium">{t(invoice.payment_condition)}</dd>
          </div>
          {invoice.issued_at && (
            <div>
              <dt className="text-muted-foreground inline">{t("issuedAtLabel")}: </dt>
              <dd className="inline font-medium">
                {new Date(invoice.issued_at).toLocaleDateString("es-CR")}
              </dd>
            </div>
          )}
          {invoice.due_date && (
            <div>
              <dt className="text-muted-foreground inline">{t("fieldDueDate")}: </dt>
              <dd className="inline font-medium">{invoice.due_date}</dd>
            </div>
          )}
        </dl>
      </header>

      <section className="px-6 py-4 grid gap-4 sm:grid-cols-2 border-b text-sm print:px-0">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
            {t("billToLabel")}
          </p>
          <p className="font-semibold text-base">
            {invoice.customer_name || "—"}
          </p>
          {invoice.reference_number && (
            <p className="text-muted-foreground mt-1">
              {t("fieldReference")}: {invoice.reference_number}
            </p>
          )}
        </div>
        {invoice.notes && (
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
              {t("fieldNotes")}
            </p>
            <p className="whitespace-pre-wrap text-muted-foreground">
              {invoice.notes}
            </p>
          </div>
        )}
      </section>

      <section className="px-2 sm:px-4 py-2 print:px-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="px-3 py-2 text-left font-medium">#</th>
              <th className="px-3 py-2 text-left font-medium">
                {t("fieldDescription")}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {t("fieldQuantity")}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {t("fieldUnitPrice")}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {t("fieldTaxRate")}
              </th>
              <th className="px-3 py-2 text-right font-medium">
                {t("tableTotal")}
              </th>
            </tr>
          </thead>
          <tbody>
            {invoice.lines.map((line) => (
              <tr key={line.id} className="border-b border-border/50">
                <td className="px-3 py-2.5 text-muted-foreground">
                  {line.line_number}
                </td>
                <td className="px-3 py-2.5">
                  <div className="font-medium">{line.description}</div>
                  {line.sku && (
                    <div className="text-xs text-muted-foreground">{line.sku}</div>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatMoney(line.quantity)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatMoney(line.unit_price)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatPercent(line.tax_rate)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums font-medium">
                  {formatMoney(line.line_total)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="px-6 py-4 flex justify-end print:px-0">
        <dl className="w-full max-w-xs space-y-1.5 text-sm">
          <div className="flex justify-between gap-6">
            <dt className="text-muted-foreground">{t("subtotalLabel")}</dt>
            <dd className="tabular-nums">
              {formatMoney(invoice.subtotal, {
                currency: invoice.currency,
                withCurrency: true,
              })}
            </dd>
          </div>
          <div className="flex justify-between gap-6">
            <dt className="text-muted-foreground">{t("taxTotalLabel")}</dt>
            <dd className="tabular-nums">
              {formatMoney(invoice.tax_total, {
                currency: invoice.currency,
                withCurrency: true,
              })}
            </dd>
          </div>
          <div className="flex justify-between gap-6 border-t pt-2 font-semibold text-base">
            <dt>{t("tableTotal")}</dt>
            <dd className="tabular-nums">
              {formatMoney(invoice.total, {
                currency: invoice.currency,
                withCurrency: true,
              })}
            </dd>
          </div>
          <div className="flex justify-between gap-6 text-muted-foreground">
            <dt>{t("paidLabel")}</dt>
            <dd className="tabular-nums">
              {formatMoney(invoice.amount_paid, {
                currency: invoice.currency,
                withCurrency: true,
              })}
            </dd>
          </div>
          <div className="flex justify-between gap-6 font-medium">
            <dt>{t("tableBalance")}</dt>
            <dd className="tabular-nums">
              {formatMoney(invoice.balance_due, {
                currency: invoice.currency,
                withCurrency: true,
              })}
            </dd>
          </div>
        </dl>
      </section>
    </article>
  );
}
