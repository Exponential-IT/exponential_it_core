from typing import Optional, Union, Literal
from enum import Enum
from pydantic import Field, EmailStr, HttpUrl, field_validator, ConfigDict

from exponential_core.odoo.enums import CompanyTypeEnum  # Enum con .COMPANY/.PERSON
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
    return s


def _normalize_website(v: Optional[str]) -> Optional[str]:
    s = _normalize_empty(v)
    if s is None:
        return None
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    return s


class SupplierCreateSchema(BaseSchema):
    # use_enum_values=True: al serializar (model_dump) usa los .value de los Enum
    model_config = ConfigDict(use_enum_values=True, extra="ignore")

    name: str = Field(..., description="Nombre del proveedor")
    vat: str = Field(..., description="Identificación fiscal (NIT, CIF, etc.)")
    email: Optional[EmailStr] = Field(None, description="Correo del proveedor")
    phone: Optional[str] = Field(None, description="Teléfono del proveedor")

    # Acepta Enum o str; lo normalizamos a "company"/"person"
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

    # ──────────────────────────────────────────────────────────────────────────────
    # Normalizadores de texto
    # ──────────────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────────
    # Normalizador robusto de company_type
    # ──────────────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────────
    # as_odoo_payload local: siempre JSON-safe (HttpUrl/Enum/Decimal/etc.)
    # ──────────────────────────────────────────────────────────────────────────────
    def as_odoo_payload(self) -> dict:
        # mode="json" convierte HttpUrl→str, Enum→str, Decimal→float, etc.
        data = self.model_dump(exclude_none=True, mode="json")
        return self.transform_payload(data)

    # ──────────────────────────────────────────────────────────────────────────────
    # Transformación final para Odoo
    # ──────────────────────────────────────────────────────────────────────────────
    def transform_payload(self, data: dict) -> dict:
        data["supplier_rank"] = 1

        # company_type ya normalizado como str; por seguridad, idempotente
        raw_ct = data.get("company_type", "company")
        data["company_type"] = getattr(raw_ct, "value", raw_ct) or "company"

        # website podría seguir siendo Url en caso extremo; fuerzalo a str si existe
        if "website" in data and data["website"] is not None:
            data["website"] = str(data["website"])

        # Limpieza final de strings simples
        for k in ("name", "vat", "street", "zip", "city", "phone"):
            if k in data and isinstance(data[k], str):
                data[k] = data[k].strip() or None

        return data
