import * as React from "react";
import { getTranslations } from "next-intl/server";
import { getItemsPage } from "@/modules/billing/actions/items";
import { ItemsTable } from "@/modules/billing/components/items-table";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function ItemsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingItems");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const page = await getItemsPage({ q, cursor, limit: PAGE_SIZE });

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />

      <React.Suspense fallback={null}>
        <ItemsTable
          items={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
        />
      </React.Suspense>
    </div>
  );
}
