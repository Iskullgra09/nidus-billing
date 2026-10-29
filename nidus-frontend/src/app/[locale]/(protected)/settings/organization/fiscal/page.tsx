import * as React from "react";
import { getTranslations } from "next-intl/server";

import {
  getFiscalProfileAction,
  getHaciendaCredentialsAction,
} from "@/modules/billing/actions/fiscal";
import { FiscalSettingsForm } from "@/modules/billing/components/fiscal-settings-form";

export default async function FiscalSettingsPage() {
  const t = await getTranslations("SettingsFiscal");
  const [profile, credentials] = await Promise.all([
    getFiscalProfileAction(),
    getHaciendaCredentialsAction(),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{t("title")}</h2>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>
      <FiscalSettingsForm profile={profile} credentials={credentials} />
    </div>
  );
}
