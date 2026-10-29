"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { KeyRound, LogOut, Search } from "lucide-react";

import { useRouter } from "@/core/i18n/routing";
import { cn } from "@/core/lib/utils";
import { useAuth } from "@/modules/identity/contexts/auth-context";
import { logoutAction } from "@/modules/identity/actions/auth";
import { hasScope } from "@/shared/access/permissions";
import { Button } from "@/shared/ui/button";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/shared/ui/command";
import {
  SHELL_NAV_GROUPS,
  SHELL_SIDEBAR_FOOTER_ITEMS,
} from "../nav/config";
import type { ShellNavItemId } from "../nav/types";

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();
  const { user } = useAuth();
  const t = useTranslations("CommandPalette");
  const tNav = useTranslations("ShellNav");

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const run = React.useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  const itemLabel = (id: ShellNavItemId) => tNav(`item.${id}`);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "group hidden h-9 w-56 items-center gap-2 rounded-lg border border-border/50 lg:w-64",
          "bg-muted/30 px-3 text-left text-sm text-muted-foreground",
          "shadow-none transition-colors sm:flex",
          "hover:border-border hover:bg-muted/50 hover:text-foreground/80",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        )}
      >
        <Search className="size-4 shrink-0 opacity-70" />
        <span className="flex-1 truncate">{t("trigger")}</span>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-0.5 rounded border border-border/60 bg-background/80 px-1.5 font-mono text-[10px] font-medium text-muted-foreground sm:inline-flex">
          ⌘K
        </kbd>
      </button>

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="sm:hidden"
        onClick={() => setOpen(true)}
        aria-label={t("trigger")}
      >
        <Search className="size-4" />
      </Button>

      <CommandDialog
        open={open}
        onOpenChange={setOpen}
        title={t("title")}
        description={t("description")}
      >
        <CommandInput placeholder={t("placeholder")} />
        <CommandList>
          <CommandEmpty>{t("empty")}</CommandEmpty>

          {SHELL_NAV_GROUPS.map((group) => {
            const visibleItems = group.items.filter(
              (item) => !item.scope || hasScope(user, item.scope),
            );
            if (visibleItems.length === 0) return null;

            return (
              <CommandGroup
                key={group.id}
                heading={tNav(`group.${group.id}`)}
              >
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const label = itemLabel(item.id);
                  return (
                    <CommandItem
                      key={item.id}
                      value={`${label} ${item.keywords} ${item.href}`}
                      onSelect={() => run(item.href)}
                    >
                      <Icon />
                      {label}
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            );
          })}

          <CommandGroup heading={t("groupPersonal")}>
            {SHELL_SIDEBAR_FOOTER_ITEMS.map((item) => {
              const Icon = item.icon;
              const label = itemLabel(item.id);
              return (
                <CommandItem
                  key={item.id}
                  value={`${label} ${item.keywords} ${item.href}`}
                  onSelect={() => run(item.href)}
                >
                  <Icon />
                  {label}
                </CommandItem>
              );
            })}
            <CommandItem
              value="security seguridad password /settings/security"
              onSelect={() => run("/settings/security")}
            >
              <KeyRound />
              {t("security")}
            </CommandItem>
          </CommandGroup>

          <CommandSeparator />
          <CommandGroup heading={t("groupAccount")}>
            <CommandItem
              value="logout cerrar sesion sign out"
              onSelect={() => {
                setOpen(false);
                void logoutAction();
              }}
            >
              <LogOut />
              {t("logout")}
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
}
