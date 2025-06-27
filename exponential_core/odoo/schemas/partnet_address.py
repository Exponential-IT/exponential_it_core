from pydantic import BaseModel, Field
from typing import Optional

from exponential_core.odoo.enums import AddressTypeEnum

from exponential_core.odoo.schemas.base import BaseSchema


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

    def transform_payload(self, data: dict) -> dict:
        data["name"] = data.pop("address_name")
        data["parent_id"] = data.pop("partner_id")
        data["type"] = self.address_type.value  # Accedemos a self aquí
        return data
