import * as React from "react";
import { getTranslations } from "next-intl/server";

import {
  getFiscalProfileAction,
  getHaciendaCredentialsAction,
} from "@/modules/billing/actions/fiscal";
import { FiscalSettingsForm } from "@/modules/billing/components/fiscal-settings-form";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

export default async function FiscalSettingsPage() {
  const t = await getTranslations("SettingsFiscal");
  const [profile, credentials] = await Promise.all([
    getFiscalProfileAction(),
    getHaciendaCredentialsAction(),
  ]);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />
      <FiscalSettingsForm profile={profile} credentials={credentials} />
    </div>
  );
}
