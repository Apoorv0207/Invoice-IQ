from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from typing import Optional

from services.mongodb import invoices_col
from services.redis_cache import get_processing_status

router = APIRouter(prefix="/api", tags=["invoices"])


def serialize_invoice(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    doc["id"] = str(doc.pop("_id"))
    if doc.get("created_at"):
        doc["created_at"] = doc["created_at"].isoformat()
    if doc.get("updated_at"):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc


@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    skip: int = Query(0)
):
    """
    List all invoices with optional status filter.
    Returns sorted by created_at descending (newest first).
    """
    col = invoices_col()
    query = {}
    if status:
        query["status"] = status

    cursor = col.find(query, {"file_bytes": 0}).sort("created_at", -1).skip(skip).limit(limit)
    invoices = await cursor.to_list(limit)

    total = await col.count_documents(query)

    return {
        "total": total,
        "invoices": [serialize_invoice(inv) for inv in invoices]
    }


@router.get("/invoices/stats")
async def get_stats():
    """Dashboard stats — counts by status."""
    col = invoices_col()
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    results = await col.aggregate(pipeline).to_list(20)
    stats = {r["_id"]: r["count"] for r in results}
    stats["total"] = sum(stats.values())
    return stats


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get a single invoice by ID."""
    col = invoices_col()
    try:
        oid = ObjectId(invoice_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Check processing status from Redis
    redis_status = await get_processing_status(invoice_id)
    result = serialize_invoice(doc)
    if redis_status:
        result["processing_status"] = redis_status

    return result
