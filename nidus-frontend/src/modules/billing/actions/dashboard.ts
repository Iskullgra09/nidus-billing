"use server";

import { cookies } from "next/headers";
import { fetchClient } from "@/core/api/client";
import { DashboardSummary } from "../types/dashboard";

export async function getBillingDashboardSummary(): Promise<DashboardSummary | null> {
  try {
    const session = (await cookies()).get("nidus_session")?.value;
    if (!session) return null;
    const response = await fetchClient<DashboardSummary>(
      "/billing/dashboard-summary",
      {
        headers: { Authorization: `Bearer ${session}` },
      },
    );
    return response.status === "success" && response.data ? response.data : null;
  } catch (error) {
    console.error("Fetch billing dashboard summary error:", error);
    return null;
  }
}
