from enum import Enum


class TaxUseEnum(str, Enum):
    SALE = "sale"  # Venta
    PURCHASE = "purchase"  # Compra
    NONE = "none"  # Otros usos (en algunos Odoo)
