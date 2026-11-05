"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import { Invoice } from "../types/invoice";
import { CursorPage, Quote, QuoteListItem, QuotePayload } from "../types/quote";

const PATH = "/billing/quotes";
const INVOICES_PATH = "/billing/invoices";

export async function getQuotesPage(params: {
  q?: string;
  cursor?: string | null;
  limit?: number;
  status?: string;
}): Promise<CursorPage<QuoteListItem>> {
  const empty: CursorPage<QuoteListItem> = {
    items: [],
    page_info: { has_next_page: false, end_cursor: null },
  };
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return empty;
    const response = await fetchClient<CursorPage<QuoteListItem>>("/billing/quotes", {
      headers: { Authorization: `Bearer ${session}` },
      params: {
        q: params.q || undefined,
        cursor: params.cursor || undefined,
        limit: params.limit ?? 10,
        status: params.status || undefined,
      },
    });
    return response.status === "success" && response.data ? response.data : empty;
  } catch (error) {
    console.error("Fetch quotes error:", error);
    return empty;
  }
}

export async function getQuoteAction(id: string): Promise<Quote | null> {
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return null;
    const response = await fetchClient<Quote>(`/billing/quotes/${id}`, {
      headers: { Authorization: `Bearer ${session}` },
    });
    return response.status === "success" && response.data ? response.data : null;
  } catch (error) {
    console.error("Fetch quote error:", error);
    return null;
  }
}

export async function createQuoteAction(
  payload: QuotePayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<Quote>("/billing/quotes", {
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
    console.error("Create quote error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function updateQuoteAction(
  id: string,
  payload: Partial<QuotePayload>,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<Quote>(`/billing/quotes/${id}`, {
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
    console.error("Update quote error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function deleteQuoteAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient(`/billing/quotes/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${session}` },
    });
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Delete quote error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function markQuoteSentAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<Quote>(`/billing/quotes/${id}/mark-sent`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
    });
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Mark quote sent error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function convertQuoteAction(
  id: string,
): Promise<ActionResponse & { invoiceId?: string }> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<Invoice>(`/billing/quotes/${id}/convert`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
    });
    if (response.status === "success" && response.data) {
      revalidatePath(PATH);
      revalidatePath(INVOICES_PATH);
      return {
        status: "success",
        message: response.message || tCommon("success"),
        invoiceId: response.data.id,
      };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Convert quote error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}
