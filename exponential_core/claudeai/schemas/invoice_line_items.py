from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from exponential_core.claudeai.schemas.extractor_taxi_id import _to_decimal


class LineItemSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")  # ignora campos inesperados

    date: Optional[str] = Field(None, description="Fecha como aparece en el PDF")
    delivery_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit: Optional[str] = None
    unit_price: Decimal
    discount_percent: Optional[Decimal] = None
    line_total: Decimal
    notes: Optional[str] = None

    # Normalizar numéricos a Decimal
    @field_validator(
        "quantity", "unit_price", "discount_percent", "line_total", mode="before"
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class TotalsSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    taxable_base: Decimal
    vat_percent: Decimal
    vat_amount: Decimal
    grand_total: Decimal

    @field_validator(
        "taxable_base", "vat_percent", "vat_amount", "grand_total", mode="before"
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class InvoiceExtractionSchema(BaseModel):
    """
    Contenedor raíz del resultado de extracción de línea + totales.
    """

    model_config = ConfigDict(extra="ignore")

    items: List[LineItemSchema]
    totals: TotalsSchema
