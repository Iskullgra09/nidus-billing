"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

import { Link, usePathname } from "@/core/i18n/routing";
import { cn } from "@/core/lib/utils";
import { useAuth } from "@/modules/identity/contexts/auth-context";
import { hasScope } from "@/shared/access/permissions";
import { Button } from "@/shared/ui/button";
import {
  SHELL_NAV_GROUPS,
  SHELL_SIDEBAR_FOOTER_ITEMS,
} from "../nav/config";
import type { ShellNavGroupId, ShellNavItem, ShellNavItemId } from "../nav/types";
import { useSidebar } from "../contexts/sidebar-context";

function isActivePath(pathname: string, href: string) {
  if (href === "/dashboard") return pathname.includes("/dashboard");
  if (href.startsWith("/settings")) return pathname.includes("/settings");
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({
  item,
  compact,
  label,
}: {
  item: ShellNavItem;
  compact: boolean;
  label: string;
}) {
  const pathname = usePathname();
  const { setMobileOpen } = useSidebar();
  const Icon = item.icon;
  const active = isActivePath(pathname, item.href);

  return (
    <Link
      href={item.href}
      title={compact ? label : undefined}
      onClick={() => setMobileOpen(false)}
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors",
        compact && "justify-center px-0",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
      )}
    >
      <Icon className="size-4 shrink-0" />
      {!compact && <span className="truncate">{label}</span>}
    </Link>
  );
}

function SidebarNav({ compact }: { compact: boolean }) {
  const t = useTranslations("ShellNav");
  const { user } = useAuth();
  const { toggleCollapsed, setMobileOpen, collapsed } = useSidebar();

  const groupLabel = (id: ShellNavGroupId) => t(`group.${id}`);
  const itemLabel = (id: ShellNavItemId) => t(`item.${id}`);

  const collapseControl = (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="hidden size-7 shrink-0 text-muted-foreground md:inline-flex"
      onClick={toggleCollapsed}
      aria-label={collapsed ? t("expand") : t("collapse")}
    >
      {collapsed ? (
        <ChevronRight className="size-4" />
      ) : (
        <ChevronLeft className="size-4" />
      )}
    </Button>
  );

  return (
    <div className="relative flex h-full flex-col">
      <div className="flex items-center justify-end px-2 pt-2 md:hidden">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={() => setMobileOpen(false)}
          aria-label={t("close")}
        >
          <X className="size-4" />
        </Button>
      </div>

      {compact && (
        <div className="hidden items-center justify-center px-2 pt-3 md:flex">
          {collapseControl}
        </div>
      )}

      <nav className="flex-1 space-y-6 overflow-y-auto px-2 py-3">
        {SHELL_NAV_GROUPS.map((group, groupIndex) => {
          const visibleItems = group.items.filter(
            (item) =>
              item.showInSidebar !== false &&
              (!item.scope || hasScope(user, item.scope)),
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.id} className="space-y-1">
              {!compact && (
                <div className="flex items-center gap-1 px-2 pb-1">
                  <p className="min-w-0 flex-1 text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/50">
                    {groupLabel(group.id)}
                  </p>
                  {groupIndex === 0 && collapseControl}
                </div>
              )}
              {visibleItems.map((item) => (
                <NavLink
                  key={item.id}
                  item={item}
                  compact={compact}
                  label={itemLabel(item.id)}
                />
              ))}
            </div>
          );
        })}
      </nav>

      <div className="mt-auto space-y-1 border-t border-border/40 px-2 py-3">
        {SHELL_SIDEBAR_FOOTER_ITEMS.map((item) => (
          <NavLink
            key={item.id}
            item={item}
            compact={compact}
            label={itemLabel(item.id)}
          />
        ))}
      </div>
    </div>
  );
}

export function AppSidebar() {
  const t = useTranslations("ShellNav");
  const pathname = usePathname();
  const { collapsed, mobileOpen, setMobileOpen } = useSidebar();

  React.useEffect(() => {
    setMobileOpen(false);
  }, [pathname, setMobileOpen]);

  return (
    <>
      <aside
        className={cn(
          "sticky top-14 hidden h-[calc(100vh-3.5rem)] shrink-0 border-r border-border/70 bg-sidebar/95 shadow-[1px_0_0_0_rgba(0,0,0,0.02)] backdrop-blur-xl md:block",
          "transition-[width] duration-200 ease-out",
          collapsed ? "w-16" : "w-60",
        )}
      >
        <SidebarNav compact={collapsed} />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 cursor-pointer bg-black/50"
            aria-label={t("close")}
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-border/70 bg-sidebar shadow-xl">
            <SidebarNav compact={false} />
          </aside>
        </div>
      )}
    </>
  );
}
