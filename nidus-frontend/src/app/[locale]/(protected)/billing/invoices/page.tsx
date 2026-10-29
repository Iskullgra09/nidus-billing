import * as React from "react";
import { getTranslations } from "next-intl/server";
import { getCustomersPage } from "@/modules/billing/actions/customers";
import { getInvoicesPage } from "@/modules/billing/actions/invoices";
import { InvoicesTable } from "@/modules/billing/components/invoices-table";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function InvoicesPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingInvoices");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const [page, customersPage] = await Promise.all([
    getInvoicesPage({ q, cursor, limit: PAGE_SIZE }),
    getCustomersPage({ limit: 100 }),
  ]);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />

      <React.Suspense fallback={null}>
        <InvoicesTable
          invoices={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
          customers={customersPage.items}
        />
      </React.Suspense>
    </div>
  );
}
