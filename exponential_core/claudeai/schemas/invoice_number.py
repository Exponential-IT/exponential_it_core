from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MetadataSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evidence_snippet: str = Field(default="")
    pattern: Optional[str] = Field(default=None)
    candidates: List[str] = Field(default_factory=list)
    confidence_factors: Dict[str, float] = Field(default_factory=dict)

    @field_validator("evidence_snippet", mode="before")
    @classmethod
    def _trim_snippet(cls, v: Optional[str]) -> str:
        return (v or "").strip()

    @field_validator("candidates")
    @classmethod
    def _clean_candidates(cls, v: List[str]) -> List[str]:
        return [str(x).strip() for x in (v or []) if str(x).strip()]

    @field_validator("confidence_factors")
    @classmethod
    def _floats_only(cls, v: Dict[str, float]) -> Dict[str, float]:

        out: Dict[str, float] = {}
        for k, val in (v or {}).items():
            try:
                f = float(val)
            except Exception:
                continue
            if f == f:
                out[str(k)] = f
        return out


class InvoiceNumberResponseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    invoice_number: str = Field(..., min_length=1)
    has_invoice_number: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: MetadataSchema = Field(default_factory=MetadataSchema)

    @field_validator("invoice_number", mode="before")
    @classmethod
    def _strip_num(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("invoice_number cannot be empty")
        return s
