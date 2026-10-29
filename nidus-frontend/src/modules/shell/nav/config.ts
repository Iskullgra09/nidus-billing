import {
  Building2,
  Contact,
  LayoutDashboard,
  Package,
  ScrollText,
  Settings,
  Shield,
  Truck,
  Users,
} from "lucide-react";

import { NidusScope } from "@/shared/access/scopes";
import type { ShellNavGroup, ShellNavItem } from "./types";

export const SHELL_NAV_GROUPS: ShellNavGroup[] = [
  {
    id: "general",
    items: [
      {
        id: "dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        keywords: "dashboard control centro home inicio",
      },
    ],
  },
  {
    id: "billing",
    items: [
      {
        id: "customers",
        href: "/billing/customers",
        icon: Contact,
        scope: NidusScope.CUSTOMER_READ,
        keywords: "customers clientes billing",
      },
      {
        id: "suppliers",
        href: "/billing/suppliers",
        icon: Truck,
        scope: NidusScope.SUPPLIER_READ,
        keywords: "suppliers proveedores billing",
      },
      {
        id: "items",
        href: "/billing/items",
        icon: Package,
        scope: NidusScope.ITEM_READ,
        keywords: "items catalogo products services productos",
      },
    ],
  },
  {
    id: "workspace",
    items: [
      {
        id: "organization",
        href: "/settings/organization",
        icon: Building2,
        scope: NidusScope.ORG_UPDATE,
        keywords: "organization organizacion workspace settings",
        showInSidebar: false,
      },
      {
        id: "members",
        href: "/settings/organization/members",
        icon: Users,
        scope: NidusScope.MEMBER_READ,
        keywords: "members miembros team invite",
        showInSidebar: false,
      },
      {
        id: "roles",
        href: "/settings/organization/roles",
        icon: Shield,
        scope: NidusScope.ROLE_READ,
        keywords: "roles permisos permissions scopes",
        showInSidebar: false,
      },
      {
        id: "audit",
        href: "/settings/organization/audit",
        icon: ScrollText,
        scope: NidusScope.AUDIT_READ,
        keywords: "audit auditoria logs activity",
        showInSidebar: false,
      },
    ],
  },
];

export const SHELL_SIDEBAR_FOOTER_ITEMS: ShellNavItem[] = [
  {
    id: "settings",
    href: "/settings/profile",
    icon: Settings,
    keywords: "settings configuracion configuration profile perfil",
  },
];
