export enum NidusScope {
  SUPERADMIN = "*",
  ORG_READ = "org:read",
  ORG_UPDATE = "org:update",
  ORG_DELETE = "org:delete",
  MEMBER_READ = "identity:member:read",
  MEMBER_WRITE = "identity:member:write",
  MEMBER_INVITE = "identity:member:invite",
  ROLE_READ = "identity:role:read",
  ROLE_WRITE = "identity:role:write",
  AUDIT_READ = "audit:read",
  CUSTOMER_READ = "billing:customer:read",
  CUSTOMER_WRITE = "billing:customer:write",
  SUPPLIER_READ = "billing:supplier:read",
  SUPPLIER_WRITE = "billing:supplier:write",
  ITEM_READ = "billing:item:read",
  ITEM_WRITE = "billing:item:write",
  INVOICE_READ = "billing:invoice:read",
  INVOICE_WRITE = "billing:invoice:write",
  FISCAL_READ = "billing:fiscal:read",
  FISCAL_WRITE = "billing:fiscal:write",
  INBOUND_READ = "billing:inbound:read",
  INBOUND_WRITE = "billing:inbound:write",
}

/** Assignable scopes mirrored from backend NidusScope (excluding SUPERADMIN). */
export const ASSIGNABLE_SCOPES = Object.values(NidusScope).filter(
  (scope) => scope !== NidusScope.SUPERADMIN,
);
