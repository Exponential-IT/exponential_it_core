from pydantic import Field, field_validator, model_validator
from typing import List, Optional, Union
from datetime import date as dt_date, datetime as dt_datetime

from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


# ---- helper: coerción de date ----
def _to_date_or_passthrough(
    v: Union[None, dt_date, dt_datetime, str],
) -> Optional[dt_date]:
    """
    - None -> None
    - date -> date
    - datetime -> .date()
    - str -> intenta parsear (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, YYYY/MM/DD)
    - otro tipo -> pásalo tal cual para que Pydantic emita su error estándar
    """
    if v is None:
        return None
    if isinstance(v, dt_date) and not isinstance(v, dt_datetime):
        return v
    if isinstance(v, dt_datetime):
        return v.date()
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        from datetime import datetime as _dt

        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return _dt.strptime(s, fmt).date()
            except ValueError:
                continue
        return v
    return v


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

    # @field_validator("price_unit", mode="after")
    # @classmethod
    # def _price_nonneg(cls, v: float) -> float:
    #     if v < 0:
    #         raise ValueError("price_unit no puede ser negativo")
    #     return v

    @field_validator("discount", mode="after")
    @classmethod
    def _discount_range(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if not (0.0 <= v <= 100.0):
            raise ValueError("discount debe estar entre 0 y 100")
        return v

    @field_validator("tax_ids", mode="after")
    @classmethod
    def _dedup_tax_ids(cls, v: List[int]) -> List[int]:
        # enteros, sin repetidos preservando orden
        return list(dict.fromkeys(int(x) for x in v if x is not None))

    # ---------- XOR product_id vs name ----------
    @model_validator(mode="after")
    def _ensure_one_of(self):
        has_pid = self.product_id is not None
        has_name = self.name is not None and self.name != ""
        if has_pid == has_name:
            raise ValueError(
                "Debes proporcionar exactamente uno: 'product_id' o 'name' (pero no ambos)."
            )
        return self

    # ---------- Payload ----------
    def transform_payload(self, data: dict | None = None) -> dict:
        """
        Implementación requerida por BaseSchema:
        construye el payload final para Odoo.
        """
        payload = {
            "quantity": self.quantity,
            "price_unit": self.price_unit,
            "discount": self.discount or 0.0,
        }

        if self.product_id is not None:
            payload.update({"product_id": self.product_id, "name": "/"})
        else:
            payload.update({"name": self.name or "/"})

        if self.tax_ids:
            payload["tax_ids"] = [(6, 0, self.tax_ids)]

        if self.analytic_distribution is not None:
            # Odoo espera un mapping {analytic_account_id: porcentaje}
            payload["analytic_distribution"] = {self.analytic_distribution: 100.0}

        return payload


class InvoiceCreateSchema(BaseSchema):
    partner_id: int = Field(..., description="ID del proveedor en Odoo")
    ref: Optional[str] = Field(None, description="Número o referencia de la factura")
    payment_reference: Optional[str] = Field(
        None, description="Referencia de pago, puede ser igual a ref"
    )

    # Fechas como 'date' (Odoo espera YYYY-MM-DD sin hora)
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

    # 👇 Coerción de fechas ANTES de que Pydantic intente castear a `date`
    @field_validator("invoice_date", "invoice_date_due", "date", mode="before")
    @classmethod
    def _coerce_dates(cls, v):
        return _to_date_or_passthrough(v)

    # ---------- Reglas de negocio ----------
    @model_validator(mode="after")
    def _must_have_lines(self):
        if not self.lines:
            raise ValueError("Debe incluir al menos una línea de factura")
        return self

    def transform_payload(self, data: dict | None = None) -> dict:
        """
        Construye el payload final para Odoo (move_type=in_invoice).
        """
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
