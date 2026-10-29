"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import { CursorPage, Party, PartyPayload } from "../types/party";

const PATH = "/billing/customers";

export async function getCustomersPage(params: {
  q?: string;
  cursor?: string | null;
  limit?: number;
}): Promise<CursorPage<Party>> {
  const empty: CursorPage<Party> = {
    items: [],
    page_info: { has_next_page: false, end_cursor: null },
  };
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return empty;

    const response = await fetchClient<CursorPage<Party>>("/billing/customers", {
      headers: { Authorization: `Bearer ${session}` },
      params: {
        q: params.q || undefined,
        cursor: params.cursor || undefined,
        limit: params.limit ?? 10,
      },
    });

    return response.status === "success" && response.data ? response.data : empty;
  } catch (error) {
    console.error("Fetch customers error:", error);
    return empty;
  }
}

export async function createCustomerAction(
  payload: PartyPayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Party>("/billing/customers", {
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
    console.error("Create customer error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function updateCustomerAction(
  id: string,
  payload: Partial<PartyPayload>,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<Party>(`/billing/customers/${id}`, {
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
    console.error("Update customer error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function deleteCustomerAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<null>(`/billing/customers/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${session}` },
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Delete customer error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}
