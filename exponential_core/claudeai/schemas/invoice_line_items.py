"""
Invoice Extraction Schema v2.0
Actualizado para el prompt mejorado con:
- taxable_base en vat_breakdown
- Validación de sum(items.line_total) ≈ taxable_base
- Soporte completo para valores negativos
- vat_breakdown nunca vacío
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from exponential_core.claudeai.enums.tax_ids import CurrencyEnum
from exponential_core.claudeai.schemas.extractor_tax_id import _to_decimal


_DEC_Q = Decimal("0.01")
_TOL = Decimal("0.03")
_TOL_TOTALS = Decimal("0.10")


def _q2(x: Decimal) -> Decimal:
    """Redondeo financiero a 2 decimales"""
    return x.quantize(_DEC_Q, rounding=ROUND_HALF_UP)


class LineItemSchema(BaseModel):
    """
    Representa un ítem/línea de factura.

    IMPORTANTE:
    - line_total es el importe ANTES de IVA (base imponible de la línea)
    - Los valores negativos se preservan (notas de crédito, devoluciones)
    - vat_percent y vat_amount son obligatorios (0.0 si exento)
    """

    model_config = ConfigDict(extra="ignore")

    # Campos básicos
    date: Optional[str] = Field(None, description="Fecha como aparece en el PDF")
    delivery_code: Optional[str] = None
    product_code: Optional[str] = None
    description: str

    # Cantidades y precios
    quantity: Decimal = Field(..., description="Puede ser negativo para devoluciones")
    unit: Optional[str] = None
    unit_price: Decimal = Field(..., description="Precio unitario (siempre positivo)")

    # Descuentos por línea
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None

    # Importes calculados
    net_price: Optional[Decimal] = Field(
        None, description="Precio neto por unidad post-descuento (opcional)"
    )
    line_total: Decimal = Field(
        ..., description="Base imponible de la línea (pre-IVA). Negativo para créditos."
    )

    # IVA por línea (OBLIGATORIO - nunca null)
    vat_percent: Decimal = Field(
        ..., description="Porcentaje de IVA. 0.0 si exento, NUNCA null"
    )
    vat_amount: Decimal = Field(
        ...,
        description="Monto de IVA de la línea. 0.0 si exento, NUNCA null. Negativo para créditos.",
    )

    # Etiquetas opcionales
    vat_label: Optional[str] = Field(
        None, description='Etiqueta detectada (p.ej. "IVA 21%")'
    )
    tax_id: Optional[int] = Field(
        None, description="ID de impuesto interno si ya fue mapeado"
    )

    # Metadatos opcionales
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
    def _validate_line_item(self):
        """
        Validaciones de línea:
        1. Calcula vat_amount si viene vacío
        2. Valida coherencia aritmética
        3. Preserva valores negativos
        """
        # Validar que vat_percent no sea None
        if self.vat_percent is None:
            object.__setattr__(self, "vat_percent", Decimal("0"))

        # Calcular vat_amount esperado
        try:
            # Usar abs() solo para el cálculo, preservar signo de line_total
            expected = _q2(self.line_total * (self.vat_percent / Decimal("100")))
        except Exception:
            return self

        if self.vat_amount is None:
            object.__setattr__(self, "vat_amount", expected)
        else:
            diff = abs(self.vat_amount - expected)
            if diff > _TOL:
                note = (
                    f"IVA línea difiere de esperado: provisto={self.vat_amount} "
                    f"esperado={expected} (Δ={_q2(diff)})."
                )
                if self.notes:
                    object.__setattr__(self, "notes", f"{self.notes} | {note}")
                else:
                    object.__setattr__(self, "notes", note)

        # Calcular net_price si no existe
        if self.net_price is None and self.quantity != 0:
            calculated_net = _q2(self.line_total / self.quantity)
            object.__setattr__(self, "net_price", calculated_net)

        return self


class VATEntrySchema(BaseModel):
    """
    Entrada de desglose de IVA.

    IMPORTANTE: Ahora incluye taxable_base obligatorio.
    Esto permite validar que sum(vat_breakdown.taxable_base) == totals.taxable_base
    """

    model_config = ConfigDict(extra="ignore")

    percent: Decimal = Field(..., description="Porcentaje de IVA (ej: 21.0)")
    taxable_base: Decimal = Field(
        ...,
        description="Base imponible para esta tasa. OBLIGATORIO. Puede ser negativo.",
    )
    amount: Decimal = Field(
        ..., description="Cuota de IVA para esta tasa. Puede ser negativo."
    )

    @field_validator("percent", "taxable_base", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)

    @model_validator(mode="after")
    def _validate_vat_entry(self):
        """Valida coherencia entre taxable_base, percent y amount"""
        try:
            expected_amount = _q2(self.taxable_base * (self.percent / Decimal("100")))
            diff = abs(self.amount - expected_amount)
            if diff > _TOL:
                # No fallamos, solo es informativo
                pass
        except Exception:
            pass
        return self


class DiscountEntrySchema(BaseModel):
    """Descuento - se RESTA antes de IVA"""

    model_config = ConfigDict(extra="ignore")

    label: str
    percent: Optional[Decimal] = None
    amount: Decimal = Field(..., description="Monto del descuento (positivo)")

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class WithholdingEntrySchema(BaseModel):
    """Retención - se RESTA después de IVA (IRPF, etc.)"""

    model_config = ConfigDict(extra="ignore")

    label: str
    percent: Optional[Decimal] = None
    amount: Decimal = Field(..., description="Monto de la retención (positivo)")

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class PerceptionEntrySchema(BaseModel):
    """
    Percepciones AR (IIBB, SIRCREB, ARBA, AGIP, etc.) — se SUMAN al total.

    IMPORTANTE: No confundir con retenciones.
    - Percepciones → SUMAN al total
    - Retenciones → RESTAN del total
    """

    model_config = ConfigDict(extra="ignore")

    label: str = Field(
        ..., description="Etiqueta (ej: 'IIBB CABA', 'Percepción ARBA', 'SIRCREB')"
    )
    percent: Optional[Decimal] = None
    amount: Decimal = Field(..., description="Monto de la percepción (positivo)")

    @field_validator("percent", "amount", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class TotalsSchema(BaseModel):
    """
    Totales de la factura.

    VALIDACIONES IMPORTANTES:
    1. vat_breakdown NUNCA puede estar vacío
    2. sum(vat_breakdown.taxable_base) debe ≈ taxable_base
    3. sum(vat_breakdown.amount) debe ≈ vat_amount
    4. grand_total = taxable_base + vat_amount + perceptions - discounts - withholding
    """

    model_config = ConfigDict(extra="ignore")

    subtotal: Optional[Decimal] = None
    taxable_base: Decimal = Field(
        ..., description="Base imponible total. Puede ser negativo."
    )
    vat_percent: Decimal = Field(..., description="Porcentaje de IVA promedio o único")
    vat_amount: Decimal = Field(..., description="Total IVA. Puede ser negativo.")

    vat_breakdown: List[VATEntrySchema] = Field(
        ...,  # Obligatorio, no puede ser default vacío
        description="Desglose por tipo de IVA. NUNCA vacío, mínimo 1 entrada.",
        min_length=1,  # Forzar al menos 1 elemento
    )

    discounts: Optional[Decimal] = None
    discounts_breakdown: List[DiscountEntrySchema] = Field(default_factory=list)

    withholding: Optional[Decimal] = None
    withholding_percent: Optional[Decimal] = None
    withholdings_breakdown: List[WithholdingEntrySchema] = Field(default_factory=list)

    # Percepciones (Argentina) → ADITIVAS
    perceptions: Optional[Decimal] = None
    perceptions_breakdown: List[PerceptionEntrySchema] = Field(default_factory=list)

    other_taxes: Optional[Decimal] = None
    grand_total: Decimal = Field(..., description="Total factura. Puede ser negativo.")

    # Campo para notas de validación
    notes: Optional[str] = Field(
        None, description="Notas sobre discrepancias o ajustes detectados"
    )

    @field_validator(
        "subtotal",
        "taxable_base",
        "vat_percent",
        "vat_amount",
        "discounts",
        "withholding",
        "withholding_percent",
        "perceptions",
        "other_taxes",
        "grand_total",
        mode="before",
    )
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)

    @model_validator(mode="after")
    def _validate_and_round_totals(self):
        """
        Validaciones y redondeo de totales:
        1. Redondeo consistente a 2 decimales
        2. Validar vat_breakdown no vacío
        3. Validar sum(vat_breakdown.taxable_base) ≈ taxable_base
        4. Validar sum(vat_breakdown.amount) ≈ vat_amount
        """
        validation_notes = []

        # --- Redondeo de campos escalares ---
        scalar_fields = [
            "subtotal",
            "taxable_base",
            "vat_percent",
            "vat_amount",
            "discounts",
            "withholding",
            "withholding_percent",
            "perceptions",
            "other_taxes",
            "grand_total",
        ]
        for f in scalar_fields:
            val = getattr(self, f, None)
            if isinstance(val, Decimal):
                object.__setattr__(self, f, _q2(val))

        # --- Redondeo en vat_breakdown ---
        vbd = []
        for v in self.vat_breakdown:
            v.percent = _q2(v.percent)
            v.taxable_base = _q2(v.taxable_base)
            v.amount = _q2(v.amount)
            vbd.append(v)
        object.__setattr__(self, "vat_breakdown", vbd)

        # --- Validar vat_breakdown no vacío ---
        if not self.vat_breakdown:
            validation_notes.append(
                "ADVERTENCIA: vat_breakdown está vacío, debería tener al menos 1 entrada"
            )

        # --- Validar sum(vat_breakdown.taxable_base) ≈ taxable_base ---
        if self.vat_breakdown:
            sum_vb_taxable = sum(v.taxable_base for v in self.vat_breakdown)
            diff_taxable = abs(sum_vb_taxable - self.taxable_base)
            if diff_taxable > _TOL_TOTALS:
                validation_notes.append(
                    f"sum(vat_breakdown.taxable_base)={sum_vb_taxable} ≠ taxable_base={self.taxable_base} "
                    f"(Δ={_q2(diff_taxable)})"
                )

        # --- Validar sum(vat_breakdown.amount) ≈ vat_amount ---
        if self.vat_breakdown:
            sum_vb_amount = sum(v.amount for v in self.vat_breakdown)
            diff_vat = abs(sum_vb_amount - self.vat_amount)
            if diff_vat > _TOL_TOTALS:
                validation_notes.append(
                    f"sum(vat_breakdown.amount)={sum_vb_amount} ≠ vat_amount={self.vat_amount} "
                    f"(Δ={_q2(diff_vat)})"
                )

        # --- Validar fórmula de grand_total ---
        try:
            expected_grand = (
                self.taxable_base
                + self.vat_amount
                + (self.perceptions or Decimal("0"))
                + (self.other_taxes or Decimal("0"))
                - (self.discounts or Decimal("0"))
                - (self.withholding or Decimal("0"))
            )
            diff_grand = abs(self.grand_total - expected_grand)
            if diff_grand > _TOL_TOTALS:
                validation_notes.append(
                    f"grand_total={self.grand_total} ≠ calculado={_q2(expected_grand)} "
                    f"(Δ={_q2(diff_grand)})"
                )
        except Exception:
            pass

        # --- Redondeo en otros breakdowns ---
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

        pbd = []
        for p in self.perceptions_breakdown:
            if p.percent is not None:
                p.percent = _q2(p.percent)
            p.amount = _q2(p.amount)
            pbd.append(p)
        object.__setattr__(self, "perceptions_breakdown", pbd)

        # --- Guardar notas de validación ---
        if validation_notes:
            combined_notes = " | ".join(validation_notes)
            if self.notes:
                object.__setattr__(self, "notes", f"{self.notes} | {combined_notes}")
            else:
                object.__setattr__(self, "notes", combined_notes)

        return self


class SecondaryTotalSchema(BaseModel):
    """
    Total secundario cuando el PDF imprime un segundo total en otra moneda
    (p. ej., TOTAL U$S y TOTAL PESOS con tipo de cambio).
    """

    model_config = ConfigDict(extra="ignore")

    currency: Optional[CurrencyEnum] = None
    amount: Optional[Decimal] = None
    fx_rate: Optional[Decimal] = Field(
        None, description="Tipo de cambio si está impreso en el documento"
    )

    @field_validator("amount", "fx_rate", mode="before")
    @classmethod
    def _decimals(cls, v):
        return _to_decimal(v)


class InvoiceExtractionSchema(BaseModel):
    """
    Contenedor raíz del resultado de extracción de ítems + totales.

    VALIDACIONES A NIVEL DE DOCUMENTO:
    1. sum(items.line_total) debe ≈ totals.taxable_base
    2. sum(items.vat_amount) debe ≈ totals.vat_amount
    3. Valores negativos se preservan para notas de crédito
    """

    model_config = ConfigDict(extra="ignore")

    currency: CurrencyEnum = CurrencyEnum.EUR
    secondary_total: Optional[SecondaryTotalSchema] = None

    items: List[LineItemSchema] = Field(
        ...,
        description="Lista de ítems. Puede estar vacía solo si es factura sin detalle.",
        min_length=0,
    )
    totals: TotalsSchema

    @model_validator(mode="after")
    def _validate_document_totals(self):
        """
        Validación a nivel de documento:
        - sum(items.line_total) ≈ totals.taxable_base
        - sum(items.vat_amount) ≈ totals.vat_amount
        """
        if not self.items:
            return self

        validation_notes = []

        # Suma de line_totals de items
        sum_line_totals = sum(item.line_total for item in self.items)
        diff_taxable = abs(sum_line_totals - self.totals.taxable_base)

        if diff_taxable > _TOL_TOTALS:
            validation_notes.append(
                f"sum(items.line_total)={_q2(sum_line_totals)} ≠ "
                f"taxable_base={self.totals.taxable_base} (Δ={_q2(diff_taxable)})"
            )

        # Suma de vat_amounts de items
        sum_vat_amounts = sum(item.vat_amount for item in self.items)
        diff_vat = abs(sum_vat_amounts - self.totals.vat_amount)

        if diff_vat > _TOL_TOTALS:
            validation_notes.append(
                f"sum(items.vat_amount)={_q2(sum_vat_amounts)} ≠ "
                f"vat_amount={self.totals.vat_amount} (Δ={_q2(diff_vat)})"
            )

        # Agregar notas de validación al totals
        if validation_notes:
            combined_notes = " | ".join(validation_notes)
            current_notes = self.totals.notes or ""
            if current_notes:
                new_notes = f"{current_notes} | {combined_notes}"
            else:
                new_notes = combined_notes

            # Crear nuevo TotalsSchema con las notas actualizadas
            totals_dict = self.totals.model_dump()
            totals_dict["notes"] = new_notes
            object.__setattr__(self, "totals", TotalsSchema(**totals_dict))

        return self
