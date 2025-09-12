# app/schemas/tax_match_response.py
from __future__ import annotations
from typing import Optional, List, Literal, Union, Annotated, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

TypeTaxUse = Literal["sale", "purchase"]
StatusOk = Literal["ok"]
StatusError = Literal["error"]
ErrorCode = Literal[
    "PRIMARY_TAX_NOT_AVAILABLE", "NO_CANDIDATE", "AMBIGUOUS", "INVALID_INPUT"
]


class TaxCandidateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Optional[int] = None
    name: Optional[str] = None
    amount: Optional[float] = None
    type_tax_use: Optional[TypeTaxUse] = None


class ResultPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    best_tax: TaxCandidateSchema
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    reason: str
    alternatives: Annotated[
        List[TaxCandidateSchema], Field(default_factory=list, max_length=3)
    ]


class ErrorPayloadSchema(BaseModel):
    model_config = ConfigDict(
        extra="ignore"
    )  # o "forbid" si quieres bloquear campos adicionales
    code: ErrorCode
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class TaxIdOkSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: StatusOk
    result: ResultPayloadSchema
    error: None = None


class TaxIdErrorSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: StatusError
    result: None = None
    error: ErrorPayloadSchema


# Unión discriminada por "status"
TaxIdExtractionResponse = Annotated[
    Union[TaxIdOkSchema, TaxIdErrorSchema], Field(discriminator="status")
]
