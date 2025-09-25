from pydantic import Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime

from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


class InvoiceLineSchema(BaseSchema):
    # Opción A: por producto
    product_id: Optional[int] = Field(
        None, description="ID del producto en Odoo (opcional si usas name)"
    )
    # Opción B: por descripción
    name: Optional[str] = Field(
        None, description="Descripción de la línea (opcional si usas product_id)"
    )

    quantity: float = Field(1.0, description="Cantidad del producto")
    price_unit: float = Field(..., description="Precio unitario del producto")
    discount: Optional[float] = Field(
        None, description="Descuento por ítem (porcentaje)"
    )
    tax_ids: List[int] = Field(
        default_factory=list, description="Lista de IDs de impuestos aplicables"
    )

    # Normalizar strings vacíos a None
    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, v):
        return normalize_empty_string(v)

    # Validar que venga exactamente uno: product_id XOR name
    @model_validator(mode="after")
    def _ensure_one_of(self):
        has_pid = self.product_id is not None
        has_name = self.name is not None and self.name != ""
        if has_pid == has_name:
            # True==True (ambos) o False==False (ninguno) -> error
            raise ValueError(
                "Debes proporcionar exactamente uno: 'product_id' o 'name' (pero no ambos)."
            )
        return self

    def transform_payload(self, data: dict) -> dict:
        """
        Devuelve el dict listo para Odoo (para usar con (0, 0, payload)).
        - Si product_id está presente, usamos '/' como name (Odoo lo permite y rellenará la descripción).
        - Si usamos name (sin product_id), enviamos solo la descripción.
        """
        payload = {
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "discount": self.discount,
        }

        if self.product_id is not None:
            payload.update(
                {
                    "product_id": self.product_id,
                    "name": "/",  # Odoo requiere 'name'; con product_id se suele usar "/"
                }
            )
        else:
            # Modo sin product_id: enviar la descripción obligatoria
            payload.update(
                {
                    "name": self.name,
                }
            )

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

    # 💡 Normalización de strings vacíos a None
    @field_validator("ref", "payment_reference", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

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


class InvoiceCreateSchemaV18(BaseSchema):
    partner_id: int = Field(..., description="ID del proveedor en Odoo")
    ref: Optional[str] = Field(None, description="Número o referencia de la factura")
    payment_reference: Optional[str] = Field(
        None, description="Referencia de pago, puede ser igual a ref"
    )
    invoice_date: Optional[datetime] = Field(None, description="Fecha de la factura")
    date: Optional[datetime] = Field(None, description="Fecha contable")
    checked: bool = Field(
        False, description="Debe marcarse si la factura fue revisada."
    )
    lines: List[InvoiceLineSchema] = Field(..., description="Líneas de la factura")

    # 💡 Normalización de strings vacíos a None
    @field_validator("ref", "payment_reference", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

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
            "checked": self.checked,
            "invoice_line_ids": [(0, 0, line.as_odoo_payload()) for line in self.lines],
        }
