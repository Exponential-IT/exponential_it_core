from typing import Optional, Union, Literal, Any
from enum import Enum
import re

from pydantic import (
    Field,
    EmailStr,
    HttpUrl,
    field_validator,
    ConfigDict,
    TypeAdapter,
)

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


_EMAIL_ADAPTER = TypeAdapter(EmailStr)
_EMAIL_REGEX = re.compile(r"[\w\.\+\-]+@[\w\.\-]+\.\w+")


def _validate_email_strict(s: str) -> Optional[str]:
    """
    Usa el validador real de Pydantic para EmailStr.
    Si es válido → devuelve el email como str.
    Si no → devuelve None.
    Nunca lanza excepción.
    """
    try:
        value = _EMAIL_ADAPTER.validate_python(s)
        return str(value)
    except Exception:
        return None


def _normalize_email(v: Any) -> Optional[str]:
    """
    Estrategia:
    - Si viene vacío / placeholder → None
    - Si viene EmailStr → str(email)
    - Si viene string:
        1. Intentar validar el string completo como email.
        2. Si falla, buscar el primer patrón tipo email dentro del texto.
        3. Si nada funciona → None.
    Nunca lanza excepción → los opcionales no rompen la validación.
    """
    if v is None:
        return None

    if isinstance(v, EmailStr):
        return str(v)

    s = _normalize_empty(v)
    if not s:
        return None

    strict = _validate_email_strict(s)
    if strict is not None:
        return strict

    match = _EMAIL_REGEX.search(s)
    if not match:
        return None

    candidate = match.group(0)
    return _validate_email_strict(candidate)


def _normalize_website(v: Optional[str]) -> Optional[str]:
    s = _normalize_empty(v)
    if s is None:
        return None
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s


class SupplierCreateSchema(BaseSchema):

    model_config = ConfigDict(use_enum_values=True, extra="ignore")

    name: str = Field(..., description="Nombre del proveedor")
    vat: str = Field(..., description="Identificación fiscal (NIT, CIF, etc.)")
    email: Optional[EmailStr] = Field(None, description="Correo del proveedor")
    phone: Optional[str] = Field(None, description="Teléfono del proveedor")

    company_type: Union[CompanyTypeEnum, Literal["company", "person"]] = Field(
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

    @field_validator("company_type", mode="before")
    @classmethod
    def _normalize_company_type(cls, v):
        if v is None:
            return "company"
        if isinstance(v, Enum):
            return v.value
        s = str(v).strip().lower()
        if s in {"company", "person", "individual"}:
            return "person" if s in {"person", "individual"} else "company"
        raise ValueError(
            f"company_type inválido: {v!r}. Valores permitidos: 'company' o 'person'."
        )

    def as_odoo_payload(self) -> dict:
        # mode="json" convierte HttpUrl→str, Enum→str, Decimal→float, etc.
        data = self.model_dump(exclude_none=True, mode="json")
        return self.transform_payload(data)

    def transform_payload(self, data: dict) -> dict:
        data["supplier_rank"] = 1

        raw_ct = data.get("company_type", "company")
        data["company_type"] = getattr(raw_ct, "value", raw_ct) or "company"

        if "website" in data and data["website"] is not None:
            data["website"] = str(data["website"])

        for k in ("name", "vat", "street", "zip", "city", "phone"):
            if k in data and isinstance(data[k], str):
                data[k] = data[k].strip() or None

        return data
