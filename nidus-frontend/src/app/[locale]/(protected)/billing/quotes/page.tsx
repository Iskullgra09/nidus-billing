import * as React from "react";
import { getTranslations } from "next-intl/server";
import { getCustomersPage } from "@/modules/billing/actions/customers";
import { getQuotesPage } from "@/modules/billing/actions/quotes";
import { QuotesTable } from "@/modules/billing/components/quotes-table";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function QuotesPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingQuotes");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const [page, customersPage] = await Promise.all([
    getQuotesPage({ q, cursor, limit: PAGE_SIZE }),
    getCustomersPage({ limit: 100 }),
  ]);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />

      <React.Suspense fallback={null}>
        <QuotesTable
          quotes={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
          customers={customersPage.items}
        />
      </React.Suspense>
    </div>
  );
}
