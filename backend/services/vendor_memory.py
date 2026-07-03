"""
Vendor Memory Service — replaces the old Redis cache skip logic.

Old (WRONG): Known vendor → skip Gemini entirely.
New (CORRECT): Known vendor → fetch examples → build few-shot prompt → run Gemini normally.

This keeps accuracy high even when vendor invoice layouts change.
"""

from datetime import datetime
from services.mongodb import vendor_memory_col
import config


async def get_vendor_examples(vendor_name: str) -> list:
    """
    Fetch stored extraction examples for a vendor.
    These become few-shot examples in the Gemini prompt.
    Returns up to VENDOR_MEMORY_MAX_EXAMPLES examples.
    """
    if not vendor_name:
        return []

    col = vendor_memory_col()
    vendor_key = _normalize(vendor_name)

    doc = await col.find_one({"vendor_key": vendor_key})
    if not doc:
        return []

    examples = doc.get("examples", [])
    # Return most recent N examples
    return examples[-config.VENDOR_MEMORY_MAX_EXAMPLES:]


async def store_vendor_example(
    vendor_name: str,
    invoice_text_hint: str,
    correct_extraction: dict
):
    """
    Store a confirmed-correct extraction as a future few-shot example.
    Called when human approves or corrects an invoice.

    invoice_text_hint: a short text summary of the invoice
                       (we can't store the image, so we store key fields as text)
    correct_extraction: the final approved extraction dict
    """
    col = vendor_memory_col()
    vendor_key = _normalize(vendor_name)

    example = {
        "invoice_hint": invoice_text_hint,
        "correct_extraction": correct_extraction,
        "stored_at": datetime.utcnow().isoformat()
    }

    existing = await col.find_one({"vendor_key": vendor_key})

    if existing:
        examples = existing.get("examples", [])
        examples.append(example)
        # Keep only last 10 examples per vendor
        examples = examples[-10:]
        await col.update_one(
            {"vendor_key": vendor_key},
            {"$set": {"examples": examples, "updated_at": datetime.utcnow()}}
        )
    else:
        await col.insert_one({
            "vendor_key": vendor_key,
            "vendor_name": vendor_name,
            "examples": [example],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    print(f"✅ Vendor memory updated for: {vendor_name}")


async def get_vendor_stats(vendor_name: str) -> dict:
    """Returns metadata about how much we know about this vendor."""
    col = vendor_memory_col()
    vendor_key = _normalize(vendor_name)
    doc = await col.find_one({"vendor_key": vendor_key})
    if not doc:
        return {"known": False, "example_count": 0}
    return {
        "known": True,
        "example_count": len(doc.get("examples", [])),
        "first_seen": doc.get("created_at"),
        "last_updated": doc.get("updated_at")
    }


def _normalize(vendor_name: str) -> str:
    return vendor_name.lower().strip().replace(" ", "_")


def build_few_shot_section(examples: list) -> str:
    """
    Converts stored examples into a few-shot text block
    to inject into the Gemini extraction prompt.
    """
    if not examples:
        return ""

    lines = ["HISTORICAL EXAMPLES FOR THIS VENDOR (use as reference):"]
    for i, ex in enumerate(examples, 1):
        hint = ex.get("invoice_hint", "")
        ext = ex.get("correct_extraction", {})
        lines.append(f"\nExample {i}:")
        if hint:
            lines.append(f"  Invoice context: {hint}")
        lines.append(f"  Correct vendor_name: {ext.get('vendor_name', '')}")
        lines.append(f"  Correct invoice_number format: {ext.get('invoice_number', '')}")
        lines.append(f"  Correct total_amount: {ext.get('total_amount', '')}")
        lines.append(f"  Correct tax_rate: {ext.get('tax_rate', '')}")

    return "\n".join(lines)
