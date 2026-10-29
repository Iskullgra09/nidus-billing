import {
  Building2,
  Contact,
  FileInput,
  FileText,
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
        id: "invoices",
        href: "/billing/invoices",
        icon: FileText,
        scope: NidusScope.INVOICE_READ,
        keywords:
          "invoices facturas venta sales billing contado credito pdf emitir",
      },
      {
        id: "inbound",
        href: "/billing/inbound",
        icon: FileInput,
        scope: NidusScope.INBOUND_READ,
        keywords:
          "inbound compras purchase facturas compra bandeja hacienda proveedores accept reject",
      },
    ],
  },
  {
    id: "billing_masters",
    items: [
      {
        id: "customers",
        href: "/billing/customers",
        icon: Contact,
        scope: NidusScope.CUSTOMER_READ,
        keywords: "customers clientes billing maestros",
      },
      {
        id: "suppliers",
        href: "/billing/suppliers",
        icon: Truck,
        scope: NidusScope.SUPPLIER_READ,
        keywords: "suppliers proveedores billing maestros",
      },
      {
        id: "items",
        href: "/billing/items",
        icon: Package,
        scope: NidusScope.ITEM_READ,
        keywords: "items catalogo products services productos maestros",
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
        id: "fiscal",
        href: "/settings/organization/fiscal",
        icon: Building2,
        scope: NidusScope.FISCAL_WRITE,
        keywords: "fiscal hacienda cedula tributaria credentials",
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
