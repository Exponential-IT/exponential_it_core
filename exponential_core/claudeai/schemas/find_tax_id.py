# app/schemas/tax_match_response.py
from __future__ import annotations

from typing import Optional, Union, Annotated, Dict, Any, List
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator

from exponential_core.claudeai.enums.tax_ids import ErrorCode, GlobalStatus, TypeTaxUse


class TaxCandidateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    type_tax_use: Optional[TypeTaxUse] = None


class ResultPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    best_tax: TaxCandidateSchema
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    alternatives: List[TaxCandidateSchema] = Field(default_factory=list, max_length=3)


class ErrorPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")  # o "forbid" si quieres contrato estricto

    code: ErrorCode
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


# =========================
# Resultados por entrada (DISCRIMINATED UNION por "status")
#  ⚠️ En Pydantic v2 el discriminador debe ser Literal, NO Enum.
# =========================
class ResultEntryOk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"  # 👈 Literal requerido para el discriminador
    primary_amount: Optional[float] = Field(
        default=None,
        description="Ej.: 21.0; None cuando no hubo primary_tax (inferencia por semántica).",
    )
    result: ResultPayloadSchema
    error: None = None


class ResultEntryError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["error"] = "error"  # 👈 Literal requerido para el discriminador
    primary_amount: Optional[float] = Field(
        default=None,
        description="Ej.: 21.0; None cuando no hubo primary_tax (inferencia por semántica).",
    )
    result: None = None
    error: ErrorPayloadSchema


ResultEntry = Annotated[
    Union[ResultEntryOk, ResultEntryError],
    Field(discriminator="status"),
]


# =========================
# Meta
# =========================
class MetaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validated_unique_amounts: List[float] = Field(
        default_factory=list,
        description="Amounts únicos presentes en validated_tax_ids (informativo).",
    )
    notes: Optional[str] = None


# =========================
# Respuesta global (batch)
# =========================
class TaxIdBatchResponse(BaseModel):
    """
    'results' tiene una entrada por cada primary_amount (preservando orden y multiplicidad).
    'status' global: ok | partial_error | error (se ajusta automáticamente).
    """

    model_config = ConfigDict(extra="forbid")

    status: GlobalStatus
    results: List[ResultEntry]
    meta: MetaSchema = Field(default_factory=MetaSchema)

    @model_validator(mode="after")
    def _coerce_global_status(self) -> "TaxIdBatchResponse":
        if not self.results:
            object.__setattr__(self, "status", GlobalStatus.ERROR)
            return self

        oks = sum(1 for r in self.results if r.status == "ok")
        errs = sum(1 for r in self.results if r.status == "error")
