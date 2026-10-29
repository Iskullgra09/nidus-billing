import * as React from "react";
import { getTranslations } from "next-intl/server";
import {
  createSupplierAction,
  deleteSupplierAction,
  getSuppliersPage,
  updateSupplierAction,
} from "@/modules/billing/actions/suppliers";
import { PartiesTable } from "@/modules/billing/components/parties-table";
import { NidusScope } from "@/shared/access/scopes";
import { SettingsPageHeader } from "@/shared/components/layout/settings-page-header";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function SuppliersPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingSuppliers");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const page = await getSuppliersPage({ q, cursor, limit: PAGE_SIZE });

  return (
    <div className="space-y-6">
      <SettingsPageHeader title={t("title")} description={t("description")} />

      <React.Suspense fallback={null}>
        <PartiesTable
          parties={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
          namespace="BillingSuppliers"
          writeScope={NidusScope.SUPPLIER_WRITE}
          onCreate={createSupplierAction}
          onUpdate={updateSupplierAction}
          onDelete={deleteSupplierAction}
        />
      </React.Suspense>
    </div>
  );
}
