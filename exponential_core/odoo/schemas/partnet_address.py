from pydantic import Field, field_validator
from typing import Optional

from exponential_core.odoo.enums import AddressTypeEnum
from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


class AddressCreateSchema(BaseSchema):
    partner_id: int = Field(
        ..., description="ID del partner principal (cliente o proveedor)"
    )
    address_name: str = Field(
        ..., description="Nombre de la dirección (ej. 'Bodega norte')"
    )
    street: str = Field(..., description="Calle y número")
    city: str = Field(..., description="Ciudad o municipio")
    address_type: AddressTypeEnum = Field(
        default=AddressTypeEnum.invoice,
        description=(
            "Tipo de dirección:\n"
            "- contact: Contacto (detalles de empleados)\n"
            "- invoice: Dirección de factura\n"
            "- delivery: Dirección de entrega\n"
            "- private: Dirección privada\n"
            "- other: Otra dirección (subsidiarias u otras)"
        ),
    )
    zip: Optional[str] = Field(None, description="Código postal")
    state_id: Optional[int] = Field(None, description="ID del estado o provincia")
    country_id: Optional[int] = Field(None, description="ID del país")
    phone: Optional[str] = Field(None, description="Teléfono fijo (si aplica)")

    # 💡 Normaliza campos vacíos a None
    @field_validator("zip", "phone", mode="before")
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    def transform_payload(self, data: dict) -> dict:
        data["name"] = data.pop("address_name")
        data["parent_id"] = data.pop("partner_id")
        data["type"] = self.address_type.value  # Accedemos a self aquí
        data.pop("address_type", None)
        return data
