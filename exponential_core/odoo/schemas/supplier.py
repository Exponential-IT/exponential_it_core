from typing import Optional
from pydantic import Field, EmailStr, HttpUrl, field_validator, ConfigDict

from exponential_core.odoo.enums import CompanyTypeEnum
from exponential_core.odoo.schemas.base import BaseSchema


_PLACEHOLDERS_EMPTY = {
    "",
    " ",
    "-",
    "--",
    "n/a",
    "na",
    "n.a.",
    "s/n",
    "sin correo",
    "no aplica",
    "n/a.",
}


def _normalize_empty(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if s.lower() in _PLACEHOLDERS_EMPTY:
        return None
    return s


def _normalize_email(v: Optional[str]) -> Optional[str]:
    s = _normalize_empty(v)
    # si es None o vacío, se queda None y EmailStr no valida
    return s


def _normalize_website(v: Optional[str]) -> Optional[str]:
    s = _normalize_empty(v)
    if s is None:
        return None
    # Si no tiene esquema, agrega https:// para que HttpUrl valide
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s


class SupplierCreateSchema(BaseSchema):
    model_config = ConfigDict(use_enum_values=True)

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
    website: Optional[HttpUrl] = Field(None, description="Sitio web del proveedor")

    # Normaliza campos vacíos / placeholders → None
    @field_validator("phone", "street", "zip", "city", mode="before")
    @classmethod
    def _normalize_empty_fields(cls, v):
        return _normalize_empty(v)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email_field(cls, v):
        return _normalize_email(v)

    @field_validator("website", mode="before")
    @classmethod
    def _normalize_website_field(cls, v):
        return _normalize_website(v)

    def transform_payload(self, data: dict) -> dict:
        data["supplier_rank"] = 1
        data["company_type"] = self.company_type.value
        # Limpieza final de strings simples
        for k in ("name", "vat", "street", "zip", "city", "phone"):
            if k in data and isinstance(data[k], str):
                data[k] = data[k].strip() or None
        return data
