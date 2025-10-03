from enum import Enum


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
