import * as React from "react";
import { getTranslations } from "next-intl/server";
import { SettingsSidebar } from "@/modules/identity/components/settings-sidebar";

export default async function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = await getTranslations("SettingsLayout");

  return (
    <div className="space-y-4 pb-16">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">{t("title")}</h2>
        <p className="text-muted-foreground">{t("description")}</p>
      </div>
      <div className="rounded-xl border border-border/70 bg-card p-4 shadow-sm lg:p-6">
        <div className="flex flex-col gap-8 lg:flex-row lg:gap-8">
          <aside className="w-full shrink-0 border-border/60 lg:w-56 lg:border-r lg:pr-6">
            <SettingsSidebar />
          </aside>
          <div className="min-w-0 flex-1">{children}</div>
        </div>
      </div>
    </div>
  );
}
