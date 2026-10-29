"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getLocale, getTranslations } from "next-intl/server";
import { fetchClient } from "@/core/api/client";
import { ActionResponse } from "@/core/types/api";
import {
  FiscalProfile,
  FiscalProfilePayload,
  HaciendaCredentialStatus,
} from "../types/fiscal";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

async function sessionToken() {
  return (await cookies()).get("nidus_session")?.value;
}

export async function getFiscalProfileAction(): Promise<FiscalProfile | null> {
  try {
    const session = await sessionToken();
    if (!session) return null;
    const response = await fetchClient<FiscalProfile | null>(
      "/billing/fiscal-profile",
      { headers: { Authorization: `Bearer ${session}` } },
    );
    return response.status === "success" ? (response.data ?? null) : null;
  } catch {
    return null;
  }
}

export async function upsertFiscalProfileAction(
  payload: FiscalProfilePayload,
): Promise<ActionResponse> {
  const t = await getTranslations({
    locale: await getLocale(),
    namespace: "Common",
  });
  try {
    const session = await sessionToken();
    if (!session) return { status: "error", message: t("unknownError") };
    const response = await fetchClient<FiscalProfile>("/billing/fiscal-profile", {
      method: "PUT",
      headers: { Authorization: `Bearer ${session}` },
      body: JSON.stringify(payload),
    });
    if (response.status === "success") {
      revalidatePath("/settings/organization/fiscal");
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || t("unknownError") };
  } catch {
    return { status: "error", message: t("connectionError") };
  }
}

export async function getHaciendaCredentialsAction(): Promise<HaciendaCredentialStatus | null> {
  try {
    const session = await sessionToken();
    if (!session) return null;
    const response = await fetchClient<HaciendaCredentialStatus>(
      "/billing/hacienda-credentials",
      { headers: { Authorization: `Bearer ${session}` } },
    );
    return response.status === "success" ? response.data : null;
  } catch {
    return null;
  }
}

export async function upsertHaciendaCredentialsAction(
  formData: FormData,
): Promise<ActionResponse> {
  const t = await getTranslations({
    locale: await getLocale(),
    namespace: "Common",
  });
  try {
    const session = await sessionToken();
    if (!session) return { status: "error", message: t("unknownError") };

    const response = await fetch(`${BASE_URL}/billing/hacienda-credentials`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${session}` },
      body: formData,
    });
    const json = (await response.json()) as {
      status?: string;
      message?: string;
    };
    if (response.ok && json.status === "success") {
      revalidatePath("/settings/organization/fiscal");
      return { status: "success", message: json.message || t("success") };
    }
    return { status: "error", message: json.message || t("unknownError") };
  } catch {
    return { status: "error", message: t("connectionError") };
  }
}

export async function deleteHaciendaCredentialsAction(): Promise<ActionResponse> {
  const t = await getTranslations({
    locale: await getLocale(),
    namespace: "Common",
  });
  try {
    const session = await sessionToken();
    if (!session) return { status: "error", message: t("unknownError") };
    const response = await fetchClient<HaciendaCredentialStatus>(
      "/billing/hacienda-credentials",
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session}` },
      },
    );
    if (response.status === "success") {
      revalidatePath("/settings/organization/fiscal");
      return { status: "success", message: response.message };
    }
    return { status: "error", message: response.message || t("unknownError") };
  } catch {
    return { status: "error", message: t("connectionError") };
  }
}
