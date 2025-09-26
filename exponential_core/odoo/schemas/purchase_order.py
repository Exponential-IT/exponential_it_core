# exponential_core/odoo/schemas/purchase_order.py
from typing import List, Tuple
from pydantic import BaseModel, Field, RootModel


class PurchaseOrderSchema(BaseModel):
    id: int = Field(..., description="ID interno de la orden en Odoo")
    name: str = Field(..., description="Referencia de la orden (p. ej. 'PO 02-00032')")
    state: str = Field(..., description="Estado de la orden")
    partner_id: Tuple[int, str] = Field(..., description="(partner_id, partner_name)")
    invoice_ids: List[int] = Field(default_factory=list)
    invoice_count: int
    invoice_status: str
    delivery_status: str


class PurchaseOrdersResponse(RootModel[List[PurchaseOrderSchema]]):
    pass
