from pydantic import Field
from exponential_core.odoo.enums.tax import TaxUseEnum
from exponential_core.odoo.schemas.base import BaseSchema


class ResponseTaxesSchema(BaseSchema):
    id: int = Field(..., description="ID único del impuesto en Odoo.")
    name: str = Field(
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
