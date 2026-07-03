from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from datetime import datetime
from bson import ObjectId
import mimetypes

from services.mongodb import invoices_col, po_col
from services.redis_cache import set_processing_status
from services.vendor_memory import store_vendor_example
from agents.invoice_agent import run_invoice_agent
from tools.extractor import extract_po
from models.invoice import InvoiceStatus

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/jpg", "image/png", "image/webp"
}


async def process_invoice_background(
    invoice_id: str, file_bytes: bytes, mime_type: str, file_name: str
):
    col = invoices_col()
    object_id = ObjectId(invoice_id)

    try:
        await set_processing_status(invoice_id, "running")
        result = await run_invoice_agent(
            file_bytes=file_bytes,
            mime_type=mime_type,
            invoice_id=invoice_id
        )

        extracted_data = result.get("extracted_data", {})
        math_result = result.get("math_result", {})
        dup_result = result.get("duplicate_result", {})
        po_result = result.get("po_result", {})
        enriched_items = result.get("enriched_line_items", [])

        if enriched_items:
            extracted_data["line_items"] = enriched_items

        validation = {
            "math_valid": math_result.get("math_valid", True),
            "math_discrepancy": math_result.get("discrepancy"),
            "is_duplicate": dup_result.get("is_duplicate", False),
            "duplicate_invoice_id": dup_result.get("duplicate_invoice_id"),
            "flagged_fields": result.get("flagged_fields", [])
        }

        await col.update_one(
            {"_id": object_id},
            {"$set": {
                "status": result.get("final_status", InvoiceStatus.REVIEW_REQUIRED),
                "confidence_score": result.get("final_confidence", 0),
                "extracted_data": extracted_data,
                "validation": validation,
                "po_match": po_result,
                "explainability": result.get("explanations", []),
                "routing_reason": result.get("routing_reason", ""),
                "processing_time_ms": result.get("processing_time_ms"),
                "updated_at": datetime.utcnow()
            }}
        )
        await set_processing_status(invoice_id, "done")

    except Exception as e:
        print(f"❌ Error processing {invoice_id}: {e}")
        await col.update_one(
            {"_id": object_id},
            {"$set": {
                "status": InvoiceStatus.REVIEW_REQUIRED,
                "routing_reason": f"Processing error: {str(e)}",
                "updated_at": datetime.utcnow()
            }}
        )
        await set_processing_status(invoice_id, "error")


@router.post("/upload")
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a single invoice. Processing happens in background."""
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    col = invoices_col()
    result = await col.insert_one({
        "file_name": file.filename,
        "status": InvoiceStatus.PROCESSING,
        "confidence_score": None,
        "extracted_data": None,
        "validation": None,
        "po_match": None,
        "explainability": None,
        "routing_reason": "Processing...",
        "processing_time_ms": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "exported": False
    })

    invoice_id = str(result.inserted_id)
    background_tasks.add_task(
        process_invoice_background,
        invoice_id=invoice_id,
        file_bytes=file_bytes,
        mime_type=content_type,
        file_name=file.filename
    )

    return {
        "invoice_id": invoice_id,
        "file_name": file.filename,
        "status": "processing",
        "message": "Invoice uploaded. Poll /api/invoices/{id} for status."
    }


@router.post("/upload/po")
async def upload_po(file: UploadFile = File(...)):
    """
    Upload a Purchase Order document.
    Extracts PO data immediately (synchronous) and stores in MongoDB.
    """
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    # Extract PO data synchronously
    try:
        po_data = await extract_po(file_bytes, content_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PO extraction failed: {str(e)}")

    col = po_col()
    result = await col.insert_one({
        "file_name": file.filename,
        "po_number": po_data.get("po_number"),
        "vendor_name": po_data.get("vendor_name"),
        "vendor_address": po_data.get("vendor_address"),
        "issue_date": po_data.get("issue_date"),
        "delivery_date": po_data.get("delivery_date"),
        "line_items": po_data.get("line_items", []),
        "subtotal": po_data.get("subtotal"),
        "tax_amount": po_data.get("tax_amount"),
        "total_amount": po_data.get("total_amount"),
        "currency": po_data.get("currency", "INR"),
        "terms": po_data.get("terms"),
        "created_at": datetime.utcnow()
    })

    return {
        "po_id": str(result.inserted_id),
        "file_name": file.filename,
        "po_number": po_data.get("po_number"),
        "vendor_name": po_data.get("vendor_name"),
        "total_amount": po_data.get("total_amount"),
        "message": "PO uploaded and extracted successfully"
    }


@router.post("/upload/batch")
async def upload_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...)
):
    """Upload multiple invoices."""
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 files per batch.")

    results = []
    for file in files:
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        if content_type not in ALLOWED_MIME_TYPES:
            results.append({"file": file.filename, "error": "Unsupported type"})
            continue

        file_bytes = await file.read()
        col = invoices_col()
        result = await col.insert_one({
            "file_name": file.filename,
            "status": InvoiceStatus.PROCESSING,
            "confidence_score": None,
            "extracted_data": None,
            "validation": None,
            "po_match": None,
            "explainability": None,
            "routing_reason": "Processing...",
            "processing_time_ms": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "exported": False
        })
        invoice_id = str(result.inserted_id)
        background_tasks.add_task(
            process_invoice_background,
            invoice_id=invoice_id,
            file_bytes=file_bytes,
            mime_type=content_type,
            file_name=file.filename
        )
        results.append({"file": file.filename, "invoice_id": invoice_id, "status": "processing"})

    return {"uploaded": len(results), "invoices": results}
