from pydantic import BaseModel, Field
from typing import List, Literal


class PurchaseOrderEntry(BaseModel):
    po: str = Field(..., description="Raw purchase order value detected")
    po_normalized: str = Field(..., description="Normalized form, e.g., 'PO 01-05254'")
    label_detected: str = Field(
        ...,
        description="Label text that introduced the PO (e.g., 'Referencia', 'Orden de compra')",
    )
    position_hint: Literal["Header", "Body", "Footer", "Table", "Sidebar", "Unknown"]
    raw_line: str = Field(..., description="Raw line of text where PO was found")
    evidence_snippet: str = Field(..., description="Surrounding evidence text snippet")


class PrimaryPurchaseOrder(BaseModel):
    label_detected: str
    position_hint: Literal["Header", "Body", "Footer", "Table", "Sidebar", "Unknown"]
    raw_line: str
    evidence_snippet: str


class PurchaseOrder(BaseModel):
    primary_po: str = Field(..., description="Main purchase order value or N/A")
    primary_po_normalized: str = Field(..., description="Normalized main PO or N/A")
    primary: PrimaryPurchaseOrder
    other_pos: List[PurchaseOrderEntry]


class PurchaseOrderResponse(BaseModel):
    purchase_order: PurchaseOrder
