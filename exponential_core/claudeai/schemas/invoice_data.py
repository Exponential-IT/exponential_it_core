from __future__ import annotations

from typing import List, Optional, Iterable
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from exponential_core.claudeai.enums.tax_ids import ContextLabel, TaxIdType


# ============================================================
# 🔧 Utilidades de normalización
# ============================================================


def _norm_na(v: Optional[str]) -> str:
    """Normaliza cadenas vacías/None a 'N/A'."""
    if v is None:
        return "N/A"
    s = str(v).strip()
    return s if s else "N/A"


def _dedup_keep_order(xs: Optional[Iterable[str]]) -> list[str]:
    """Elimina duplicados preservando el orden."""
    seen = set()
    out: list[str] = []
    for x in xs or []:
        x = (x or "").strip()
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out[:3]  # máximo 3


def _parse_to_dd_mm_yyyy_or_none_or_na(
    v: Optional[str], none_as_na: bool
) -> Optional[str] | str:
    """
    - Si v es None/""/"N/A"/"NULL": retorna None si none_as_na=False (para due_date),
      o "N/A" si none_as_na=True (para invoice_date).
    - Si es string con fecha válida, normaliza a DD-MM-YYYY.
    - Si no se puede parsear, retorna None (due_date) o "N/A" (invoice_date).
    """
    if v is None:
        return "N/A" if none_as_na else None
    s = str(v).strip()
    if not s or s.upper() in {"N/A", "NULL"}:
        return "N/A" if none_as_na else None

    candidates = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d %m %Y",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(s, fmt).date()
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            continue
    return "N/A" if none_as_na else None


# ============================================================
# 🏠 Submodelos
# ============================================================


class AddressSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    street: str = "N/A"
    city: str = "N/A"
    state: str = "N/A"
    country_code: str = "N/A"
    postal_code: str = "N/A"

    @field_validator("street", "city", "state", "postal_code", mode="before")
    @classmethod
    def _norm_text(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("country_code", mode="before")
    @classmethod
    def _upper_cc(cls, v: Optional[str]) -> str:
        s = _norm_na(v)
        return s.upper() if s != "N/A" else s


class ContactSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    phone: str = "N/A"
    fax: str = "N/A"
    email: str = "N/A"
    website: str = "N/A"

    @field_validator("phone", "fax", "website", mode="before")
    @classmethod
    def _norm_text(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("email", mode="before")
    @classmethod
    def _norm_email(cls, v: Optional[str]) -> str:
        s = _norm_na(v)
        return s.lower() if s != "N/A" else s


class PartySchema(BaseModel):
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    name: str = "N/A"
    tax_id: str = "N/A"
    tax_id_type: TaxIdType = TaxIdType.UNKNOWN
    address: AddressSchema = Field(default_factory=AddressSchema)
    contact: ContactSchema = Field(default_factory=ContactSchema)
    raw_block: str = "N/A"
    evidence_snippets: List[str] = Field(default_factory=list)

    @field_validator("name", mode="before")
    @classmethod
    def _norm_name(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("tax_id", mode="before")
    @classmethod
    def _norm_tax_id(cls, v: Optional[str]) -> str:
        s = _norm_na(v)
        return s.upper() if s != "N/A" else s

    @field_validator("raw_block", mode="before")
    @classmethod
    def _norm_raw_block(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("evidence_snippets", mode="before")
    @classmethod
    def _limit_evidence(cls, v: Optional[Iterable[str]]) -> List[str]:
        return _dedup_keep_order(v)


# ============================================================
# 📄 Metadatos de factura
# ============================================================


class InvoiceInfoSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    invoice_date: str = "N/A"  # DD-MM-YYYY o "N/A"
    invoice_number: str = "N/A"
    due_date: Optional[str] = None  # DD-MM-YYYY o None

    @field_validator("invoice_number", mode="before")
    @classmethod
    def _norm_invoice_number(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("invoice_date", mode="before")
    @classmethod
    def _norm_invoice_date(cls, v: Optional[str]) -> str:
        # Para invoice_date: si no hay fecha o no parsea -> "N/A"
        out = _parse_to_dd_mm_yyyy_or_none_or_na(v, none_as_na=True)
        return out  # siempre str

    @field_validator("due_date", mode="before")
    @classmethod
    def _norm_due_date(cls, v: Optional[str]) -> Optional[str]:
        # Para due_date: si no hay fecha o no parsea -> None
        out = _parse_to_dd_mm_yyyy_or_none_or_na(v, none_as_na=False)
        return out  # Optional[str]


# ============================================================
# 🧾 Tax IDs detectados
# ============================================================


class DetectedTaxIdSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    value: str
    tax_id_type: TaxIdType = TaxIdType.UNKNOWN
    is_valid_checksum: Optional[bool] = None
    context_label: ContextLabel = ContextLabel.UNKNOWN
    evidence_snippet: str = "N/A"

    @field_validator("value", mode="before")
    @classmethod
    def _norm_value(cls, v: Optional[str]) -> str:
        s = _norm_na(v)
        return s.upper() if s != "N/A" else s

    @field_validator("evidence_snippet", mode="before")
    @classmethod
    def _norm_snippet(cls, v: Optional[str]) -> str:
        return _norm_na(v)

    @field_validator("tax_id_type", mode="before")
    @classmethod
    def _enum_tax_id_type(cls, v):
        if v is None or isinstance(v, TaxIdType):
            return v
        try:
            return TaxIdType[str(v).strip().upper()]
        except KeyError:
            return v  # dejar que Pydantic valide/falle

    @field_validator("context_label", mode="before")
    @classmethod
    def _enum_context_label(cls, v):
        if v is None or isinstance(v, ContextLabel):
            return v
        try:
            return ContextLabel[str(v).strip().upper()]
        except KeyError:
            return v  # dejar que Pydantic valide/falle


# ============================================================
# ⚖️ Notas fiscales (Sujeto Pasivo)
# ============================================================


class TaxNotesSchema(BaseModel):
    """
    Bloque adicional del prompt:
    - Detecta si se menciona 'Sujeto Pasivo' (o variantes) y devuelve evidencia textual.
    """

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    mentions_sujeto_pasivo: bool = False
    sujeto_pasivo_variants_found: List[str] = Field(default_factory=list)
    sujeto_pasivo_evidence: List[str] = Field(default_factory=list)

    @field_validator(
        "sujeto_pasivo_variants_found", "sujeto_pasivo_evidence", mode="before"
    )
    @classmethod
    def _norm_lists(cls, v: Optional[Iterable[str]]) -> List[str]:
        return _dedup_keep_order(v)


# ============================================================
# 🌍 Raíz
# ============================================================


class PartyExtractionSchema(BaseModel):
    """Raíz del resultado de identificación de CLIENT y SUPPLIER + metadatos de factura."""

    model_config = ConfigDict(extra="ignore", use_enum_values=True)

    invoice: InvoiceInfoSchema
    client: PartySchema
    supplier: PartySchema
    tax_notes: TaxNotesSchema = Field(default_factory=TaxNotesSchema)
    detected_tax_ids: List[DetectedTaxIdSchema] = Field(default_factory=list)
