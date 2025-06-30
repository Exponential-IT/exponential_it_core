from typing import Optional, Union
from pydantic import Field, EmailStr, HttpUrl, field_validator

from exponential_core.odoo.enums import CompanyTypeEnum
from exponential_core.odoo.schemas.base import BaseSchema
from exponential_core.odoo.schemas.normalizers import normalize_empty_string


class SupplierCreateSchema(BaseSchema):
    name: str = Field(..., description="Nombre del proveedor")
    vat: str = Field(..., description="Identificación fiscal (NIT, CIF, etc.)")
    email: Optional[EmailStr] = Field(None, description="Correo del proveedor")
    phone: Optional[str] = Field(None, description="Teléfono del proveedor")
    company_type: CompanyTypeEnum = Field(
        default=CompanyTypeEnum.COMPANY,
        description="Tipo de entidad: 'company' o 'person'",
    )
    is_company: bool = Field(
        True,
        description="Indica si el partner es una empresa (True) o una persona natural (False)",
    )
    street: Optional[str] = Field(None, description="Calle y número del proveedor")
    zip: Optional[str] = Field(None, description="Código postal")
    city: Optional[str] = Field(None, description="Ciudad o municipio")
    state_id: Optional[int] = Field(None, description="ID del estado/provincia en Odoo")
    country_id: Optional[int] = Field(None, description="ID del país en Odoo")
    website: Optional[Union[str, HttpUrl]] = Field(
        None, description="Sitio web del proveedor"
    )

    # 💡 Normaliza campos vacíos a None
    @field_validator(
        "email", "phone", "street", "zip", "city", "website", mode="before"
    )
    @classmethod
    def normalize_empty_fields(cls, v):
        return normalize_empty_string(v)

    def transform_payload(self, data: dict) -> dict:
        data["supplier_rank"] = 1
        data["company_type"] = self.company_type.value
        if "website" in data:
            data["website"] = data["website"].strip()
        return data
