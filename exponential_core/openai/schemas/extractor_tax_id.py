from pydantic import BaseModel, Field


class PartnerTaxIdSchema(BaseModel):
    partner_name: str = Field(..., description="Nombre legal del proveedor/emisor")
    partner_tax_it: str = Field(
        ..., description="CIF/NIF/VAT del proveedor/emisor, normalizado sin espacios"
    )
