from __future__ import annotations


from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from exponential_core.claudeai.enums.tax_ids import CurrencyEnum
from exponential_core.claudeai.schemas.extractor_tax_id import _to_decimal


class LineItemSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: Optional[str] = Field(None, description="Fecha como aparece en el PDF")
    delivery_code: Optional[str] = None
    product_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit: Optional[str] = None
    unit_price: Decimal
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    net_price: Decimal
    line_total: Decimal
    measurements: Optional[str] = None
    color: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator(
        "quantity",
        "unit_price",
        "discount_percent",
        "discount_amount",
        "net_price",
        "line_total",
        "weight_kg",
        mode="before",
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class VATEntrySchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    percent: Decimal
    amount: Decimal

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class DiscountEntrySchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str
    percent: Optional[Decimal] = None
    amount: Decimal

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class WithholdingEntrySchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str
    percent: Optional[Decimal] = None
    amount: Decimal

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class TotalsSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subtotal: Optional[Decimal] = None
    taxable_base: Decimal
    vat_percent: Decimal
    vat_amount: Decimal
    vat_breakdown: List[VATEntrySchema] = Field(default_factory=list)

    discounts: Optional[Decimal] = None
    discounts_breakdown: List[DiscountEntrySchema] = Field(default_factory=list)

    withholding: Optional[Decimal] = None
    withholding_percent: Optional[Decimal] = None
    withholdings_breakdown: List[WithholdingEntrySchema] = Field(default_factory=list)

    other_taxes: Optional[Decimal] = None
    grand_total: Decimal

    @field_validator(
        "subtotal",
        "taxable_base",
        "vat_percent",
        "vat_amount",
        "discounts",
        "withholding",
        "withholding_percent",
        "other_taxes",
        "grand_total",
        mode="before",
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class SecondaryTotalSchema(BaseModel):
    """
    Total secundario cuando el PDF imprime un segundo total en otra moneda
    (p. ej., TOTAL U$S y TOTAL PESOS con tipo de cambio).
    """

    model_config = ConfigDict(extra="ignore")

    currency: CurrencyEnum
    amount: Decimal
    fx_rate: Optional[Decimal] = None  # tipo de cambio si está impreso

    @field_validator("amount", "fx_rate", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class InvoiceExtractionSchema(BaseModel):
    """
    Contenedor raíz del resultado de extracción de ítems + totales.
    Incluye moneda primaria (default EUR) y total secundario opcional.
    """

    model_config = ConfigDict(extra="ignore")

    currency: CurrencyEnum = CurrencyEnum.EUR
    secondary_total: Optional[SecondaryTotalSchema] = None

    items: List[LineItemSchema]
    totals: TotalsSchema
