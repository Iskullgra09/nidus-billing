import { getTranslations } from "next-intl/server";
import {
  Activity,
  AlertTriangle,
  Building2,
  FileText,
  HeartPulse,
  Receipt,
  Users,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { getCurrentUser, getUserOrganizations } from "@/modules/identity/actions/auth";
import { getOrganizationMembersPage } from "@/modules/organization/actions/members";
import { getRecentAuditLogs } from "@/modules/access/actions/audit";
import { getBillingDashboardSummary } from "@/modules/billing/actions/dashboard";
import { formatMoney } from "@/modules/billing/lib/format";
import { hasScope } from "@/shared/access/permissions";
import { NidusScope } from "@/shared/access/scopes";
import { fetchClient } from "@/core/api/client";
import { Link } from "@/core/i18n/routing";

async function getSystemHealth(): Promise<"ok" | "down"> {
  try {
    const response = await fetchClient<{ status?: string }>("/health/");
    if (response.status === "success" && response.data?.status === "ok") {
      return "ok";
    }
    return "down";
  } catch {
    return "down";
  }
}

export default async function DashboardPage() {
  const t = await getTranslations("Dashboard");
  const user = await getCurrentUser();

  const canReadInvoices = hasScope(user, NidusScope.INVOICE_READ);
  const canReadAudit = hasScope(user, NidusScope.AUDIT_READ);

  const [membersPage, organizations, health, billingSummary] = await Promise.all([
    getOrganizationMembersPage({ limit: 100 }),
    getUserOrganizations(),
    getSystemHealth(),
    canReadInvoices ? getBillingDashboardSummary() : Promise.resolve(null),
  ]);

  const recentActivity = canReadAudit ? await getRecentAuditLogs(5) : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-muted-foreground">{t("description")}</p>
      </div>

      {canReadInvoices && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("openArCard")}
              </CardTitle>
              <Receipt className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {billingSummary ? (
                <>
                  <div className="text-2xl font-bold tabular-nums">
                    {formatMoney(billingSummary.open_ar, {
                      currency: billingSummary.open_ar_currency,
                      withCurrency: true,
                    })}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t("openArHint", {
                      count: billingSummary.open_invoice_count,
                    })}
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">{t("billingEmpty")}</p>
              )}
              <Link
                href="/billing/invoices"
                className="text-xs text-primary hover:underline mt-2 inline-block"
              >
                {t("viewInvoices")}
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("recentEmitsCard")}
              </CardTitle>
              <FileText className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {!billingSummary || billingSummary.recent_emits.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t("recentEmitsEmpty")}
                </p>
              ) : (
                <ul className="space-y-2">
                  {billingSummary.recent_emits.slice(0, 5).map((emit) => (
                    <li
                      key={`${emit.invoice_id}-${emit.updated_at}`}
                      className="flex items-center justify-between gap-2 text-sm"
                    >
                      <Link
                        href={`/billing/invoices/${emit.invoice_id}`}
                        className="truncate font-mono text-xs hover:underline"
                      >
                        {emit.clave?.slice(0, 16) ||
                          emit.invoice_id.slice(0, 8)}
                      </Link>
                      <Badge variant="secondary" className="shrink-0">
                        {emit.status}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
              <Link
                href="/billing/invoices"
                className="text-xs text-primary hover:underline mt-3 inline-block"
              >
                {t("viewInvoices")}
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {t("haciendaFailuresCard")}
              </CardTitle>
              <AlertTriangle className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {!billingSummary ? (
                <p className="text-sm text-muted-foreground">{t("billingEmpty")}</p>
              ) : billingSummary.hacienda_failure_count === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t("haciendaFailuresEmpty")}
                </p>
              ) : (
                <>
                  <div className="text-2xl font-bold text-destructive">
                    {billingSummary.hacienda_failure_count}
                  </div>
                  <ul className="mt-2 space-y-2">
                    {billingSummary.hacienda_failures.slice(0, 3).map((item) => (
                      <li
                        key={`${item.invoice_id}-${item.updated_at}`}
                        className="text-xs text-muted-foreground"
                      >
                        <Link
                          href={`/billing/invoices/${item.invoice_id}`}
                          className="font-medium text-foreground hover:underline"
                        >
                          {item.clave?.slice(0, 12) ||
                            item.invoice_id.slice(0, 8)}
                        </Link>
                        {item.message ? ` — ${item.message.slice(0, 60)}` : ""}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              <Link
                href="/billing/inbound"
                className="text-xs text-primary hover:underline mt-3 inline-block"
              >
                {t("viewInbound")}
              </Link>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t("membersCard")}
            </CardTitle>
            <Users className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{membersPage.items.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {membersPage.page_info.has_next_page
                ? t("membersCardHintMore")
                : t("membersCardHint")}
            </p>
            <Link
              href="/settings/organization/members"
              className="text-xs text-primary hover:underline mt-2 inline-block"
            >
              {t("manageMembers")}
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t("orgsCard")}
            </CardTitle>
            <Building2 className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{organizations.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {t("orgsCardHint")}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t("healthCard")}
            </CardTitle>
            <HeartPulse className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                health === "ok" ? "text-primary" : "text-destructive"
              }`}
            >
              {health === "ok" ? t("healthOk") : t("healthDown")}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t("healthCardHint")}
            </p>
          </CardContent>
        </Card>
      </div>

      {canReadAudit && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="size-4" />
                {t("activityTitle")}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {t("activityDescription")}
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {recentActivity.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("activityEmpty")}</p>
            ) : (
              <ul className="space-y-3">
                {recentActivity.map((event) => (
                  <li
                    key={event.id}
                    className="flex items-center justify-between gap-4 border-b border-border/50 pb-2 last:border-0 last:pb-0"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {event.action}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {event.resource_type
                          ? `${event.resource_type}${event.resource_id ? ` · ${event.resource_id.slice(0, 8)}` : ""}`
                          : t("activityNoResource")}
                      </p>
                    </div>
                    <time className="text-xs text-muted-foreground shrink-0 tabular-nums">
                      {new Date(event.created_at).toLocaleString()}
                    </time>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
