from enum import Enum


class TypeTaxUse(str, Enum):
    SALE = "sale"
    PURCHASE = "purchase"


class EntryStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class GlobalStatus(str, Enum):
    OK = "ok"
    PARTIAL_ERROR = "partial_error"
    ERROR = "error"


class ErrorCode(str, Enum):
    PRIMARY_TAX_NOT_AVAILABLE = "PRIMARY_TAX_NOT_AVAILABLE"
    NO_CANDIDATE = "NO_CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID_INPUT = "INVALID_INPUT"


# Otros enums que ya tienes
class TaxIdType(str, Enum):
    NIF = "NIF"
    NIE = "NIE"
    CIF = "CIF"
    VAT = "VAT"
    CUIT = "CUIT"
    UNKNOWN = "UNKNOWN"


class ContextLabel(str, Enum):
    CLIENT = "Client"
    SUPPLIER = "Supplier"
    HEADER = "Header"
    FOOTER = "Footer"
    UNKNOWN = "Unknown"


class CurrencyEnum(str, Enum):
    EUR = "EUR"
    USD = "USD"
    ARS = "ARS"
