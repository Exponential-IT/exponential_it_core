from pydantic import BaseModel, Field

class InvoicePartiesSchema(BaseModel):
    partner_name: str = Field(..., description="Nombre legal del proveedor/emisor")
    partner_tax_it: str = Field(..., description="CIF/NIF/VAT del proveedor/emisor")
    client_name: str = Field(..., description="Nombre legal del cliente/receptor")
    client_tax_it: str = Field(..., description="CIF/NIF/VAT del cliente/receptor")
