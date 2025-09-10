from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConfidenceFactorsSchema(BaseModel):
    keyword_match: Optional[float] = None
    ocr_quality: Optional[float] = None
    format_consistency: Optional[float] = None

    model_config = ConfigDict(extra="ignore")

    # Normaliza a float y valida rango [0, 1]
    @field_validator(
        "keyword_match", "ocr_quality", "format_consistency", mode="before"
    )
    @classmethod
    def _to_unit_float(cls, v):
        if v is None:
            return None
        f = float(v)
        if not (0.0 <= f <= 1.0):
            raise ValueError("Los factores de confianza deben estar en [0, 1].")
        return f


class MetadataSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evidence_snippet: str = Field(default="")
    pattern: Optional[str] = Field(default=None)
    candidates: List[str] = Field(default_factory=list)
    confidence_factors: Optional[ConfidenceFactorsSchema] = None

    @field_validator("evidence_snippet", mode="before")
    @classmethod
    def _trim_snippet(cls, v: Optional[str]) -> str:
        return (v or "").strip()

    @field_validator("candidates")
    @classmethod
    def _clean_candidates(cls, v: List[str]) -> List[str]:
        return [str(x).strip() for x in (v or []) if str(x).strip()]

    # Acepta dicts sueltos y los convierte al schema tipado
    @field_validator("confidence_factors", mode="before")
    @classmethod
    def _coerce_conf_factors(cls, v):
        if v is None or isinstance(v, ConfidenceFactorsSchema):
            return v
        if isinstance(v, dict):
            # Filtra a floats válidos y en rango [0,1]
            cleaned: Dict[str, float] = {}
            for k, val in v.items():
                try:
                    f = float(val)
                except Exception:
                    continue
                if f == f and 0.0 <= f <= 1.0:  # no NaN y dentro de rango
                    cleaned[str(k)] = f
            return ConfidenceFactorsSchema(**cleaned)
        return v


class InvoiceNumberResponseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Puede ser null cuando has_invoice_number = False
    invoice_number: Optional[str] = Field(default=None)
    has_invoice_number: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: MetadataSchema = Field(default_factory=MetadataSchema)

    @field_validator("invoice_number", mode="before")
    @classmethod
    def _strip_num(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def _consistency(self):
        """
        Reglas de consistencia:
        - Si has_invoice_number = True => invoice_number debe existir y no estar vacío.
        - Si has_invoice_number = False => invoice_number se normaliza a None.
        """
        if self.has_invoice_number:
            if not self.invoice_number:
                raise ValueError(
                    "has_invoice_number=True pero invoice_number es None o vacío."
                )
        else:
            object.__setattr__(self, "invoice_number", None)
        return self
