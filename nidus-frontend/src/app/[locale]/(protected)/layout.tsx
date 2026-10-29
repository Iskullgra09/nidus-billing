import * as React from "react";
import { redirect } from "next/navigation";
import { getLocale } from "next-intl/server";
import { redirectTo } from "@/core/i18n/routing";
import {
  getCurrentUser,
  getUserOrganizations,
  hasSessionCookie,
} from "@/modules/identity/actions/auth";
import { AppShell } from "@/modules/shell/components/app-shell";
import { AuthProvider } from "@/modules/identity/contexts/auth-context";
import { UserPreferencesSync } from "@/modules/identity/components/user-preferences-sync";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const user = await getCurrentUser();

  if (!user) {
    if (await hasSessionCookie()) {
      redirect(`/api/auth/clear-session?locale=${locale}`);
    }
    redirectTo("/login", locale);
  }

  const organizations = await getUserOrganizations();

  return (
    <AuthProvider initialUser={user}>
      <UserPreferencesSync user={user} />
      <AppShell user={user} organizations={organizations}>
        {children}
      </AppShell>
    </AuthProvider>
  );
}
