from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, field_validator


class CompanySchema(BaseModel):
    name: str
    address: str
    tax_id: str
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None


class CustomerSchema(BaseModel):
    name: str
    tax_number: str
    address: str


class GeneralInfoSchema(BaseModel):
    company: CompanySchema
    customer: CustomerSchema
    invoice_date: str
    invoice_number: str
    project: Optional[str] = None
    manager: Optional[str] = None
    delivery_note: Optional[str] = None
    order_number: Optional[str] = None
    notes: Optional[str] = None


def _to_decimal(value):
    """
    Coerce int/float/str -> Decimal safely.
    - Floats are wrapped via str() to avoid binary artifacts.
    - Strings like '7,50' are normalized to '7.50'.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        v = value.strip().replace(",", ".")
        return Decimal(v)
    return value


class ItemSchema(BaseModel):
    # Optional metadata
    date: Optional[str] = None
    delivery_code: Optional[str] = None
    product_code: Optional[str] = None

    description: str
    # CHANGED: quantity can be fractional (e.g., cubic meters), so use Decimal
    quantity: Decimal
    # CHANGED: unit can be missing => Optional[str]
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

    # Normalize numeric fields to Decimal
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
    def _normalize_decimals(cls, v):
        return _to_decimal(v)


class TotalsSchema(BaseModel):
    subtotal: Optional[Decimal] = None
    taxable_base: Decimal
    vat_percent: Decimal
    vat_amount: Decimal
    other_taxes: Optional[Decimal] = None
    grand_total: Decimal

    @field_validator(
        "subtotal",
        "taxable_base",
        "vat_percent",
        "vat_amount",
        "other_taxes",
        "grand_total",
        mode="before",
    )
    @classmethod
    def _normalize_decimals(cls, v):
        return _to_decimal(v)


class PaymentMethodSchema(BaseModel):
    method: str
    due_date: str
    iban: Optional[str] = None
    terms: Optional[str] = None


class InvoiceResponseSchema(BaseModel):
    # Estructura que esperamos de Claude
    general_info: GeneralInfoSchema
    items: List[ItemSchema]
    totals: TotalsSchema
    payment: PaymentMethodSchema
