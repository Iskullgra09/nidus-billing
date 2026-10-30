import * as React from "react";
import { getTranslations } from "next-intl/server";
import { getSuppliersPage } from "@/modules/billing/actions/suppliers";
import {
  getInboundDocumentsPage,
  getInboundMailboxAction,
} from "@/modules/billing/actions/inbound";
import { InboundDocumentsTable } from "@/modules/billing/components/inbound-documents-table";
import { InboundMailboxCard } from "@/modules/billing/components/inbound-mailbox-card";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function InboundPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingInbound");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const [page, suppliersPage, mailbox] = await Promise.all([
    getInboundDocumentsPage({ q, cursor, limit: PAGE_SIZE }),
    getSuppliersPage({ limit: 100 }),
    getInboundMailboxAction(),
  ]);

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />

      <InboundMailboxCard mailbox={mailbox} />

      <React.Suspense fallback={null}>
        <InboundDocumentsTable
          documents={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
          suppliers={suppliersPage.items}
        />
      </React.Suspense>
    </div>
  );
}
