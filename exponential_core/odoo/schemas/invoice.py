from pydantic import Field
from typing import List, Optional
from datetime import datetime

from exponential_core.odoo.schemas.base import BaseSchema


class InvoiceLineSchema(BaseSchema):
    product_id: int = Field(..., description="ID del producto en Odoo")
    quantity: float = Field(1.0, description="Cantidad del producto")
    price_unit: float = Field(..., description="Precio unitario del producto")
    tax_ids: Optional[List[int]] = Field(
        default=[], description="Lista de IDs de impuestos aplicables"
    )

    def transform_payload(self, data: dict) -> dict:
        payload = {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "name": "/",
        }
        if self.tax_ids:
            payload["tax_ids"] = [(6, 0, self.tax_ids)]
        return payload


class InvoiceCreateSchema(BaseSchema):
    partner_id: int = Field(..., description="ID del proveedor en Odoo")
    ref: Optional[str] = Field(None, description="Número o referencia de la factura")
    payment_reference: Optional[str] = Field(
        None, description="Referencia de pago, puede ser igual a ref"
    )
    invoice_date: Optional[datetime] = Field(None, description="Fecha de la factura")
    date: Optional[datetime] = Field(None, description="Fecha contable")
    to_check: bool = Field(
        True, description="Debe marcarse si la factura necesita revisión"
    )
    lines: List[InvoiceLineSchema] = Field(..., description="Líneas de la factura")

    def transform_payload(self, data: dict) -> dict:
        return {
            "partner_id": self.partner_id,
            "move_type": "in_invoice",
            "ref": self.ref,
            "payment_reference": self.payment_reference or self.ref,
            "invoice_date": (
                self.invoice_date.isoformat() if self.invoice_date else None
            ),
            "date": self.date.isoformat() if self.date else None,
            "to_check": self.to_check,
            "invoice_line_ids": [(0, 0, line.as_odoo_payload()) for line in self.lines],
        }
