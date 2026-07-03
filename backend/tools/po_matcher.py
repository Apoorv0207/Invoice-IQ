"""
PO Matcher — LangGraph node that compares invoice against Purchase Order.

Three outcomes:
- PASS: all fields within tolerance
- FLAGGED: one or more fields outside PO_MATCH_TOLERANCE_PERCENT
- MISSING: no matching PO found in database
"""

from services.mongodb import po_col
import config


async def match_po(
    invoice_number: str,
    po_number: str,
    vendor_name: str,
    invoice_line_items: list,
    invoice_total: float,
    invoice_tax: float
) -> dict:
    """
    Fetch matching PO from MongoDB and compare against invoice fields.
    Returns structured match result with per-field mismatch details.
    """

    # ─── Step 1: Find the PO ──────────────────────────────
    po = await _find_po(po_number, vendor_name)

    if not po:
        return {
            "po_status": "MISSING",
            "po_id": None,
            "po_number": po_number,
            "mismatches": [],
            "summary": f"No PO found matching PO# '{po_number}' for vendor '{vendor_name}'"
        }

    # ─── Step 2: Compare fields ───────────────────────────
    mismatches = []
    tolerance = config.PO_MATCH_TOLERANCE_PERCENT / 100.0

    # Total amount check
    po_total = po.get("total_amount")
    if po_total and invoice_total:
        diff_pct = abs(invoice_total - po_total) / po_total if po_total else 0
        if diff_pct > tolerance:
            mismatches.append({
                "field": "total_amount",
                "invoice_value": invoice_total,
                "po_value": po_total,
                "difference_percent": round(diff_pct * 100, 2)
            })

    # Tax amount check
    po_tax = po.get("tax_amount")
    if po_tax and invoice_tax:
        diff_pct = abs(invoice_tax - po_tax) / po_tax if po_tax else 0
        if diff_pct > tolerance:
            mismatches.append({
                "field": "tax_amount",
                "invoice_value": invoice_tax,
                "po_value": po_tax,
                "difference_percent": round(diff_pct * 100, 2)
            })

    # Line item comparison (match by index)
    po_items = po.get("line_items", [])
    for i, inv_item in enumerate(invoice_line_items):
        if i >= len(po_items):
            mismatches.append({
                "field": f"line_item_{i+1}",
                "invoice_value": f"{inv_item.get('description')} x{inv_item.get('quantity')}",
                "po_value": "NOT IN PO",
                "difference_percent": 100
            })
            continue

        po_item = po_items[i]

        # Quantity check
        inv_qty = inv_item.get("quantity", 0)
        po_qty = po_item.get("quantity", 0)
        if po_qty and inv_qty:
            diff_pct = abs(inv_qty - po_qty) / po_qty
            if diff_pct > tolerance:
                mismatches.append({
                    "field": f"line_{i+1}_quantity",
                    "invoice_value": inv_qty,
                    "po_value": po_qty,
                    "difference_percent": round(diff_pct * 100, 2)
                })

        # Unit price check
        inv_price = inv_item.get("unit_price", 0)
        po_price = po_item.get("unit_price", 0)
        if po_price and inv_price:
            diff_pct = abs(inv_price - po_price) / po_price
            if diff_pct > tolerance:
                mismatches.append({
                    "field": f"line_{i+1}_unit_price",
                    "invoice_value": inv_price,
                    "po_value": po_price,
                    "difference_percent": round(diff_pct * 100, 2)
                })

    # ─── Step 3: Determine status ─────────────────────────
    po_status = "PASS" if not mismatches else "FLAGGED"

    summary = (
        f"PO {po.get('po_number')} matched — {len(mismatches)} mismatch(es) found"
        if mismatches else
        f"PO {po.get('po_number')} matched — all fields within {config.PO_MATCH_TOLERANCE_PERCENT}% tolerance ✓"
    )

    return {
        "po_status": po_status,
        "po_id": str(po.get("_id", "")),
        "po_number": po.get("po_number"),
        "mismatches": mismatches,
        "summary": summary,
        "po_vendor": po.get("vendor_name"),
        "po_total": po.get("total_amount")
    }


async def _find_po(po_number: str, vendor_name: str) -> dict | None:
    """Find PO by PO number, with vendor name as secondary filter."""
    col = po_col()

    # Try exact PO number match first
    if po_number:
        po = await col.find_one({"po_number": {"$regex": f"^{po_number}$", "$options": "i"}})
        if po:
            return po

    # Try vendor match if no PO number
    if vendor_name:
        po = await col.find_one({"vendor_name": {"$regex": vendor_name[:10], "$options": "i"}})
        if po:
            return po

    return None
