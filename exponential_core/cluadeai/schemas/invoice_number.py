from typing import Dict, List, Optional
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


class Metadata(BaseModel):
    evidence_snippet: str = Field(
        "", description="Exact text snippet where the invoice number was found"
    )
    pattern: Optional[str] = Field(
        None, description="Keyword or regex that triggered detection"
    )
    candidates: List[str] = Field(
        default_factory=list, description="Other possible invoice numbers"
    )
    confidence_factors: Dict[str, float] = Field(
        default_factory=dict, description="Breakdown of confidence"
    )

    @field_validator("evidence_snippet", mode="before")
    @classmethod
    def _trim_evidence(cls, v: Optional[str]) -> str:
        return (v or "").strip()

    # ❌ Antes tenías "pattern", "engine_version"
    # ✅ Deja solo "pattern", o vuelve a definir engine_version como Optional[str]
    @field_validator("pattern", mode="before")
    @classmethod
    def _trim_strs(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        sv = str(v).strip()
        return sv or None

    @field_validator("candidates")
    @classmethod
    def _clean_candidates(cls, v: List[str]) -> List[str]:
        seen = set()
        cleaned: List[str] = []
        for item in v or []:
            s = str(item).strip()
            if not s:
                continue
            if s not in seen:
                seen.add(s)
                cleaned.append(s)
        return cleaned

    @field_validator("confidence_factors")
    @classmethod
    def _validate_conf_factors(cls, v: Dict[str, float]) -> Dict[str, float]:
        out = {}
        for k, val in (v or {}).items():
            try:
                f = float(val)
            except Exception:
                continue
            if 0.0 <= f <= 1.0:
                out[str(k)] = f
        return out


class InvoiceNumberResponse(BaseModel):
    invoice_number: Optional[str] = Field(
        None,
        description="Extracted invoice number or null if not found",
        max_length=100,
    )
    has_invoice_number: bool = Field(
        ..., description="True if an invoice number was detected"
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1",
    )
    metadata: Optional[Metadata] = Field(default=None)

    @field_validator("invoice_number", mode="before")
    @classmethod
    def _normalize_invoice_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def _cross_field_rules(self) -> "InvoiceNumberResponse":
        # Si no hay número, fuerza invoice_number=None
        if self.has_invoice_number is False:
            object.__setattr__(self, "invoice_number", None)

        # Si dice que sí hay número, debe venir no vacío
        if self.has_invoice_number is True:
            if not self.invoice_number:
                raise ValueError(
                    "invoice_number must be non-empty when has_invoice_number=true"
                )
        return self
