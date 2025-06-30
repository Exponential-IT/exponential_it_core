from typing import Optional
from pydantic import Field, field_validator
from exponential_core.odoo.enums.tax import TaxUseEnum
from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


class ResponseTaxesSchema(BaseSchema):
    id: int = Field(..., description="ID único del impuesto en Odoo.")
    name: Optional[str] = Field(
        ...,
        description="Nombre descriptivo del impuesto (por ejemplo, 'IVA 21% (Bienes)').",
    )
    amount: float = Field(
        ...,
        description="Porcentaje aplicado por el impuesto. Ejemplo: 21.0 para un 21%.",
    )
    type_tax_use: TaxUseEnum = Field(
        ...,
        description="Tipo de uso del impuesto: 'sale' (ventas), 'purchase' (compras) o 'none' (genérico).",
    )
    active: bool = Field(
        ...,
        description="Indica si el impuesto está activo (visible para usar) en Odoo.",
    )

    # 💡 Normaliza campos vacíos a None
    @field_validator(
        "name",
    )
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    def transform_payload(self, data: dict) -> dict:
        return data
