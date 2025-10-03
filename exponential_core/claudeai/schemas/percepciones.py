from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ArTaxes(BaseModel):
    mentions_percepciones: bool = Field(
        ...,
        description="Boolean flag indicating if any 'Percepciones' were detected in the invoice",
    )
    percepcion_evidence: List[str] = Field(
        default_factory=list,
        description="List of evidence text snippets where perceptions were detected",
    )


class PercepcionAR(BaseModel):
    type: Literal["IIBB", "IVA", "UNKNOWN"] = Field(
        ..., description="Type of perception: Ingresos Brutos (IIBB), IVA, or UNKNOWN"
    )
    jurisdiction: str = Field(
        ..., description="Jurisdiction code or name, e.g., 'CABA', 'PBA', 'TUCUMAN'"
    )
    label_raw: str = Field(..., description="Raw label text as printed in the document")
    rate: Optional[float] = Field(
        None, description="Rate/percentage if available, otherwise null"
    )
    amount: float = Field(..., description="Perception amount as a decimal number")
    currency: Literal["ARS", "USD", "N/A"] = Field(
        ..., description="Currency of the perception amount"
    )
    evidence_snippet: str = Field(
        ..., description="Short text snippet showing where the perception was found"
    )


class PercepcionesResponse(BaseModel):
    ar_taxes: ArTaxes
    percepciones_ar: List[PercepcionAR] = Field(
        default_factory=list,
        description="List of all perceptions detected in the invoice",
    )
