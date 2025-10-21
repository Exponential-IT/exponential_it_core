from pydantic import Field, field_validator, model_validator
from typing import List, Optional
from datetime import date as dt_date

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
    analytic_distribution: Optional[int] = Field(None, description="Cuenta analítica")
    discount: Optional[float] = Field(
        None, description="Descuento por ítem (porcentaje)"
    )
    tax_ids: List[int] = Field(
        default_factory=list, description="Lista de IDs de impuestos aplicables"
    )

    # ---------- Normalizaciones ----------
    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, v):
        return normalize_empty_string(v)

    # ---------- Reglas de negocio ----------
    @field_validator("quantity", mode="after")
    @classmethod
    def _qty_pos(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("quantity debe ser > 0")
        return v

    @field_validator("price_unit", mode="after")
    @classmethod
    def _price_nonneg(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price_unit no puede ser negativo")
        return v

    @field_validator("discount", mode="after")
    @classmethod
    def _discount_range(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not (0.0 <= v <= 100.0):
            raise ValueError("discount debe estar entre 0 y 100")
        return v

    # ---------- XOR product_id vs name ----------
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

    # ---------- Payload ----------
    def as_odoo_payload(self) -> dict:
        """
        Devuelve el dict listo para Odoo (para usar con (0, 0, payload)).
        - Si product_id está presente, usamos '/' como name (Odoo lo permite y rellena la descripción).
        - Si usamos name (sin product_id), enviamos solo la descripción.
        """
        payload = {
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "discount": self.discount or 0.0,  # evita None en Odoo
        }

        if self.product_id is not None:
            payload.update(
                {
                    "product_id": self.product_id,
                    "name": "/",  # Requerido por Odoo cuando se pasa product_id
                }
            )
        else:
            # Modo sin product_id: enviar la descripción obligatoria
            payload.update({"name": self.name or "/"})

        if self.tax_ids:
            payload["tax_ids"] = [(6, 0, self.tax_ids)]

        if self.analytic_distribution is not None:
            # Odoo espera un mapping {analytic_account_id: porcentaje}
            payload["analytic_distribution"] = {self.analytic_distribution: 100.0}

        return payload

    def transform_payload(self, data: dict | None = None) -> dict:
        return self.as_odoo_payload()


class InvoiceCreateSchema(BaseSchema):
    partner_id: int = Field(..., description="ID del proveedor en Odoo")
    ref: Optional[str] = Field(None, description="Número o referencia de la factura")
    payment_reference: Optional[str] = Field(
        None, description="Referencia de pago, puede ser igual a ref"
    )

    # ✅ Fechas como 'date' (Odoo espera YYYY-MM-DD sin hora)
    invoice_date: Optional[dt_date] = Field(None, description="Fecha de la factura")
    invoice_date_due: Optional[dt_date] = Field(
        None, description="Fecha de pago/vencimiento de la factura"
    )
    date: Optional[dt_date] = Field(None, description="Fecha contable")
    to_check: bool = Field(
        True, description="Debe marcarse si la factura necesita revisión"
    )
    lines: List[InvoiceLineSchema] = Field(..., description="Líneas de la factura")

    # ---------- Normalización ----------
    @field_validator("ref", "payment_reference", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    # ---------- Reglas de negocio ----------
    @model_validator(mode="after")
    def _must_have_lines(self):
        if not self.lines:
            raise ValueError("Debe incluir al menos una línea de factura")
        return self

    def transform_payload(self) -> dict:
        return {
            "partner_id": self.partner_id,
            "move_type": "in_invoice",
            "ref": self.ref,
            "payment_reference": self.payment_reference or self.ref,
            "invoice_date": (
                self.invoice_date.isoformat() if self.invoice_date else None
            ),
            "invoice_date_due": (
                self.invoice_date_due.isoformat() if self.invoice_date_due else None
            ),
            "date": self.date.isoformat() if self.date else None,
            "to_check": self.to_check,
            "invoice_line_ids": [(0, 0, line.as_odoo_payload()) for line in self.lines],
        }
