from pydantic import BaseModel, Field


class LinkExistingSchema(BaseModel):
    purchase_order_id: int = Field(..., description="ID de la OC (p.ej. 5302)")
    invoice_id: int = Field(
        ..., description="ID de la factura existente (account.move.id)"
    )
    force_fallback: bool = Field(
        True,
        description="Si no hay match, enlaza a la primera POL (Purchase order line) disponible",
    )
