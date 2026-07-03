from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class POLineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float


class PurchaseOrder(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    file_name: str
    po_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    issue_date: Optional[str] = None
    delivery_date: Optional[str] = None
    line_items: List[POLineItem] = []
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    terms: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class POMatchResult(BaseModel):
    po_status: str  # PASS | FLAGGED | MISSING
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    mismatches: List[dict] = []
    summary: Optional[str] = None


class ExplainabilityRecord(BaseModel):
    decision: str
    output: str
    confidence: float
    reason: List[str] = []
    metadata: Optional[dict] = None
