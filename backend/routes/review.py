from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from services.mongodb import invoices_col
from services.learning_loop import store_correction
from services.vendor_memory import store_vendor_example
from models.invoice import InvoiceStatus

router = APIRouter(prefix="/api", tags=["review"])


class ReviewPayload(BaseModel):
    action: str  # "approve" | "reject"
    corrected_data: Optional[dict] = None
    reviewer: Optional[str] = "human"


@router.patch("/invoices/{invoice_id}/review")
async def review_invoice(invoice_id: str, payload: ReviewPayload):
    col = invoices_col()
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    new_status = InvoiceStatus.APPROVED if payload.action == "approve" else InvoiceStatus.REJECTED
    if payload.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    original_data = doc.get("extracted_data", {})
    corrected_data = payload.corrected_data or original_data
    vendor_name = (corrected_data or original_data or {}).get("vendor_name", "unknown")

    learning_updated = False

    if payload.action == "approve":
        # Store correction in learning loop (for prompt improvement)
        if payload.corrected_data and payload.corrected_data != original_data:
            await store_correction(
                invoice_id=invoice_id,
                vendor_name=vendor_name,
                original_data=original_data,
                corrected_data=payload.corrected_data
            )
            learning_updated = True

        # Always store approved extraction in vendor memory (few-shot examples)
        final_data = corrected_data or original_data
        invoice_hint = (
            f"Invoice #{final_data.get('invoice_number', 'N/A')} "
            f"dated {final_data.get('invoice_date', 'N/A')} "
            f"total ₹{final_data.get('total_amount', 'N/A')}"
        )
        await store_vendor_example(
            vendor_name=vendor_name,
            invoice_text_hint=invoice_hint,
            correct_extraction=final_data
        )

    await col.update_one(
        {"_id": oid},
        {"$set": {
            "status": new_status,
            "approved_data": corrected_data if payload.action == "approve" else None,
            "human_corrections": payload.corrected_data,
            "reviewed_by": payload.reviewer,
            "updated_at": datetime.utcnow()
        }}
    )

    return {
        "invoice_id": invoice_id,
        "status": new_status,
        "learning_updated": learning_updated,
        "vendor_memory_updated": payload.action == "approve",
        "message": f"Invoice {payload.action}d successfully"
    }


@router.patch("/invoices/{invoice_id}/field")
async def update_field(invoice_id: str, field: str, value: str):
    """Quick inline field update for flagged invoices."""
    col = invoices_col()
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")

    allowed_fields = [
        "vendor_name", "invoice_number", "invoice_date", "due_date",
        "po_number", "total_amount", "tax_amount", "subtotal",
        "payment_terms", "bank_details"
    ]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Field '{field}' not editable")

    await col.update_one(
        {"_id": oid},
        {"$set": {f"extracted_data.{field}": value, "updated_at": datetime.utcnow()}}
    )
    return {"invoice_id": invoice_id, "field": field, "updated_to": value}


@router.get("/invoices/{invoice_id}/explain")
async def get_explanations(invoice_id: str):
    """Fetch all AI decision explanations for an invoice."""
    from tools.explainability import get_explanations
    explanations = await get_explanations(invoice_id)
    return {"invoice_id": invoice_id, "explanations": explanations}
