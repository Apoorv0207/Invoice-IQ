from fastapi import APIRouter, HTTPException
from bson import ObjectId
from services.mongodb import po_col

router = APIRouter(prefix="/api", tags=["purchase-orders"])


def serialize_po(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    if doc.get("created_at"):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@router.get("/purchase-orders")
async def list_pos(limit: int = 50):
    col = po_col()
    docs = await col.find().sort("created_at", -1).limit(limit).to_list(limit)
    return {"purchase_orders": [serialize_po(d) for d in docs]}


@router.get("/purchase-orders/{po_id}")
async def get_po(po_id: str):
    col = po_col()
    try:
        oid = ObjectId(po_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PO ID")
    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="PO not found")
    return serialize_po(doc)


@router.delete("/purchase-orders/{po_id}")
async def delete_po(po_id: str):
    col = po_col()
    try:
        oid = ObjectId(po_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PO ID")
    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="PO not found")
    return {"deleted": True, "po_id": po_id}
