"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
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

interface PromptDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  label: string;
  placeholder?: string;
  defaultValue?: string;
  inputType?: React.HTMLInputTypeAttribute;
  confirmLabel?: string;
  cancelLabel?: string;
  size?: ModalSize;
  loading?: boolean;
  allowEmpty?: boolean;
  onConfirm: (value: string) => void | Promise<void>;
}

const sizeClasses: Record<ModalSize, string> = {
  sm: "sm:max-w-[425px]",
  md: "sm:max-w-[480px]",
};

export function PromptDialog({
  open,
  onOpenChange,
  title,
  description,
  label,
  placeholder,
  defaultValue = "",
  inputType = "text",
  confirmLabel,
  cancelLabel,
  size = "sm",
  loading = false,
  allowEmpty = false,
  onConfirm,
}: PromptDialogProps) {
  const t = useTranslations("Common");
  const [value, setValue] = React.useState(defaultValue);
  const [pending, setPending] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const busy = loading || pending;

  React.useEffect(() => {
    if (open) {
      setValue(defaultValue);
      const id = window.setTimeout(() => inputRef.current?.focus(), 0);
      return () => window.clearTimeout(id);
    }
  }, [open, defaultValue]);

  const canSubmit = allowEmpty || value.trim().length > 0;

  const handleConfirm = async () => {
    if (busy || !canSubmit) return;
    setPending(true);
    try {
      await onConfirm(value);
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
          {description ? (
            <DialogDescription>{description}</DialogDescription>
          ) : null}
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="shared-prompt-input">{label}</Label>
          <Input
            ref={inputRef}
            id="shared-prompt-input"
            type={inputType}
            value={value}
            placeholder={placeholder}
            disabled={busy}
            autoComplete="off"
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void handleConfirm();
              }
            }}
          />
        </div>

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
            disabled={busy || !canSubmit}
            onClick={() => void handleConfirm()}
          >
            {busy ? t("loading") : (confirmLabel ?? t("confirm"))}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
