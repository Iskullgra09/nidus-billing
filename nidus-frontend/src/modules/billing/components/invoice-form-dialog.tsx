"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Plus, Trash2 } from "lucide-react";

import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { ActionResponse } from "@/core/types/api";
import { formatMoney, formatMoneyInput, formatPercentInput } from "../lib/format";
import { Party } from "../types/party";
import { Invoice, InvoicePayload } from "../types/invoice";

const lineSchema = z.object({
  description: z.string().min(1),
  quantity: z.string().min(1),
  unit_price: z.string().min(1),
  tax_rate: z.string().optional(),
  unit: z.string().min(1),
});

const invoiceSchema = z.object({
  customer_id: z.string().uuid(),
  payment_condition: z.enum(["contado", "credito"]),
  currency: z.enum(["CRC", "USD"]),
  due_date: z.string().optional(),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
  lines: z.array(lineSchema).min(1),
});

type InvoiceFormValues = z.infer<typeof invoiceSchema>;

interface InvoiceFormDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  invoice?: Invoice | null;
  customers: Party[];
  onCreate: (payload: InvoicePayload) => Promise<ActionResponse>;
  onUpdate: (id: string, payload: Partial<InvoicePayload>) => Promise<ActionResponse>;
}

function previewLineTotal(quantity: string, unitPrice: string, taxRate?: string) {
  const q = Number(quantity);
  const p = Number(unitPrice);
  const rate = taxRate ? Number(taxRate) : 0;
  if (![q, p, rate].every((n) => Number.isFinite(n))) return null;
  const sub = q * p;
  return sub + sub * (rate / 100);
}

