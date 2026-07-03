"""
Confidence Scorer — Routes invoices to auto-approve, flag, or full review.
Combines Gemini's extraction confidence with validation results.
"""

import config
from models.invoice import InvoiceStatus


def compute_final_confidence(
    gemini_confidence: float,
    math_valid: bool,
    is_duplicate: bool,
    missing_critical_fields: list
) -> dict:
    """
    Computes final confidence score and determines routing.
    
    Factors that LOWER confidence:
    - Math errors: -30 points
    - Duplicate detected: forces REJECTED status
    - Missing critical fields: -10 points each (max -30)
    
    Returns:
        {
            "final_score": float,
            "status": InvoiceStatus,
            "flagged_fields": list,
            "reason": str
        }
    """
    flagged_fields = []
    score = gemini_confidence  # Start with Gemini's own confidence

    # Duplicate = instant flag for human review
    if is_duplicate:
        return {
            "final_score": 0,
            "status": InvoiceStatus.FLAGGED,
            "flagged_fields": ["duplicate"],
            "reason": "Duplicate invoice detected — requires human confirmation"
        }

    # Math errors reduce score significantly
    if not math_valid:
        score -= 30
        flagged_fields.append("math_error")

    # Missing critical fields reduce score
    critical_fields = ["vendor_name", "invoice_number", "total_amount", "invoice_date"]
    for field in missing_critical_fields:
        if field in critical_fields:
            score -= 10
            flagged_fields.append(field)

    score = max(0, min(100, score))  # Clamp 0-100

    # ─── Routing Decision ─────────────────────────────────
    if score >= config.AUTO_APPROVE_THRESHOLD and not flagged_fields:
        status = InvoiceStatus.AUTO_APPROVED
        reason = f"High confidence ({score:.1f}%) — auto approved ✓"

    elif score >= config.FLAG_THRESHOLD:
        status = InvoiceStatus.FLAGGED
        reason = f"Medium confidence ({score:.1f}%) — specific fields flagged for review"

    else:
        status = InvoiceStatus.REVIEW_REQUIRED
        reason = f"Low confidence ({score:.1f}%) — full human review required"

    return {
        "final_score": round(score, 1),
        "status": status,
        "flagged_fields": flagged_fields,
        "reason": reason
    }


def get_missing_critical_fields(extracted_data: dict) -> list:
    """Returns list of critical fields that are None or missing."""
    critical = ["vendor_name", "invoice_number", "total_amount", "invoice_date"]
    missing = []
    for field in critical:
        if not extracted_data.get(field):
            missing.append(field)
    return missing
