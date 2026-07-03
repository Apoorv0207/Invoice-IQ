from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from bson import ObjectId
import csv
import json
import io
from datetime import datetime

from services.mongodb import invoices_col

router = APIRouter(prefix="/api", tags=["export"])


def flatten_invoice_for_csv(doc: dict) -> dict:
    """Flatten nested invoice data for CSV export."""
    data = doc.get("approved_data") or doc.get("extracted_data") or {}
    validation = doc.get("validation") or {}

    return {
        "invoice_id": str(doc.get("_id", "")),
        "file_name": doc.get("file_name", ""),
        "status": doc.get("status", ""),
        "confidence_score": doc.get("confidence_score", ""),
        "vendor_name": data.get("vendor_name", ""),
        "vendor_address": data.get("vendor_address", ""),
        "invoice_number": data.get("invoice_number", ""),
        "invoice_date": data.get("invoice_date", ""),
        "due_date": data.get("due_date", ""),
        "po_number": data.get("po_number", ""),
        "subtotal": data.get("subtotal", ""),
        "tax_rate": data.get("tax_rate", ""),
        "tax_amount": data.get("tax_amount", ""),
        "total_amount": data.get("total_amount", ""),
        "currency": data.get("currency", "INR"),
        "payment_terms": data.get("payment_terms", ""),
        "math_valid": validation.get("math_valid", ""),
        "is_duplicate": validation.get("is_duplicate", ""),
        "created_at": doc.get("created_at", "").isoformat() if doc.get("created_at") else "",
    }


@router.get("/export/{invoice_id}/csv")
async def export_invoice_csv(invoice_id: str):
    """Export a single invoice as CSV (Tally/QuickBooks compatible format)."""
    col = invoices_col()
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get line items for CSV
    data = doc.get("approved_data") or doc.get("extracted_data") or {}
    line_items = data.get("line_items", [])

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Invoice Number", "Vendor Name", "Invoice Date", "Due Date",
        "PO Number", "Line Description", "Quantity", "Unit Price",
        "Line Total", "GL Code", "GL Description", "Tax Amount",
        "Total Amount", "Currency"
    ])

    for item in line_items:
        writer.writerow([
            data.get("invoice_number", ""),
            data.get("vendor_name", ""),
            data.get("invoice_date", ""),
            data.get("due_date", ""),
            data.get("po_number", ""),
            item.get("description", ""),
            item.get("quantity", ""),
            item.get("unit_price", ""),
            item.get("total", ""),
            item.get("gl_code", ""),
            item.get("gl_description", ""),
            data.get("tax_amount", ""),
            data.get("total_amount", ""),
            data.get("currency", "INR"),
        ])

    output.seek(0)

    # Mark as exported
    await col.update_one({"_id": oid}, {"$set": {"exported": True}})

    filename = f"invoice_{invoice_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/{invoice_id}/json")
async def export_invoice_json(invoice_id: str):
    """Export invoice as structured JSON (ERP API format)."""
    col = invoices_col()
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    data = doc.get("approved_data") or doc.get("extracted_data") or {}
    export_payload = {
        "invoice_id": invoice_id,
        "exported_at": datetime.utcnow().isoformat(),
        "invoice_data": data,
        "validation": doc.get("validation", {}),
        "confidence_score": doc.get("confidence_score"),
        "status": doc.get("status")
    }

    await col.update_one({"_id": oid}, {"$set": {"exported": True}})

    filename = f"invoice_{invoice_id}.json"
    return StreamingResponse(
        io.BytesIO(json.dumps(export_payload, indent=2, default=str).encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/batch/csv")
async def export_batch_csv(status: str = "approved"):
    """Export all approved invoices as a single CSV file."""
    col = invoices_col()
    cursor = col.find({"status": status}).sort("created_at", -1)
    docs = await cursor.to_list(1000)

    if not docs:
        raise HTTPException(status_code=404, detail=f"No invoices with status '{status}'")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(flatten_invoice_for_csv(docs[0]).keys()))
    writer.writeheader()

    for doc in docs:
        writer.writerow(flatten_invoice_for_csv(doc))

    output.seek(0)
    filename = f"invoices_{status}_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
