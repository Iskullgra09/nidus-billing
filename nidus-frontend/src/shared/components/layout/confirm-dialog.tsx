"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { cn } from "@/shared/lib/utils";

type ModalSize = "sm" | "md";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
  size?: ModalSize;
  loading?: boolean;
  onConfirm: () => void | Promise<void>;
}

const sizeClasses: Record<ModalSize, string> = {
  sm: "sm:max-w-[425px]",
  md: "sm:max-w-[480px]",
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel,
  variant = "default",
  size = "sm",
  loading = false,
  onConfirm,
}: ConfirmDialogProps) {
  const t = useTranslations("Common");
  const [pending, setPending] = React.useState(false);
  const busy = loading || pending;

  const handleConfirm = async () => {
    if (busy) return;
    setPending(true);
    try {
      await onConfirm();
    } finally {
      setPending(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (busy) return;
        onOpenChange(next);
      }}
    >
      <DialogContent
        showCloseButton={!busy}
        className={cn(sizeClasses[size], "shadow-lg")}
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={busy}
            onClick={() => onOpenChange(false)}
          >
            {cancelLabel ?? t("cancel")}
          </Button>
          <Button
            type="button"
            variant={variant === "destructive" ? "destructive" : "default"}
            disabled={busy}
            onClick={() => void handleConfirm()}
          >
            {busy ? t("loading") : (confirmLabel ?? t("confirm"))}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
