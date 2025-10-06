from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exponential_core.claudeai.enums.tax_ids import CurrencyEnum
from exponential_core.claudeai.schemas.extractor_tax_id import _to_decimal


_DEC_Q = Decimal("0.01")
_TOL = Decimal("0.03")  # tolerancia para mismatch de IVA por línea


def _q2(x: Decimal) -> Decimal:
    # Redondeo financiero a 2 decimales
    return x.quantize(_DEC_Q, rounding=ROUND_HALF_UP)


class LineItemSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Campos básicos
    date: Optional[str] = Field(None, description="Fecha como aparece en el PDF")
    delivery_code: Optional[str] = None
    product_code: Optional[str] = None
    description: str

    # Cantidades y precios (neto = post-descuento, pre-IVA)
    quantity: Decimal
    unit: Optional[str] = None
    unit_price: Decimal
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    net_price: Decimal
    line_total: Decimal  # = base imponible por línea (post-desc., pre-IVA)

    # IVA por línea (OBLIGATORIO)
    vat_percent: Decimal = Field(..., description="0.0 si exento")
    vat_amount: Decimal = Field(..., description="Monto de IVA de la línea")

    # Extras opcionales
    vat_label: Optional[str] = Field(
        None, description='Etiqueta detectada (p.ej. "IVA 21%")'
    )
    tax_id: Optional[int] = Field(
        None, description="ID de impuesto interno si ya fue mapeado"
    )

    # Metadatos
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
        "vat_percent",
        "vat_amount",
        "weight_kg",
        mode="before",
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)

    @model_validator(mode="after")
    def _validate_vat(self):
        """
        - Calcula vat_amount si viene vacío.
        - Si hay desvío contra lo esperado (> _TOL), mantiene el valor provisto y anota en notes.
        """
        try:
            expected = _q2(self.line_total * (self.vat_percent / Decimal("100")))
        except Exception:
            # Si algo vino mal formateado, no bloqueamos validación.
            return self

        if self.vat_amount is None:
            object.__setattr__(self, "vat_amount", expected)
        else:
            diff = abs(self.vat_amount - expected)
            if diff > _TOL:
                # Respetamos el monto provisto (posible “impreso”), pero lo dejamos documentado.
                note = f"IVA línea difiere de esperado: provisto={self.vat_amount} esperado={expected} (Δ={_q2(diff)})."
                if self.notes:
                    object.__setattr__(self, "notes", f"{self.notes} | {note}")
                else:
                    object.__setattr__(self, "notes", note)
        return self


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

    @model_validator(mode="after")
    def _round_totals(self):
        # Redondeo consistente a 2 decimales en totales clave
        fields = [
            "subtotal",
            "taxable_base",
            "vat_percent",
            "vat_amount",
            "discounts",
            "withholding",
            "withholding_percent",
            "other_taxes",
            "grand_total",
        ]
        for f in fields:
            val = getattr(self, f, None)
            if isinstance(val, Decimal):
                object.__setattr__(self, f, _q2(val))
        # Redondeo en breakdowns
        vbd = []
        for v in self.vat_breakdown:
            v.percent = _q2(v.percent)
            v.amount = _q2(v.amount)
            vbd.append(v)
        object.__setattr__(self, "vat_breakdown", vbd)
        dbd = []
        for d in self.discounts_breakdown:
            if d.percent is not None:
                d.percent = _q2(d.percent)
            d.amount = _q2(d.amount)
            dbd.append(d)
        object.__setattr__(self, "discounts_breakdown", dbd)
        wbd = []
        for w in self.withholdings_breakdown:
            if w.percent is not None:
                w.percent = _q2(w.percent)
            w.amount = _q2(w.amount)
            wbd.append(w)
        object.__setattr__(self, "withholdings_breakdown", wbd)
        return self


class SecondaryTotalSchema(BaseModel):
    """
    Total secundario cuando el PDF imprime un segundo total en otra moneda
    (p. ej., TOTAL U$S y TOTAL PESOS con tipo de cambio).
    """

    model_config = ConfigDict(extra="ignore")

    currency: Optional[CurrencyEnum]
    amount: Optional[Decimal]
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
