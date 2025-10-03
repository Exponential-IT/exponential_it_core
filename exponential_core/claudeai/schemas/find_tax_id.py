# app/schemas/tax_match_response.py
from __future__ import annotations

from typing import Optional, Union, Annotated, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, model_validator

from exponential_core.claudeai.enums.tax_ids import (
    EntryStatus,
    ErrorCode,
    GlobalStatus,
    TypeTaxUse,
)


class TaxCandidateSchema(BaseModel):
    """
    Candidato de impuesto tal como viene de Odoo/tu catálogo validado.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    type_tax_use: Optional[TypeTaxUse] = None


class ResultPayloadSchema(BaseModel):
    """
    Payload cuando hay match (best_tax) para un primary_amount dado.
    """

    model_config = ConfigDict(extra="forbid")

    best_tax: TaxCandidateSchema
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    reason: str
    alternatives: Annotated[
        List[TaxCandidateSchema],
        Field(default_factory=list, max_length=3),
    ]


class ErrorPayloadSchema(BaseModel):
    """
    Detalle de error para un primary_amount (p.ej. no hubo candidato).
    """

    # Usa "ignore" si quieres permitir metadata flexible en details;
    # cambia a "forbid" si quieres contrato estricto.
    model_config = ConfigDict(extra="ignore")

    code: ErrorCode
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


# =========================
# Resultados por entrada (discriminated union)
# =========================
class ResultEntryOk(BaseModel):
    """
    Entrada OK para un primary_amount específico (o None si no hubo primary_tax).
    """

    model_config = ConfigDict(extra="forbid")

    status: EntryStatus = Field(default=EntryStatus.OK)
    primary_amount: Optional[float] = Field(
        default=None,
        description="Ej.: 21.0; None cuando no hubo primary_tax (inferencia por semántica).",
    )
    result: ResultPayloadSchema
    error: None = None


class ResultEntryError(BaseModel):
    """
    Entrada ERROR para un primary_amount que no encontró candidato válido.
    """

    model_config = ConfigDict(extra="forbid")

    status: EntryStatus = Field(default=EntryStatus.ERROR)
    primary_amount: Optional[float] = Field(
        default=None,
        description="Ej.: 21.0; None cuando no hubo primary_tax (inferencia por semántica).",
    )
    result: None = None
    error: ErrorPayloadSchema


# Unión discriminada por "status"
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
    Respuesta batch para la selección de impuestos:
      - 'results' contiene una entrada por cada valor en primary_tax (preservando orden y multiplicidad).
      - 'status' global se ajusta automáticamente:
          * 'ok'            → todas las entradas son ok
          * 'error'         → todas las entradas son error
          * 'partial_error' → mezcla de ok y error
    """

    model_config = ConfigDict(extra="forbid")

    status: GlobalStatus
    results: List[ResultEntry]
    meta: MetaSchema = Field(default_factory=MetaSchema)

    @model_validator(mode="after")
    def _coerce_global_status(self) -> "TaxIdBatchResponse":
        """
        Ajusta 'status' global según el contenido de 'results' para evitar inconsistencias.
        Elimínalo si prefieres fijar el estado global desde la capa de orquestación.
        """
        if not self.results:
            object.__setattr__(self, "status", GlobalStatus.ERROR)
            return self

        oks = sum(1 for r in self.results if r.status == EntryStatus.OK)
        errs = sum(1 for r in self.results if r.status == EntryStatus.ERROR)

        if oks > 0 and errs == 0:
            computed = GlobalStatus.OK
        elif errs > 0 and oks == 0:
            computed = GlobalStatus.ERROR
        else:
            computed = GlobalStatus.PARTIAL_ERROR

        if self.status != computed:
            object.__setattr__(self, "status", computed)
        return self
