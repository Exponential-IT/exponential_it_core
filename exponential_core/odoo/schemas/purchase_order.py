from typing import List, Tuple
from pydantic import BaseModel, Field


class PurchaseOrderSchema(BaseModel):
    id: int = Field(..., description="ID interno de la orden de compra en Odoo")
    name: str = Field(..., description="Número o referencia de la orden de compra")
    state: str = Field(..., description="Estado de la orden de compra (ej: 'purchase')")
    partner_id: Tuple[int, str] = Field(
        ..., description="Tupla con el ID y nombre del proveedor asociado"
    )
    invoice_ids: List[int] = Field(
        default_factory=list, description="IDs de facturas relacionadas"
    )
    invoice_count: int = Field(..., description="Cantidad de facturas asociadas")
    invoice_status: str = Field(..., description="Estado de facturación de la orden")
    delivery_status: str = Field(..., description="Estado de entrega de la orden")


class PurchaseOrdersResponse(BaseModel):
    __root__: List[PurchaseOrderSchema]
