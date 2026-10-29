"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { ModalWrapper } from "@/shared/components/layout/modal-wrapper";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Checkbox } from "@/shared/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { ActionResponse } from "@/core/types/api";
import { CatalogItem, ItemPayload } from "../types/item";

const itemSchema = z.object({
  name: z.string().min(1),
  sku: z.string().optional(),
  description: z.string().optional(),
  unit: z.string().min(1),
  unit_price: z.string().min(1),
  tax_rate: z.string().optional(),
  is_service: z.boolean(),
  is_active: z.boolean(),
});

type ItemFormValues = z.infer<typeof itemSchema>;

interface ItemFormDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  item?: CatalogItem | null;
  onCreate: (payload: ItemPayload) => Promise<ActionResponse>;
  onUpdate: (id: string, payload: Partial<ItemPayload>) => Promise<ActionResponse>;
}

export function ItemFormDialog({
  isOpen,
  onClose,
  item,
  onCreate,
  onUpdate,
}: ItemFormDialogProps) {
  const t = useTranslations("BillingItems");
  const tCom = useTranslations("Common");
  const [isPending, setIsPending] = React.useState(false);

  const form = useForm<ItemFormValues>({
    resolver: zodResolver(itemSchema),
    defaultValues: {
      name: "",
      sku: "",
      description: "",
      unit: "unit",
      unit_price: "0",
      tax_rate: "",
      is_service: false,
      is_active: true,
    },
  });

  React.useEffect(() => {
    form.reset({
      name: item?.name ?? "",
      sku: item?.sku ?? "",
      description: item?.description ?? "",
      unit: item?.unit ?? "unit",
      unit_price: item?.unit_price ?? "0",
      tax_rate: item?.tax_rate ?? "",
      is_service: item?.is_service ?? false,
      is_active: item?.is_active ?? true,
    });
  }, [item, form, isOpen]);

  const handleOpenChange = (open: boolean) => {
    if (!open) form.reset();
    onClose(open);
  };

  const onSubmit = async (values: ItemFormValues) => {
    setIsPending(true);
    const payload: ItemPayload = {
      name: values.name,
      sku: values.sku || null,
      description: values.description || null,
      unit: values.unit,
      unit_price: values.unit_price,
      tax_rate: values.tax_rate ? values.tax_rate : null,
      is_service: values.is_service,
      is_active: values.is_active,
    };

    const result = item
      ? await onUpdate(item.id, payload)
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
      title={item ? t("editTitle") : t("createTitle")}
      description={t("formDescription")}
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("fieldName")}</FormLabel>
                <FormControl>
                  <Input {...field} placeholder={t("namePlaceholder")} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="sku"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldSku")}</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="unit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldUnit")}</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="unit_price"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldPrice")}</FormLabel>
                  <FormControl>
                    <Input {...field} inputMode="decimal" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="tax_rate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldTaxRate")}</FormLabel>
                  <FormControl>
                    <Input {...field} inputMode="decimal" placeholder="13" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("fieldDescription")}</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="is_service"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center gap-3 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={(checked) => field.onChange(checked === true)}
                  />
                </FormControl>
                <FormLabel className="font-normal">{t("fieldService")}</FormLabel>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="is_active"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center gap-3 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={(checked) => field.onChange(checked === true)}
                  />
                </FormControl>
                <FormLabel className="font-normal">{t("fieldActive")}</FormLabel>
              </FormItem>
            )}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isPending}
            >
              {tCom("cancel")}
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              {item ? t("saveButton") : t("createButton")}
            </Button>
          </div>
        </form>
      </Form>
    </ModalWrapper>
  );
}
