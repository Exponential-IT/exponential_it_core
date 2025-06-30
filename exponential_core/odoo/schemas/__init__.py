# exponential_core/odoo/schemas/__init__.py

from .invoice import InvoiceCreateSchema, InvoiceLineSchema
from .product import ProductCreateSchema
from .supplier import SupplierCreateSchema
from .partnet_address import AddressCreateSchema
from .taxes import ResponseTaxesSchema

__all__ = [
    "InvoiceCreateSchema",
    "InvoiceLineSchema",
    "ProductCreateSchema",
    "SupplierCreateSchema",
    "AddressCreateSchema",
    "ResponseTaxesSchema",
]
