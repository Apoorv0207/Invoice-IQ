from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InvoiceStatus(str, Enum):
    PROCESSING = "processing"
    AUTO_APPROVED = "auto_approved"
    FLAGGED = "flagged"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float
    gl_code: Optional[str] = None
    gl_description: Optional[str] = None
    gl_confidence: Optional[float] = None


class ValidationResult(BaseModel):
    math_valid: bool
    math_discrepancy: Optional[float] = None
    is_duplicate: bool
    duplicate_invoice_id: Optional[str] = None
    flagged_fields: List[str] = []


class InvoiceData(BaseModel):
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    po_number: Optional[str] = None
    line_items: List[LineItem] = []
    subtotal: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    payment_terms: Optional[str] = None
    bank_details: Optional[str] = None


class Invoice(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    file_name: str
    file_url: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.PROCESSING
    confidence_score: Optional[float] = None
    extracted_data: Optional[InvoiceData] = None
    validation: Optional[ValidationResult] = None
    human_corrections: Optional[dict] = None
    approved_data: Optional[InvoiceData] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    exported: bool = False

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

class InvoiceV2(BaseModel):
    """Extended invoice model with PO match + explainability fields."""
    id: Optional[str] = Field(default=None, alias="_id")
    file_name: str
    file_url: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.PROCESSING
    confidence_score: Optional[float] = None
    extracted_data: Optional[InvoiceData] = None
    validation: Optional[ValidationResult] = None
    po_match: Optional[dict] = None
    explainability: Optional[List[dict]] = None
    human_corrections: Optional[dict] = None
    approved_data: Optional[InvoiceData] = None
    processing_time_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    exported: bool = False

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
