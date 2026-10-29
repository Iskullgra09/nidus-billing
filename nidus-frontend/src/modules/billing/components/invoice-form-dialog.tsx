"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useFieldArray, useForm } from "react-hook-form";
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
      due_date: "",
      reference_number: "",
      notes: "",
      lines: [{ description: "", quantity: "1", unit_price: "0", tax_rate: "", unit: "unit" }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "lines",
  });

  React.useEffect(() => {
    form.reset({
      customer_id: invoice?.customer_id ?? customers[0]?.id ?? "",
      payment_condition: invoice?.payment_condition ?? "contado",
      due_date: invoice?.due_date ?? "",
      reference_number: invoice?.reference_number ?? "",
      notes: invoice?.notes ?? "",
      lines:
        invoice?.lines.map((line) => ({
          description: line.description,
          quantity: line.quantity,
          unit_price: line.unit_price,
          tax_rate: line.tax_rate ?? "",
          unit: line.unit,
        })) ?? [{ description: "", quantity: "1", unit_price: "0", tax_rate: "", unit: "unit" }],
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
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="customer_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldCustomer")}</FormLabel>
                  <FormControl>
                    <select
                      className="border-input bg-background h-8 w-full rounded-lg border px-2.5 text-sm"
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
                      className="border-input bg-background h-8 w-full rounded-lg border px-2.5 text-sm"
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
                    unit_price: "0",
                    tax_rate: "",
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
                className="grid gap-2 rounded-lg border border-border/50 p-3 sm:grid-cols-12"
              >
                <FormField
                  control={form.control}
                  name={`lines.${index}.description`}
                  render={({ field: lineField }) => (
                    <FormItem className="sm:col-span-4">
                      <FormLabel>{t("fieldDescription")}</FormLabel>
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
                      <FormLabel>{t("fieldQuantity")}</FormLabel>
                      <FormControl>
                        <Input {...lineField} />
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
                      <FormLabel>{t("fieldUnitPrice")}</FormLabel>
                      <FormControl>
                        <Input {...lineField} />
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
                      <FormLabel>{t("fieldTaxRate")}</FormLabel>
                      <FormControl>
                        <Input {...lineField} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="flex items-end sm:col-span-2">
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
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2">
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
