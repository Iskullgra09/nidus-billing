import * as React from "react";
import { getTranslations } from "next-intl/server";
import {
  createCustomerAction,
  deleteCustomerAction,
  getCustomersPage,
  updateCustomerAction,
} from "@/modules/billing/actions/customers";
import { PartiesTable } from "@/modules/billing/components/parties-table";
import { NidusScope } from "@/shared/access/scopes";

const PAGE_SIZE = 10;

type SearchParams = Promise<{
  q?: string;
  cursor?: string;
}>;

export default async function CustomersPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const t = await getTranslations("BillingCustomers");
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const cursor = params.cursor ?? null;

  const page = await getCustomersPage({ q, cursor, limit: PAGE_SIZE });

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">{t("title")}</h3>
        <p className="text-sm text-muted-foreground">{t("description")}</p>
      </div>

      <React.Suspense fallback={null}>
        <PartiesTable
          parties={page.items}
          pageInfo={page.page_info}
          searchQuery={q}
          pageSize={PAGE_SIZE}
          namespace="BillingCustomers"
          writeScope={NidusScope.CUSTOMER_WRITE}
          onCreate={createCustomerAction}
          onUpdate={updateCustomerAction}
          onDelete={deleteCustomerAction}
        />
      </React.Suspense>
    </div>
  );
}
