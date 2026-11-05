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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { ActionResponse } from "@/core/types/api";
import {
  formatMoney,
  formatMoneyInput,
  formatPercentInput,
  parseMoney,
} from "../lib/format";
import { Party } from "../types/party";
import { Quote, QuotePayload } from "../types/quote";

const lineSchema = z.object({
  description: z.string().min(1),
  quantity: z.string().min(1),
  unit_price: z.string().min(1),
  tax_rate: z.string().optional(),
  cabys_code: z.string().optional(),
  unit: z.string().min(1),
});

const quoteSchema = z.object({
  customer_id: z.string().uuid(),
  currency: z.enum(["CRC", "USD"]),
  exchange_rate: z.string().optional(),
  exchange_rate_date: z.string().optional(),
  valid_until: z.string().optional(),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
  lines: z.array(lineSchema).min(1),
});

type QuoteFormValues = z.infer<typeof quoteSchema>;

interface QuoteFormDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  quote?: Quote | null;
  customers: Party[];
  onCreate: (payload: QuotePayload) => Promise<ActionResponse>;
  onUpdate: (id: string, payload: Partial<QuotePayload>) => Promise<ActionResponse>;
}

function previewLineTotal(quantity: string, unitPrice: string, taxRate?: string) {
  const q = parseMoney(quantity);
  const p = parseMoney(unitPrice);
  const rate = taxRate ? parseMoney(taxRate) ?? 0 : 0;
  if (q == null || p == null || !Number.isFinite(rate)) return null;
  const sub = q * p;
  return sub + sub * (rate / 100);
}

