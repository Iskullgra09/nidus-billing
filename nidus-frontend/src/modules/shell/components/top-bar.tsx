"use client";

import * as React from "react";
import { Menu } from "lucide-react";
import { useTranslations } from "next-intl";

import { Link } from "@/core/i18n/routing";
import { LanguageSwitcher } from "@/core/i18n/components/language-switcher";
import { UserDropdown } from "@/modules/identity/components/user-dropdown";
import { OrgSwitcher } from "@/modules/organization/components/org-switcher";
import { persistLanguageAction } from "@/modules/identity/actions/user";
import { UserOrganizationSummary } from "@/modules/identity/types/auth";
import { UserProfileResponse } from "@/modules/identity/types/user";
import { Button } from "@/shared/ui/button";
import { useSidebar } from "../contexts/sidebar-context";
import { CommandPalette } from "./command-palette";

interface TopBarProps {
  user: UserProfileResponse;
  organizations: UserOrganizationSummary[];
}

export function TopBar({ user, organizations }: TopBarProps) {
  const t = useTranslations("ShellNav");
  const { toggleMobileOpen } = useSidebar();

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-card/90 shadow-sm backdrop-blur-xl supports-backdrop-filter:bg-card/80">
      <div className="flex h-14 items-center gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-8 md:hidden"
            onClick={toggleMobileOpen}
            aria-label={t("openMenu")}
          >
            <Menu className="size-4" />
          </Button>

          <Link
            href="/dashboard"
            className="text-primary text-lg font-semibold tracking-tight shrink-0 hover:opacity-80 transition-opacity"
          >
            NIDUS
          </Link>
          <span
            aria-hidden
            className="hidden h-4 w-px bg-border/80 sm:block shrink-0"
          />
          <OrgSwitcher
            organizations={organizations}
            currentOrganizationId={user.organization.id}
            fallbackName={user.organization.name}
          />
          <span className="hidden sm:inline-flex rounded-md bg-muted/60 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground shrink-0">
            {user.role_name}
          </span>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <CommandPalette />
          <LanguageSwitcher onLocaleChange={persistLanguageAction} />
          <UserDropdown user={user} />
        </div>
      </div>
    </header>
  );
}
