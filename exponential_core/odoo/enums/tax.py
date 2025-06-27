from enum import Enum


class TaxUseEnum(str, Enum):
    sale = "sale"  # Venta
    purchase = "purchase"  # Compra
    none = "none"  # Otros usos (en algunos Odoo)
