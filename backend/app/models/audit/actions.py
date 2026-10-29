from enum import StrEnum


class AuditAction(StrEnum):
    """Canonical audit action codes. Pattern: resource.verb"""

    AUTH_LOGIN = "auth.login"
    AUTH_SELECT_ORG = "auth.select_org"
    AUTH_SWITCH_ORG = "auth.switch_org"

    ORG_CREATE = "organization.create"
    ORG_UPDATE = "organization.update"
    ORG_DELETE = "organization.delete"

    INVITATION_CREATE = "invitation.create"
    INVITATION_ACCEPT = "invitation.accept"
    INVITATION_REVOKE = "invitation.revoke"

    ROLE_CREATE = "role.create"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"

    MEMBER_ROLE_UPDATE = "member.role_update"
    MEMBER_REMOVE = "member.remove"

    CUSTOMER_CREATE = "customer.create"
    CUSTOMER_UPDATE = "customer.update"
    CUSTOMER_DELETE = "customer.delete"

    SUPPLIER_CREATE = "supplier.create"
    SUPPLIER_UPDATE = "supplier.update"
    SUPPLIER_DELETE = "supplier.delete"

    ITEM_CREATE = "item.create"
    ITEM_UPDATE = "item.update"
    ITEM_DELETE = "item.delete"

    INVOICE_CREATE = "invoice.create"
    INVOICE_UPDATE = "invoice.update"
    INVOICE_DELETE = "invoice.delete"
    INVOICE_ISSUE = "invoice.issue"
    INVOICE_VOID = "invoice.void"
    INVOICE_PAYMENT_CREATE = "invoice_payment.create"
    INVOICE_PAYMENT_DELETE = "invoice_payment.delete"
    INVOICE_EMAIL_SEND = "invoice_email.send"

    FISCAL_PROFILE_UPDATE = "fiscal_profile.update"
    HACIENDA_CREDENTIAL_UPDATE = "hacienda_credential.update"
    HACIENDA_CREDENTIAL_DELETE = "hacienda_credential.delete"


class AuditResourceType(StrEnum):
    ORGANIZATION = "organization"
    INVITATION = "invitation"
    ROLE = "role"
    MEMBER = "member"
    USER = "user"
    SESSION = "session"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    ITEM = "item"
    INVOICE = "invoice"
    INVOICE_PAYMENT = "invoice_payment"
    INVOICE_EMAIL = "invoice_email"
    FISCAL_PROFILE = "fiscal_profile"
    HACIENDA_CREDENTIAL = "hacienda_credential"
