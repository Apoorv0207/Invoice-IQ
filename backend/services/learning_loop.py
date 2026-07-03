from datetime import datetime
from services.mongodb import corrections_col, vendor_prompts_col
from services.redis_cache import invalidate_vendor_schema
import json


async def store_correction(
    invoice_id: str,
    vendor_name: str,
    original_data: dict,
    corrected_data: dict
):
    """
    Store human correction in MongoDB.
    This is what makes the system smarter over time.
    """
    correction = {
        "invoice_id": invoice_id,
        "vendor_name": vendor_name,
        "original": original_data,
        "corrected": corrected_data,
        "diff": _compute_diff(original_data, corrected_data),
        "created_at": datetime.utcnow()
    }
    await corrections_col().insert_one(correction)

    # Update vendor-specific prompt examples
    await _update_vendor_prompt(vendor_name, correction["diff"])

    # Invalidate Redis cache so next invoice uses updated prompt
    await invalidate_vendor_schema(vendor_name)

    print(f"✅ Correction stored for vendor: {vendor_name}")


async def _update_vendor_prompt(vendor_name: str, diff: dict):
    """
    Maintains a list of known corrections per vendor.
    Injected as few-shot examples into Gemini prompts.
    Max 5 most recent corrections kept per vendor.
    """
    col = vendor_prompts_col()
    vendor_key = vendor_name.lower().strip()

    existing = await col.find_one({"vendor_key": vendor_key})

    if existing:
        corrections = existing.get("corrections", [])
        corrections.append(diff)
        # Keep only last 5 corrections
        corrections = corrections[-5:]
        await col.update_one(
            {"vendor_key": vendor_key},
            {"$set": {"corrections": corrections, "updated_at": datetime.utcnow()}}
        )
    else:
        await col.insert_one({
            "vendor_key": vendor_key,
            "vendor_name": vendor_name,
            "corrections": [diff],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })


async def get_vendor_corrections(vendor_name: str) -> list:
    """
    Fetch stored corrections for a vendor to inject as few-shot examples.
    """
    col = vendor_prompts_col()
    vendor_key = vendor_name.lower().strip()
    doc = await col.find_one({"vendor_key": vendor_key})
    if doc:
        return doc.get("corrections", [])
    return []


def _compute_diff(original: dict, corrected: dict) -> dict:
    """Returns only fields that changed between original and corrected."""
    diff = {}
    for key in corrected:
        if corrected.get(key) != original.get(key):
            diff[key] = {
                "was": original.get(key),
                "corrected_to": corrected.get(key)
            }
    return diff
