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
    FE = "fe"


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


class InvoiceCurrency(StrEnum):
    CRC = "CRC"
    USD = "USD"


class HaciendaDocumentType(StrEnum):
    FE = "01"
    ND = "02"
    NC = "03"
    TE = "04"


class HaciendaFiscalStatus(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"


class HaciendaTaxRateCode(StrEnum):
    EXENTO = "01"
    REDUCIDA_1 = "02"
    REDUCIDA_2 = "03"
    REDUCIDA_4 = "04"
    TRANSITORIO_0 = "05"
    TRANSITORIO_4 = "06"
    TRANSITORIO_8 = "07"
    GENERAL_13 = "08"


MH_IDENTIFICATION_CODES: dict[IdentificationType, str] = {
    IdentificationType.FISICA: "01",
    IdentificationType.JURIDICA: "02",
    IdentificationType.DIMEX: "03",
    IdentificationType.NITE: "04",
    IdentificationType.EXTRANJERO: "05",
}


def tax_rate_to_mh_code(rate: float | None) -> str:
    if rate is None:
        return HaciendaTaxRateCode.EXENTO.value
    rounded = round(float(rate), 2)
    mapping = {
        0.0: HaciendaTaxRateCode.EXENTO,
        1.0: HaciendaTaxRateCode.REDUCIDA_1,
        2.0: HaciendaTaxRateCode.REDUCIDA_2,
        4.0: HaciendaTaxRateCode.REDUCIDA_4,
        8.0: HaciendaTaxRateCode.TRANSITORIO_8,
        13.0: HaciendaTaxRateCode.GENERAL_13,
    }
    code = mapping.get(rounded)
    return (code or HaciendaTaxRateCode.GENERAL_13).value
