from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class MoneySchema(BaseModel):
    raw: str = Field(..., description="Texto tal cual aparece (ej: '7.685,38')")
    value: Decimal = Field(
        ..., description="Valor numérico normalizado en punto decimal (ej: 7685.38)"
    )


class InvoiceTotalsSchema(BaseModel):
    currency: str = Field(..., description="Moneda detectada, p.ej. 'EUR'")
    subtotal: MoneySchema
    tax_amount: MoneySchema
    discount_amount: MoneySchema
    total: MoneySchema
    tax_rate_percent: Decimal = Field(
        ..., description="Porcentaje total de impuestos, p.ej. 21.0"
    )
    # NUEVO: Retenciones fiscales (IRPF, 'Retención Fiscal', etc.)
    withholding_amount: MoneySchema = Field(
        default_factory=lambda: MoneySchema(raw="0", value=Decimal("0.00")),
        description="Importe total de retenciones. Suele verse como negativo en el documento.",
    )
    withholding_rate_percent: Decimal = Field(
        default=Decimal("0.0"),
        description="Porcentaje de retención si aparece impreso (p.ej. 19.0).",
    )
    # Evidencias: recortes textuales que el modelo vio en el documento
    evidence: Dict[str, List[str]] = Field(
        ..., description="Evidencias por campo (ej: {'total': ['TOTAL 7.685,38 €']})"
    )
    notes: Optional[str] = None
