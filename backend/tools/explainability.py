"""
Explainability Layer — generates human-readable reasoning for every AI decision.

Stored per invoice so users can always ask "why did this happen?"
"""

from datetime import datetime
from services.mongodb import explainability_col


async def store_explanations(invoice_id: str, explanations: list):
    """Persist all explanations for an invoice to MongoDB."""
    col = explainability_col()
    await col.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "invoice_id": invoice_id,
            "explanations": explanations,
            "created_at": datetime.utcnow()
        }},
        upsert=True
    )


async def get_explanations(invoice_id: str) -> list:
    """Retrieve all explanations for an invoice."""
    col = explainability_col()
    doc = await col.find_one({"invoice_id": invoice_id})
    return doc.get("explanations", []) if doc else []


def explain_extraction(extracted_data: dict, few_shot_count: int) -> dict:
    """Generate explanation for the extraction decision."""
    confidence = extracted_data.get("confidence_score", 0)
    vendor = extracted_data.get("vendor_name", "Unknown vendor")
    field_count = sum(1 for v in extracted_data.values() if v is not None)

    reasons = [
        f"Gemini 2.5 Flash processed the document and returned {field_count} fields",
        f"Model self-reported confidence: {confidence}%",
    ]
    if few_shot_count > 0:
        reasons.append(f"Used {few_shot_count} historical example(s) from vendor memory for '{vendor}'")
    else:
        reasons.append(f"No prior examples found for '{vendor}' — cold start extraction")

    missing = [k for k, v in extracted_data.items()
               if v is None and k in ["vendor_name", "invoice_number", "total_amount", "invoice_date"]]
    if missing:
        reasons.append(f"Critical fields not found: {', '.join(missing)}")

    return {
        "decision": "Invoice Extraction",
        "output": f"Extracted {field_count} fields from document",
        "confidence": round(confidence / 100, 2),
        "reason": reasons
    }


def explain_math_validation(math_result: dict) -> dict:
    """Generate explanation for math validation decision."""
    valid = math_result.get("math_valid", True)
    discrepancy = math_result.get("discrepancy")
    line_errors = math_result.get("line_item_errors", [])

    reasons = ["Performed deterministic arithmetic check (no AI involved)"]
    if valid:
        reasons.append("All line items × quantities match their stated totals")
        reasons.append("Sum of line items + tax equals invoice total ✓")
    else:
        if line_errors:
            reasons.append(f"{len(line_errors)} line item(s) have arithmetic errors")
        if discrepancy:
            reasons.append(f"Total discrepancy of ₹{discrepancy} detected")

    return {
        "decision": "Math Validation",
        "output": "PASS" if valid else f"FAIL — ₹{discrepancy or 'line item'} mismatch",
        "confidence": 1.0,  # Always deterministic
        "reason": reasons
    }


def explain_duplicate_check(dup_result: dict) -> dict:
    """Generate explanation for duplicate detection decision."""
    is_dup = dup_result.get("is_duplicate", False)
    dup_id = dup_result.get("duplicate_invoice_id")

    reasons = [
        "Hashed invoice_number + vendor_name + total_amount",
        "Searched across ALL historical approved invoices (cross-batch)"
    ]
    if is_dup:
        reasons.append(f"Matching invoice found with ID: {dup_id}")
        reasons.append("Invoice flagged to prevent double payment")
    else:
        reasons.append("No matching invoice found in history ✓")

    return {
        "decision": "Duplicate Detection",
        "output": f"DUPLICATE FOUND (ID: {dup_id})" if is_dup else "No duplicate",
        "confidence": 1.0,
        "reason": reasons
    }


def explain_po_match(po_result: dict) -> dict:
    """Generate explanation for PO matching decision."""
    status = po_result.get("po_status", "MISSING")
    mismatches = po_result.get("mismatches", [])
    po_num = po_result.get("po_number", "unknown")

    reasons = [f"Searched MongoDB for PO matching PO# '{po_num}'"]

    if status == "MISSING":
        reasons.append("No matching Purchase Order found in database")
        reasons.append("Invoice cannot be verified against a PO")
    elif status == "PASS":
        reasons.append(f"PO {po_num} found and matched")
        reasons.append(f"All fields within {5}% tolerance threshold ✓")
    else:
        reasons.append(f"PO {po_num} found but {len(mismatches)} field(s) exceeded tolerance")
        for m in mismatches:
            reasons.append(
                f"  • {m['field']}: invoice={m['invoice_value']}, PO={m['po_value']} "
                f"({m['difference_percent']}% variance)"
            )

    return {
        "decision": "PO Matching",
        "output": status,
        "confidence": 1.0,
        "reason": reasons
    }


def explain_gl_assignment(line_item_description: str, gl_result: dict) -> dict:
    """Generate explanation for a single GL code assignment."""
    gl_code = gl_result.get("gl_code", "9999")
    gl_desc = gl_result.get("gl_description", "Unclassified")
    confidence = gl_result.get("confidence", 0)
    category = gl_result.get("category", "Unknown")

    reasons = [
        f"Embedded line item description using gemini-embedding-001 (3072 dimensions)",
        f"Searched MongoDB Atlas Vector Search across 50 GL codes",
        f"Semantic similarity score: {confidence}%",
        f"Matched category: {category}",
    ]
    if confidence >= 85:
        reasons.append("High similarity — confident assignment")
    elif confidence >= 60:
        reasons.append("Moderate similarity — review recommended")
    else:
        reasons.append("Low similarity — manual GL assignment advised")

    return {
        "decision": "GL Assignment",
        "output": f"{gl_code} — {gl_desc}",
        "confidence": round(confidence / 100, 2),
        "reason": reasons,
        "metadata": {
            "line_item": line_item_description,
            "gl_code": gl_code,
            "gl_description": gl_desc
        }
    }


def explain_confidence_routing(score: float, status: str, flagged_fields: list, reason: str) -> dict:
    """Generate explanation for the final routing decision."""
    reasons = [
        f"Final confidence score computed: {score}%",
        f"Auto-approve threshold: ≥{95}%",
        f"Flag threshold: ≥{75}%",
    ]
    if flagged_fields:
        reasons.append(f"Fields that lowered score: {', '.join(flagged_fields)}")
    reasons.append(reason)

    return {
        "decision": "Confidence Routing",
        "output": status,
        "confidence": round(score / 100, 2),
        "reason": reasons
    }
