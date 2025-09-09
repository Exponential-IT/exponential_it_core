from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from exponential_core.claudeai.enums.tax_ids import ContextLabel, TaxIdType


# ---------- Sub-modelos ----------
class AddressSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    street: str = "N/A"
    city: str = "N/A"
    state: str = "N/A"
    country_code: str = "N/A"
    postal_code: str = "N/A"

    @field_validator("country_code", mode="before")
    @classmethod
    def _upper_cc(cls, v: Optional[str]) -> str:
        if not v or not isinstance(v, str):
            return "N/A"
        v = v.strip().upper()
        return v or "N/A"


class ContactSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    phone: str = "N/A"
    fax: str = "N/A"
    email: str = "N/A"
    website: str = "N/A"


class PartySchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = "N/A"
    tax_id: str = "N/A"
    tax_id_type: TaxIdType = TaxIdType.UNKNOWN
    address: AddressSchema = Field(default_factory=AddressSchema)
    contact: ContactSchema = Field(default_factory=ContactSchema)
    raw_block: str = "N/A"
    evidence_snippets: List[str] = Field(default_factory=list)

    @field_validator("evidence_snippets")
    @classmethod
    def _limit_evidence(cls, v: List[str]) -> List[str]:
        # Máximo 3 evidencias por compacidad (ajústalo si quieres)
        return (v or [])[:3]


class InvoiceInfoSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_date: str = "N/A"
    invoice_number: str = "N/A"


class DetectedTaxIdSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: str
    tax_id_type: TaxIdType = TaxIdType.UNKNOWN
    is_valid_checksum: Optional[bool] = None
    context_label: ContextLabel = ContextLabel.UNKNOWN
    evidence_snippet: str = "N/A"


# ---------- Raíz ----------
class PartyExtractionSchema(BaseModel):
    """
    Raíz del resultado de identificación de CLIENT y SUPPLIER + metadatos de factura.
    """

    model_config = ConfigDict(extra="ignore")

    invoice: InvoiceInfoSchema
    client: PartySchema
    supplier: PartySchema
    detected_tax_ids: List[DetectedTaxIdSchema] = Field(default_factory=list)
