import { getTranslations } from "next-intl/server";
import { getRecentAuditLogs } from "@/modules/access/actions/audit";
import { AuditLogsPanel } from "@/modules/access/components/audit-logs-panel";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

export default async function AuditSettingsPage() {
  const t = await getTranslations("SettingsAudit");
  const logs = await getRecentAuditLogs(50);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />
      <div className="overflow-hidden rounded-xl border border-border/80 bg-card p-4 shadow-md ring-1 ring-foreground/5">
        <AuditLogsPanel
          logs={logs}
          emptyLabel={t("empty")}
          noResourceLabel={t("noResource")}
        />
      </div>
    </div>
  );
}
