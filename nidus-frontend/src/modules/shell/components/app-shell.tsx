"use client";

import * as React from "react";

import { UserOrganizationSummary } from "@/modules/identity/types/auth";
import { UserProfileResponse } from "@/modules/identity/types/user";
import { SidebarProvider } from "../contexts/sidebar-context";
import { AppSidebar } from "./app-sidebar";
import { TopBar } from "./top-bar";

interface AppShellProps {
  user: UserProfileResponse;
  organizations: UserOrganizationSummary[];
  children: React.ReactNode;
}

export function AppShell({ user, organizations, children }: AppShellProps) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen flex-col bg-background">
        <TopBar user={user} organizations={organizations} />
        <div className="flex min-h-0 flex-1">
          <AppSidebar />
          <main className="min-w-0 flex-1 bg-background p-6 lg:p-8">
            <div className="mx-auto max-w-6xl space-y-6">{children}</div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