export function InvoiceFormDialog({
  isOpen,
  onClose,
  invoice,
  customers,
  onCreate,
  onUpdate,
}: InvoiceFormDialogProps) {
  const t = useTranslations("BillingInvoices");
  const tCom = useTranslations("Common");
  const [isPending, setIsPending] = React.useState(false);

  const form = useForm<InvoiceFormValues>({
    resolver: zodResolver(invoiceSchema),
    defaultValues: {
      customer_id: "",
      payment_condition: "contado",
      currency: "CRC",
      due_date: "",
      reference_number: "",
      notes: "",
      lines: [
        {
          description: "",
          quantity: "1.00",
          unit_price: "0.00",
          tax_rate: "",
          unit: "unit",
        },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "lines",
  });

  const watchedLines = useWatch({ control: form.control, name: "lines" });
  const paymentCondition = useWatch({
    control: form.control,
    name: "payment_condition",
  });

  const previewTotals = React.useMemo(() => {
    let subtotal = 0;
    let taxTotal = 0;
    for (const line of watchedLines ?? []) {
      const q = Number(line.quantity);
      const p = Number(line.unit_price);
      const rate = line.tax_rate ? Number(line.tax_rate) : 0;
      if (![q, p, rate].every((n) => Number.isFinite(n))) continue;
      const sub = q * p;
      subtotal += sub;
      taxTotal += sub * (rate / 100);
    }
    return { subtotal, taxTotal, total: subtotal + taxTotal };
  }, [watchedLines]);

  React.useEffect(() => {
    form.reset({
      customer_id: invoice?.customer_id ?? customers[0]?.id ?? "",
      payment_condition: invoice?.payment_condition ?? "contado",
      currency: (invoice?.currency as "CRC" | "USD") ?? "CRC",
      due_date: invoice?.due_date ?? "",
      reference_number: invoice?.reference_number ?? "",
      notes: invoice?.notes ?? "",
      lines:
        invoice?.lines.map((line) => ({
          description: line.description,
          quantity: formatMoneyInput(line.quantity),
          unit_price: formatMoneyInput(line.unit_price),
          tax_rate: formatPercentInput(line.tax_rate),
          unit: line.unit,
        })) ?? [
          {
            description: "",
            quantity: "1.00",
            unit_price: "0.00",
            tax_rate: "",
            unit: "unit",
          },
        ],
    });
  }, [invoice, customers, form, isOpen]);

  const handleOpenChange = (open: boolean) => {
    if (!open) form.reset();
    onClose(open);
  };

  const onSubmit = async (values: InvoiceFormValues) => {
    setIsPending(true);
    const payload: InvoicePayload = {
      customer_id: values.customer_id,
      payment_condition: values.payment_condition,
      currency: values.currency,
      due_date: values.due_date || null,
      reference_number: values.reference_number || null,
      notes: values.notes || null,
      lines: values.lines.map((line) => ({
        description: line.description,
        quantity: line.quantity,
        unit_price: line.unit_price,
        tax_rate: line.tax_rate || null,
        unit: line.unit,
      })),
    };

    const result = invoice
      ? await onUpdate(invoice.id, payload)
      : await onCreate(payload);

    setIsPending(false);
    if (result.status === "success") {
      toast.success(result.message);
      handleOpenChange(false);
    } else {
      toast.error(result.message);
    }
  };

  return (
    <ModalWrapper
      isOpen={isOpen}
      onClose={handleOpenChange}
      title={invoice ? t("editTitle") : t("createTitle")}
      description={t("formDescription")}
      size="lg"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <article className="rounded-lg border bg-background overflow-hidden">
            <header className="border-b px-5 py-4 space-y-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                {t("documentLabel")}
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="customer_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("billToLabel")}</FormLabel>
                      <FormControl>
                        <select
                          className="border-input bg-background h-9 w-full rounded-lg border px-2.5 text-sm"
                          {...field}
                        >
                          <option value="" disabled>
                            {t("customerPlaceholder")}
                          </option>
                          {customers.map((customer) => (
                            <option key={customer.id} value={customer.id}>
                              {customer.name}
                            </option>
                          ))}
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="payment_condition"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("fieldPaymentCondition")}</FormLabel>
                      <FormControl>
                        <select
                          className="border-input bg-background h-9 w-full rounded-lg border px-2.5 text-sm"
                          {...field}
                        >
                          <option value="contado">{t("contado")}</option>
                          <option value="credito">{t("credito")}</option>
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="currency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("fieldCurrency")}</FormLabel>
                      <FormControl>
                        <select
                          className="border-input bg-background h-9 w-full rounded-lg border px-2.5 text-sm"
                          {...field}
                        >
                          <option value="CRC">CRC</option>
                          <option value="USD">USD</option>
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {paymentCondition === "credito" && (
                  <FormField
                    control={form.control}
                    name="due_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>{t("fieldDueDate")}</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
                <FormField
                  control={form.control}
                  name="reference_number"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("fieldReference")}</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder={t("referencePlaceholder")} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="notes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("fieldNotes")}</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </header>

            <section className="px-3 sm:px-5 py-3 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  {t("linesTitle")}
                </p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    append({
                      description: "",
                      quantity: "1.00",
                      unit_price: "0.00",
                      tax_rate: "13",
                      unit: "unit",
                    })
                  }
                >
                  <Plus className="size-4" />
                  {t("addLine")}
                </Button>
              </div>

              <div className="hidden sm:grid sm:grid-cols-12 gap-2 px-1 text-xs text-muted-foreground">
                <span className="col-span-4">{t("fieldDescription")}</span>
                <span className="col-span-2 text-right">{t("fieldQuantity")}</span>
                <span className="col-span-2 text-right">{t("fieldUnitPrice")}</span>
                <span className="col-span-2 text-right">{t("fieldTaxRate")}</span>
                <span className="col-span-1 text-right">{t("tableTotal")}</span>
                <span className="col-span-1" />
              </div>

              {fields.map((field, index) => {
                const line = watchedLines?.[index];
                const lineTotal = previewLineTotal(
                  line?.quantity ?? "0",
                  line?.unit_price ?? "0",
                  line?.tax_rate,
                );
                return (
                  <div
                    key={field.id}
                    className="grid gap-2 rounded-md border border-border/60 bg-muted/20 p-3 sm:grid-cols-12 sm:items-start"
                  >
                    <FormField
                      control={form.control}
                      name={`lines.${index}.description`}
                      render={({ field: lineField }) => (
                        <FormItem className="sm:col-span-4">
                          <FormLabel className="sm:sr-only">{t("fieldDescription")}</FormLabel>
                          <FormControl>
                            <Input {...lineField} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`lines.${index}.quantity`}
                      render={({ field: lineField }) => (
                        <FormItem className="sm:col-span-2">
                          <FormLabel className="sm:sr-only">{t("fieldQuantity")}</FormLabel>
                          <FormControl>
                            <Input className="text-right tabular-nums" {...lineField} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`lines.${index}.unit_price`}
                      render={({ field: lineField }) => (
                        <FormItem className="sm:col-span-2">
                          <FormLabel className="sm:sr-only">{t("fieldUnitPrice")}</FormLabel>
                          <FormControl>
                            <Input className="text-right tabular-nums" {...lineField} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`lines.${index}.tax_rate`}
                      render={({ field: lineField }) => (
                        <FormItem className="sm:col-span-2">
                          <FormLabel className="sm:sr-only">{t("fieldTaxRate")}</FormLabel>
                          <FormControl>
                            <Input
                              className="text-right tabular-nums"
                              placeholder="13"
                              {...lineField}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <div className="sm:col-span-1 flex h-9 items-center justify-end text-sm tabular-nums font-medium">
                      {lineTotal == null ? "—" : formatMoney(lineTotal)}
                    </div>
                    <div className="sm:col-span-1 flex justify-end">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="text-destructive"
                        disabled={fields.length <= 1}
                        onClick={() => remove(index)}
                        aria-label={t("removeLine")}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </section>

            <footer className="border-t px-5 py-4 flex justify-end">
              <dl className="w-full max-w-xs space-y-1.5 text-sm">
                <div className="flex justify-between gap-6">
                  <dt className="text-muted-foreground">{t("subtotalLabel")}</dt>
                  <dd className="tabular-nums">{formatMoney(previewTotals.subtotal)}</dd>
                </div>
                <div className="flex justify-between gap-6">
                  <dt className="text-muted-foreground">{t("taxTotalLabel")}</dt>
                  <dd className="tabular-nums">{formatMoney(previewTotals.taxTotal)}</dd>
                </div>
                <div className="flex justify-between gap-6 border-t pt-2 font-semibold">
                  <dt>{t("tableTotal")}</dt>
                  <dd className="tabular-nums">{formatMoney(previewTotals.total)}</dd>
                </div>
              </dl>
            </footer>
          </article>

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              {tCom("cancel")}
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {invoice ? t("saveButton") : t("createButton")}
            </Button>
          </div>
        </form>
      </Form>
    </ModalWrapper>
  );
}
