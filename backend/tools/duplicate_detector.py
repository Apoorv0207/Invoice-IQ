"""
Duplicate Detector — Cross-batch duplicate detection.
Checks invoice_number + vendor_name + total_amount combination.
Flags before any posting — not after.
"""

import hashlib
from services.mongodb import invoices_col


def _generate_invoice_hash(
    invoice_number: str,
    vendor_name: str,
    total_amount: float
) -> str:
    """
    Creates a deterministic hash from key invoice fields.
    Same invoice from same vendor with same total = same hash.
    """
    raw = f"{(invoice_number or '').strip().lower()}:{(vendor_name or '').strip().lower()}:{total_amount or 0}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def check_duplicate(
    invoice_number: str,
    vendor_name: str,
    total_amount: float,
    current_invoice_id: str = None
) -> dict:
    """
    Cross-batch duplicate detection.
    Searches ALL historical invoices, not just current batch.
    
    Returns:
        {
            "is_duplicate": bool,
            "duplicate_invoice_id": str or None,
            "detail": str
        }
    """
    if not invoice_number and not vendor_name:
        return {
            "is_duplicate": False,
            "duplicate_invoice_id": None,
            "detail": "Could not check — missing invoice number and vendor name"
        }

    col = invoices_col()

    # Build query
    query = {}
    if invoice_number:
        query["extracted_data.invoice_number"] = invoice_number.strip()
    if vendor_name:
        query["extracted_data.vendor_name"] = {"$regex": vendor_name.strip(), "$options": "i"}
    if total_amount:
        # Allow ±1 rupee tolerance for total match
        query["extracted_data.total_amount"] = {
            "$gte": total_amount - 1,
            "$lte": total_amount + 1
        }

    # Exclude current invoice from check
    if current_invoice_id:
        from bson import ObjectId
        try:
            query["_id"] = {"$ne": ObjectId(current_invoice_id)}
        except Exception:
            pass

    # Only check against approved/auto_approved invoices
    query["status"] = {"$in": ["auto_approved", "approved"]}

    existing = await col.find_one(query)

    if existing:
        dup_id = str(existing.get("_id", ""))
        return {
            "is_duplicate": True,
            "duplicate_invoice_id": dup_id,
            "detail": (
                f"Duplicate detected! Invoice '{invoice_number}' from '{vendor_name}' "
                f"was already posted (ID: {dup_id})"
            )
        }

    return {
        "is_duplicate": False,
        "duplicate_invoice_id": None,
        "detail": "No duplicate found ✓"
    }
