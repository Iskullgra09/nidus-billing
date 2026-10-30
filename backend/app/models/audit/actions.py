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
    INVOICE_FISCAL_EMIT = "invoice_fiscal.emit"
    INVOICE_FISCAL_VERIFY = "invoice_fiscal.verify"
    INBOUND_CREATE = "inbound_fiscal.create"
    INBOUND_LINK = "inbound_fiscal.link"
    INBOUND_ACCEPT = "inbound_fiscal.accept"
    INBOUND_REJECT = "inbound_fiscal.reject"
    INBOUND_VERIFY = "inbound_fiscal.verify"
    INBOUND_MAILBOX_UPSERT = "inbound_mailbox.upsert"


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
    INVOICE_FISCAL = "invoice_fiscal"
    INBOUND_FISCAL = "inbound_fiscal_document"
    INBOUND_MAILBOX = "inbound_mailbox"
