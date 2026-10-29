"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import { CatalogItem, ItemPayload } from "../types/item";
import { CursorPage } from "../types/party";

const PATH = "/billing/items";

export async function getItemsPage(params: {
  q?: string;
  cursor?: string | null;
  limit?: number;
}): Promise<CursorPage<CatalogItem>> {
  const empty: CursorPage<CatalogItem> = {
    items: [],
    page_info: { has_next_page: false, end_cursor: null },
  };
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return empty;

    const response = await fetchClient<CursorPage<CatalogItem>>("/billing/items", {
      headers: { Authorization: `Bearer ${session}` },
      params: {
        q: params.q || undefined,
        cursor: params.cursor || undefined,
        limit: params.limit ?? 10,
      },
    });

    return response.status === "success" && response.data ? response.data : empty;
  } catch (error) {
    console.error("Fetch items error:", error);
    return empty;
  }
}

export async function createItemAction(
  payload: ItemPayload,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<CatalogItem>("/billing/items", {
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
    console.error("Create item error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function updateItemAction(
  id: string,
  payload: Partial<ItemPayload>,
): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<CatalogItem>(`/billing/items/${id}`, {
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
    console.error("Update item error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}

export async function deleteItemAction(id: string): Promise<ActionResponse> {
  const tCommon = await getTranslations("Common");
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return { status: "error", message: tCommon("connectionError") };

    const response = await fetchClient<null>(`/billing/items/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${session}` },
    });

    if (response.status === "success") {
      revalidatePath(PATH);
      return { status: "success", message: response.message || tCommon("success") };
    }
    return { status: "error", message: response.message || tCommon("unknownError") };
  } catch (error) {
    console.error("Delete item error:", error);
    return { status: "error", message: tCommon("connectionError") };
  }
}
