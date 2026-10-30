"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import {
  CursorPage,
  InboundCreatePayload,
  InboundDocument,
  InboundLinkPayload,
} from "../types/inbound";
import { InboundMailbox } from "../types/mailbox";

const PATH = "/billing/inbound";

export async function getInboundMailboxAction(): Promise<InboundMailbox | null> {
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return null;
    const response = await fetchClient<InboundMailbox>("/billing/inbound-mailbox", {
      headers: { Authorization: `Bearer ${session}` },
    });
    return response.status === "success" && response.data ? response.data : null;
  } catch (error) {
    console.error("Fetch inbound mailbox error:", error);
    return null;
  }
}

export async function updateInboundMailboxAction(
  enabled: boolean,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundMailbox>("/billing/inbound-mailbox", {
      method: "PUT",
      headers: { Authorization: `Bearer ${session}` },
      body: JSON.stringify({ enabled }),
    });
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Update inbound mailbox error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function getInboundDocumentsPage(params: {
  q?: string;
  cursor?: string | null;
  limit?: number;
  status?: string;
}): Promise<CursorPage<InboundDocument>> {
  const empty: CursorPage<InboundDocument> = {
    items: [],
    page_info: { has_next_page: false, end_cursor: null },
  };
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return empty;
    const response = await fetchClient<CursorPage<InboundDocument>>(
      "/billing/inbound-documents",
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
    console.error("Fetch inbound documents error:", error);
    return empty;
  }
}

export async function getInboundDocumentAction(
  id: string,
): Promise<InboundDocument | null> {
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return null;
    const response = await fetchClient<InboundDocument>(
      `/billing/inbound-documents/${id}`,
      { headers: { Authorization: `Bearer ${session}` } },
    );
    return response.status === "success" && response.data ? response.data : null;
  } catch (error) {
    console.error("Fetch inbound document error:", error);
    return null;
  }
}

export async function createInboundDocumentAction(
  payload: InboundCreatePayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundDocument>("/billing/inbound-documents", {
      method: "POST",
      headers: { Authorization: `Bearer ${session}` },
      body: JSON.stringify(payload),
    });
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Create inbound error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function linkInboundDocumentAction(
  id: string,
  payload: InboundLinkPayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundDocument>(
      `/billing/inbound-documents/${id}`,
      {
        method: "PATCH",
        headers: { Authorization: `Bearer ${session}` },
        body: JSON.stringify(payload),
      },
    );
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Link inbound error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function acceptInboundDocumentAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundDocument>(
      `/billing/inbound-documents/${id}/accept-hacienda`,
      { method: "POST", headers: { Authorization: `Bearer ${session}` } },
    );
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Accept inbound error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function rejectInboundDocumentAction(
  id: string,
  reason: string,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundDocument>(
      `/billing/inbound-documents/${id}/reject-hacienda`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${session}` },
        body: JSON.stringify({ reason }),
      },
    );
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Reject inbound error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function verifyInboundDocumentAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };
    const response = await fetchClient<InboundDocument>(
      `/billing/inbound-documents/${id}/verify-hacienda`,
      { method: "POST", headers: { Authorization: `Bearer ${session}` } },
    );
    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || tCommon("connectionError") };
  } catch (error) {
    console.error("Verify inbound error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}
