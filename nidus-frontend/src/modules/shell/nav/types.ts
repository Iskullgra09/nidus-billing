import type { LucideIcon } from "lucide-react";
import type { NidusScope } from "@/shared/access/scopes";

export type ShellNavGroupId =
  | "general"
  | "billing"
  | "billing_masters"
  | "workspace";

export type ShellNavItemId =
  | "dashboard"
  | "customers"
  | "suppliers"
  | "items"
  | "invoices"
  | "inbound"
  | "settings"
  | "organization"
  | "fiscal"
  | "members"
  | "roles"
  | "audit";

export interface ShellNavItem {
  id: ShellNavItemId;
  href: string;
  icon: LucideIcon;
  scope?: NidusScope;
  keywords: string;
  showInSidebar?: boolean;
}

export interface ShellNavGroup {
  id: ShellNavGroupId;
  items: ShellNavItem[];
}
