"use client";

import { useTranslations } from "next-intl";

import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { formatMoney, formatPercent } from "../lib/format";
import { Invoice, InvoiceEmailDelivery, InvoiceFiscal } from "../types/invoice";

interface InvoiceDetailDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  invoice: Invoice | null;
  emailDeliveries?: InvoiceEmailDelivery[];
  fiscal?: InvoiceFiscal | null;
  onEditDraft?: (invoice: Invoice) => void;
  onSendEmail?: () => void;
  onEmitHacienda?: () => void;
  onVerifyHacienda?: () => void;
}

export function InvoiceDetailDialog({
  isOpen,
  onClose,
  invoice,
  emailDeliveries = [],
  fiscal = null,
  onEditDraft,
  onSendEmail,
  onEmitHacienda,
  onVerifyHacienda,
}: InvoiceDetailDialogProps) {
  const t = useTranslations("BillingInvoices");

  if (!invoice) return null;

  const canEmitHacienda =
    invoice.status === "issued" ||
    invoice.status === "partial" ||
    invoice.status === "paid";
  const fiscalStatus = fiscal?.status;

  const docLabel =
    invoice.document_number ||
    invoice.reference_number ||
    t("viewTitle");

  return (
    <ModalWrapper
      isOpen={isOpen}
      onClose={onClose}
      title={t("viewTitle")}
      description={t("viewDescription")}
      size="lg"
    >
      <div className="space-y-4">
        <article className="rounded-lg border bg-background text-foreground shadow-sm overflow-hidden">
          <header className="border-b px-6 py-5 flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                {t("documentLabel")}
              </p>
              <h3 className="text-xl font-semibold tracking-tight">{docLabel}</h3>
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <Badge
                  variant={invoice.status === "void" ? "destructive" : "secondary"}
                >
                  {t(`status.${invoice.status}`)}
                </Badge>
                {fiscalStatus && (
                  <Badge
                    variant={
                      fiscalStatus === "rejected" || fiscalStatus === "error"
                        ? "destructive"
                        : fiscalStatus === "accepted"
                          ? "default"
                          : "secondary"
                    }
                  >
                    {t(`haciendaStatus.${fiscalStatus}`)}
                  </Badge>
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
                <dt className="text-muted-foreground inline">{t("fieldPaymentCondition")}: </dt>
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

          <section className="px-6 py-4 grid gap-4 sm:grid-cols-2 border-b text-sm">
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

          <section className="px-2 sm:px-4 py-2">
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
                        <div className="text-xs text-muted-foreground">
                          {line.sku}
                        </div>
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

          <section className="px-6 py-4 flex justify-end border-b">
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

          {invoice.payments.length > 0 && (
            <section className="px-6 py-4">
              <h4 className="text-xs uppercase tracking-wide text-muted-foreground mb-3">
                {t("paymentsTitle")}
              </h4>
              <ul className="space-y-2 text-sm">
                {invoice.payments.map((payment) => (
                  <li
                    key={payment.id}
                    className="flex items-center justify-between gap-4 border-b border-border/40 pb-2 last:border-0"
                  >
                    <span className="text-muted-foreground">
                      {payment.method} ·{" "}
                      {new Date(payment.paid_at).toLocaleString("es-CR")}
                    </span>
                    <span className="tabular-nums font-medium">
                      {formatMoney(payment.amount, {
                        currency: invoice.currency,
                        withCurrency: true,
                      })}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="px-6 py-4 border-t">
            <h4 className="text-xs uppercase tracking-wide text-muted-foreground mb-3">
              {t("haciendaTitle")}
            </h4>
            {!fiscal ? (
              <p className="text-sm text-muted-foreground">{t("haciendaEmpty")}</p>
            ) : (
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">{t("haciendaClave")}</dt>
                  <dd className="font-mono text-xs break-all">
                    {fiscal.clave || "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">{t("haciendaConsecutive")}</dt>
                  <dd className="font-mono text-xs">
                    {fiscal.consecutive || "—"}
                  </dd>
                </div>
                {fiscal.mh_message && (
                  <div className="sm:col-span-2">
                    <dt className="text-muted-foreground">{t("haciendaMessage")}</dt>
                    <dd className="text-muted-foreground">{fiscal.mh_message}</dd>
                  </div>
                )}
                {fiscal.mock_mode && (
                  <div className="sm:col-span-2">
                    <Badge variant="secondary">{t("haciendaMock")}</Badge>
                  </div>
                )}
              </dl>
            )}
          </section>

          <section className="px-6 py-4 border-t">
            <h4 className="text-xs uppercase tracking-wide text-muted-foreground mb-3">
              {t("emailsTitle")}
            </h4>
            {emailDeliveries.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("emailsEmpty")}</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {emailDeliveries.map((delivery) => (
                  <li
                    key={delivery.id}
                    className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-2 last:border-0"
                  >
                    <span className="text-muted-foreground">
                      {delivery.to_email} · {t(`emailStatus.${delivery.status}`)}
                      {delivery.sent_at
                        ? ` · ${new Date(delivery.sent_at).toLocaleString("es-CR")}`
                        : ""}
                    </span>
                    {delivery.error_message && (
                      <span className="text-destructive text-xs">
                        {delivery.error_message}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </article>

        <div className="flex flex-wrap justify-end gap-2">
          {canEmitHacienda &&
            onEmitHacienda &&
            (!fiscalStatus ||
              fiscalStatus === "rejected" ||
              fiscalStatus === "error") && (
            <CanAccess scope={NidusScope.INVOICE_WRITE}>
              <Button type="button" variant="secondary" onClick={onEmitHacienda}>
                {t("emitHaciendaAction")}
              </Button>
            </CanAccess>
          )}
          {fiscal?.clave && onVerifyHacienda && (
            <CanAccess scope={NidusScope.INVOICE_WRITE}>
              <Button type="button" variant="secondary" onClick={onVerifyHacienda}>
                {t("verifyHaciendaAction")}
              </Button>
            </CanAccess>
          )}
          {onSendEmail && (
            <CanAccess scope={NidusScope.INVOICE_WRITE}>
              <Button type="button" variant="secondary" onClick={onSendEmail}>
                {t("emailAction")}
              </Button>
            </CanAccess>
          )}
          {invoice.status === "draft" && onEditDraft && (
            <CanAccess scope={NidusScope.INVOICE_WRITE}>
              <Button
                type="button"
                onClick={() => {
                  onClose(false);
                  onEditDraft(invoice);
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
