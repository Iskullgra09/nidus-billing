"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getLocale, getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import {
  CursorPage,
  Invoice,
  InvoiceListItem,
  InvoicePayload,
  InvoicePaymentPayload,
} from "../types/invoice";

const PATH = "/billing/invoices";
const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

export async function getInvoicesPage(params: {
  q?: string;
  cursor?: string | null;
  limit?: number;
  status?: string;
}): Promise<CursorPage<InvoiceListItem>> {
  const empty: CursorPage<InvoiceListItem> = {
    items: [],
    page_info: { has_next_page: false, end_cursor: null },
  };
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return empty;

    const response = await fetchClient<CursorPage<InvoiceListItem>>(
      "/billing/invoices",
      {
        headers: { Authorization: `Bearer ${session}` },
        params: {
          q: params.q || undefined,
          cursor: params.cursor || undefined,
          limit: params.limit ?? 10,
          status: params.status || undefined,
        },
      },
    );

    return response.status === "success" && response.data ? response.data : empty;
  } catch (error) {
    console.error("Fetch invoices error:", error);
    return empty;
  }
}

export async function getInvoiceAction(id: string): Promise<Invoice | null> {
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return null;
    const response = await fetchClient<Invoice>(`/billing/invoices/${id}`, {
      headers: { Authorization: `Bearer ${session}` },
    });
    return response.status === "success" && response.data ? response.data : null;
  } catch (error) {
    console.error("Fetch invoice error:", error);
    return null;
  }
}

export async function createInvoiceAction(
  payload: InvoicePayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Invoice>("/billing/invoices", {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
      body: JSON.stringify(payload),
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Create invoice error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function updateInvoiceAction(
  id: string,
  payload: Partial<InvoicePayload>,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Invoice>(`/billing/invoices/${id}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${session}` },
      body: JSON.stringify(payload),
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Update invoice error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function deleteInvoiceAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<null>(`/billing/invoices/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${session}` },
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Delete invoice error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function issueInvoiceAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Invoice>(`/billing/invoices/${id}/issue`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Issue invoice error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function voidInvoiceAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Invoice>(`/billing/invoices/${id}/void`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Void invoice error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function createInvoicePaymentAction(
  invoiceId: string,
  payload: InvoicePaymentPayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Invoice>(
      `/billing/invoices/${invoiceId}/payments`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${session}` },
        body: JSON.stringify(payload),
      },
    );

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Create invoice payment error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function downloadInvoicePdfAction(
  id: string,
): Promise<ActionResponse & { pdfBase64?: string }> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const locale = await getLocale();
    const response = await fetch(`${BASE_URL}/billing/invoices/${id}/pdf`, {
      headers: {
        Authorization: `Bearer ${session}`,
        "Accept-Language": locale,
      },
    });

    if (!response.ok) {
      return { status: "error", message: tCommon("unknownError") };
    }

    const buffer = Buffer.from(await response.arrayBuffer());
    return {
      status: "success",
      message: tCommon("success"),
      pdfBase64: buffer.toString("base64"),
    };
  } catch (error) {
    console.error("Download invoice PDF error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}
