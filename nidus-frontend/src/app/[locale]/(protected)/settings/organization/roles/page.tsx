import * as React from "react";
import { getTranslations } from "next-intl/server";
import {
  getAvailableRoles,
  getAssignableScopes,
} from "@/modules/access/actions/roles";
import { RolesTable } from "@/modules/access/components/roles-table";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

export default async function RolesPage() {
  const t = await getTranslations("SettingsRoles");
  const [roles, scopes] = await Promise.all([
    getAvailableRoles(),
    getAssignableScopes(),
  ]);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />
      <RolesTable roles={roles} scopes={scopes} />
    </div>
  );
}
