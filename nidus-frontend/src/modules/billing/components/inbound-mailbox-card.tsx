"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/core/i18n/routing";
import { Copy, Mail } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { CanAccess } from "@/modules/access/components/can-access";
import { NidusScope } from "@/shared/access/scopes";
import { InboundMailbox } from "../types/mailbox";
import { updateInboundMailboxAction } from "../actions/inbound";

interface InboundMailboxCardProps {
  mailbox: InboundMailbox | null;
}

export function InboundMailboxCard({ mailbox }: InboundMailboxCardProps) {
  const t = useTranslations("BillingInbound");
  const router = useRouter();
  const [pending, setPending] = React.useState(false);

  if (!mailbox) return null;

  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(mailbox.address);
      toast.success(t("mailboxCopied"));
    } catch {
      toast.error(t("mailboxCopyFailed"));
    }
  };

  const toggleEnabled = async () => {
    setPending(true);
    try {
      const res = await updateInboundMailboxAction(!mailbox.enabled);
      if (res.status === "success") {
        toast.success(res.message || undefined);
        router.refresh();
      } else {
        toast.error(res.message || undefined);
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="border-border bg-muted/30 space-y-3 rounded-lg border p-4">
      <div className="flex items-start gap-3">
        <Mail className="text-muted-foreground mt-0.5 size-5 shrink-0" />
        <div className="min-w-0 flex-1 space-y-1">
          <p className="text-sm font-medium">{t("mailboxTitle")}</p>
          <p className="text-muted-foreground text-sm">{t("mailboxDescription")}</p>
          <p className="truncate font-mono text-sm">{mailbox.address}</p>
          <p className="text-muted-foreground text-xs">
            {mailbox.enabled ? t("mailboxEnabled") : t("mailboxDisabled")}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" variant="outline" onClick={() => void copyAddress()}>
          <Copy className="size-4" />
          {t("mailboxCopy")}
        </Button>
        <CanAccess scope={NidusScope.INBOUND_WRITE}>
          <Button
            type="button"
            size="sm"
            variant="secondary"
            disabled={pending}
            onClick={() => void toggleEnabled()}
          >
            {mailbox.enabled ? t("mailboxDisable") : t("mailboxEnable")}
          </Button>
        </CanAccess>
      </div>
    </div>
  );
}