export function QuoteFormDialog({
  isOpen,
  onClose,
  quote,
  customers,
  onCreate,
  onUpdate,
}: QuoteFormDialogProps) {
  const t = useTranslations("BillingQuotes");
  const tCom = useTranslations("Common");
  const [isPending, setIsPending] = React.useState(false);

  const form = useForm<QuoteFormValues>({
    resolver: zodResolver(quoteSchema),
    defaultValues: {
      customer_id: "",
      currency: "CRC",
      exchange_rate: "",
      exchange_rate_date: "",
      valid_until: "",
      reference_number: "",
      notes: "",
      lines: [
        {
          description: "",
          quantity: "1",
          unit_price: "0.00",
          tax_rate: "13",
          cabys_code: "",
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
  const currency = useWatch({ control: form.control, name: "currency" });

  React.useEffect(() => {
    if (!isOpen) return;
    if (quote) {
      form.reset({
        customer_id: quote.customer_id,
        currency: (quote.currency as "CRC" | "USD") || "CRC",
        exchange_rate: quote.exchange_rate
          ? formatMoneyInput(quote.exchange_rate)
          : "",
        exchange_rate_date: quote.exchange_rate_date ?? "",
        valid_until: quote.valid_until ?? "",
        reference_number: quote.reference_number ?? "",
        notes: quote.notes ?? "",
        lines: quote.lines.map((line) => ({
          description: line.description,
          quantity: formatMoneyInput(line.quantity),
          unit_price: formatMoneyInput(line.unit_price),
          tax_rate: line.tax_rate ? formatPercentInput(line.tax_rate) : "",
          cabys_code: line.cabys_code ?? "",
          unit: line.unit,
        })),
      });
    } else {
      form.reset({
        customer_id: customers[0]?.id ?? "",
        currency: "CRC",
        exchange_rate: "",
        exchange_rate_date: "",
        valid_until: "",
        reference_number: "",
        notes: "",
        lines: [
          {
            description: "",
            quantity: "1",
            unit_price: "0.00",
            tax_rate: "13",
            cabys_code: "",
            unit: "unit",
          },
        ],
      });
    }
  }, [isOpen, quote, customers, form]);

  const previewTotal = React.useMemo(() => {
    return (watchedLines || []).reduce((sum, line) => {
      const lineTotal = previewLineTotal(
        line.quantity,
        line.unit_price,
        line.tax_rate,
      );
      return sum + (lineTotal ?? 0);
    }, 0);
  }, [watchedLines]);

  const onSubmit = async (values: QuoteFormValues) => {
    setIsPending(true);
    const payload: QuotePayload = {
      customer_id: values.customer_id,
      currency: values.currency,
      exchange_rate:
        values.currency === "USD" && values.exchange_rate
          ? formatMoneyInput(values.exchange_rate)
          : null,
      exchange_rate_date:
        values.currency === "USD" && values.exchange_rate_date
          ? values.exchange_rate_date
          : null,
      valid_until: values.valid_until || null,
      reference_number: values.reference_number || null,
      notes: values.notes || null,
      lines: values.lines.map((line) => ({
        description: line.description,
        quantity: formatMoneyInput(line.quantity),
        unit_price: formatMoneyInput(line.unit_price),
        tax_rate: line.tax_rate ? formatPercentInput(line.tax_rate) : null,
        cabys_code: line.cabys_code || null,
        unit: line.unit,
      })),
    };
    const result = quote
      ? await onUpdate(quote.id, payload)
      : await onCreate(payload);
    setIsPending(false);
    if (result.status === "success") {
      toast.success(result.message);
      onClose(false);
    } else {
      toast.error(result.message);
    }
  };

  return (
    <ModalWrapper
      isOpen={isOpen}
      onClose={onClose}
      title={quote ? t("editTitle") : t("createTitle")}
      description={t("formDescription")}
      className="sm:max-w-3xl"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="customer_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("fieldCustomer")}</FormLabel>
                <Select
                  value={field.value || undefined}
                  onValueChange={field.onChange}
                >
                  <FormControl>
                    <SelectTrigger className="h-9 w-full">
                      <SelectValue placeholder={t("customerPlaceholder")} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {customers.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="grid gap-3 sm:grid-cols-3">
            <FormField
              control={form.control}
              name="currency"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldCurrency")}</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger className="h-9 w-full">
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="CRC">CRC</SelectItem>
                      <SelectItem value="USD">USD</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="valid_until"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldValidUntil")}</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="reference_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldReference")}</FormLabel>
                  <FormControl>
                    <Input placeholder={t("referencePlaceholder")} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {currency === "USD" && (
            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="exchange_rate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("fieldExchangeRate")}</FormLabel>
                    <FormControl>
                      <Input
                        className="tabular-nums"
                        inputMode="decimal"
                        {...field}
                        onBlur={(e) => {
                          field.onBlur();
                          const n = formatMoneyInput(e.target.value);
                          if (n !== "0.00" || e.target.value.trim()) {
                            field.onChange(n);
                          }
                        }}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="exchange_rate_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("fieldExchangeRateDate")}</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">{t("linesTitle")}</p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() =>
                  append({
                    description: "",
                    quantity: "1",
                    unit_price: "0.00",
                    tax_rate: "13",
                    cabys_code: "",
                    unit: "unit",
                  })
                }
              >
                <Plus className="size-4" />
                {t("addLine")}
              </Button>
            </div>
            {fields.map((field, index) => (
              <div
                key={field.id}
                className="grid gap-2 rounded-md border border-border/60 p-3 sm:grid-cols-12"
              >
                <FormField
                  control={form.control}
                  name={`lines.${index}.description`}
                  render={({ field: f }) => (
                    <FormItem className="sm:col-span-4">
                      <FormLabel>{t("fieldDescription")}</FormLabel>
                      <FormControl>
                        <Input {...f} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name={`lines.${index}.quantity`}
                  render={({ field: f }) => (
                    <FormItem className="sm:col-span-2">
                      <FormLabel>{t("fieldQuantity")}</FormLabel>
                      <FormControl>
                        <Input
                          className="text-right tabular-nums"
                          inputMode="decimal"
                          {...f}
                          onBlur={(e) => {
                            f.onBlur();
                            f.onChange(formatMoneyInput(e.target.value));
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name={`lines.${index}.unit_price`}
                  render={({ field: f }) => (
                    <FormItem className="sm:col-span-3">
                      <FormLabel>{t("fieldUnitPrice")}</FormLabel>
                      <FormControl>
                        <Input
                          className="text-right tabular-nums"
                          inputMode="decimal"
                          {...f}
                          onBlur={(e) => {
                            f.onBlur();
                            f.onChange(formatMoneyInput(e.target.value));
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name={`lines.${index}.tax_rate`}
                  render={({ field: f }) => (
                    <FormItem className="sm:col-span-2">
                      <FormLabel>{t("fieldTaxRate")}</FormLabel>
                      <FormControl>
                        <Input
                          className="text-right tabular-nums"
                          inputMode="decimal"
                          placeholder="13"
                          {...f}
                          onBlur={(e) => {
                            f.onBlur();
                            const next = formatPercentInput(e.target.value);
                            f.onChange(next);
                          }}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="flex items-end sm:col-span-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    disabled={fields.length <= 1}
                    onClick={() => remove(index)}
                    aria-label={t("removeLine")}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
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

          <p className="text-sm text-muted-foreground">
            {t("previewTotal")}:{" "}
            {formatMoney(previewTotal, {
              currency: currency || "CRC",
              withCurrency: true,
            })}
          </p>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onClose(false)}>
              {tCom("cancel")}
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {quote ? t("saveButton") : t("createButton")}
            </Button>
          </div>
        </form>
      </Form>
    </ModalWrapper>
  );
}
