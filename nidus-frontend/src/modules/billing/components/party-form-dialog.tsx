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
import { Party, PartyPayload } from "../types/party";

const partySchema = z.object({
  name: z.string().min(1),
  email: z.string().email().optional().or(z.literal("")),
  phone: z.string().optional(),
  tax_id: z.string().optional(),
  notes: z.string().optional(),
  is_active: z.boolean(),
});

type PartyFormValues = z.infer<typeof partySchema>;

interface PartyFormDialogProps {
  isOpen: boolean;
  onClose: (open: boolean) => void;
  party?: Party | null;
  namespace: "BillingCustomers" | "BillingSuppliers";
  onCreate: (payload: PartyPayload) => Promise<ActionResponse>;
  onUpdate: (id: string, payload: Partial<PartyPayload>) => Promise<ActionResponse>;
}

export function PartyFormDialog({
  isOpen,
  onClose,
  party,
  namespace,
  onCreate,
  onUpdate,
}: PartyFormDialogProps) {
  const t = useTranslations(namespace);
  const tCom = useTranslations("Common");
  const [isPending, setIsPending] = React.useState(false);

  const form = useForm<PartyFormValues>({
    resolver: zodResolver(partySchema),
    defaultValues: {
      name: "",
      email: "",
      phone: "",
      tax_id: "",
      notes: "",
      is_active: true,
    },
  });

  React.useEffect(() => {
    form.reset({
      name: party?.name ?? "",
      email: party?.email ?? "",
      phone: party?.phone ?? "",
      tax_id: party?.tax_id ?? "",
      notes: party?.notes ?? "",
      is_active: party?.is_active ?? true,
    });
  }, [party, form, isOpen]);

  const handleOpenChange = (open: boolean) => {
    if (!open) form.reset();
    onClose(open);
  };

  const onSubmit = async (values: PartyFormValues) => {
    setIsPending(true);
    const payload: PartyPayload = {
      name: values.name,
      email: values.email || null,
      phone: values.phone || null,
      tax_id: values.tax_id || null,
      notes: values.notes || null,
      is_active: values.is_active,
    };

    const result = party
      ? await onUpdate(party.id, payload)
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
      title={party ? t("editTitle") : t("createTitle")}
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
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t("fieldEmail")}</FormLabel>
                <FormControl>
                  <Input {...field} type="email" placeholder={t("emailPlaceholder")} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldPhone")}</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="tax_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("fieldTaxId")}</FormLabel>
                  <FormControl>
                    <Input {...field} />
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
              {party ? t("saveButton") : t("createButton")}
            </Button>
          </div>
        </form>
      </Form>
    </ModalWrapper>
  );
}
