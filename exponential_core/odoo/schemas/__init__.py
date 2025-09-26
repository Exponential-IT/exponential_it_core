# exponential_core/odoo/schemas/__init__.py

from .invoice import InvoiceCreateSchema, InvoiceLineSchema, InvoiceCreateSchemaV18
from .product import ProductCreateSchema, ProductCreateSchemaV18
from .supplier import SupplierCreateSchema
from .partnet_address import AddressCreateSchema
from .taxes import ResponseTaxesSchema
from .purchase_order import PurchaseOrderSchema, PurchaseOrdersResponse

__all__ = [
    "InvoiceCreateSchema",
    "InvoiceLineSchema",
    "InvoiceCreateSchemaV18",
    "ProductCreateSchema",
    "ProductCreateSchemaV18",
    "SupplierCreateSchema",
    "AddressCreateSchema",
    "ResponseTaxesSchema",
    "PurchaseOrderSchema",
    "PurchaseOrdersResponse",
]
