from enum import StrEnum


class PaymentCondition(StrEnum):
    CONTADO = "contado"
    CREDITO = "credito"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIAL = "partial"
    PAID = "paid"
    VOID = "void"


class DocumentSeriesType(StrEnum):
    INVOICE = "invoice"


class PaymentMethod(StrEnum):
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"
    OTHER = "other"


class InvoiceEmailStatus(StrEnum):
    SENT = "sent"
    FAILED = "failed"
    MOCKED = "mocked"


class IdentificationType(StrEnum):
    FISICA = "fisica"
    JURIDICA = "juridica"
    DIMEX = "dimex"
    NITE = "nite"
    EXTRANJERO = "extranjero"


class HaciendaEnvironment(StrEnum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"
