"""
Math Validator — Pure deterministic logic. No AI.
Checks: sum(line_items) + tax = total
"""

from typing import List, Optional


TOLERANCE = 0.02  # 2 paise tolerance for floating point rounding


def validate_math(
    line_items: List[dict],
    subtotal: Optional[float],
    tax_amount: Optional[float],
    total_amount: Optional[float]
) -> dict:
    """
    Validates invoice math at three levels:
    1. Each line item: quantity × unit_price == total
    2. Sum of line items == subtotal
    3. subtotal + tax_amount == total_amount
    
    Returns:
        {
            "math_valid": bool,
            "discrepancy": float or None,
            "line_item_errors": list,
            "detail": str
        }
    """
    errors = []
    line_item_errors = []

    # ─── Level 1: Individual line item math ───────────────
    computed_subtotal = 0.0
    for i, item in enumerate(line_items):
        qty = item.get("quantity", 0)
        unit_price = item.get("unit_price", 0)
        stated_total = item.get("total", 0)

        if qty and unit_price:
            expected = round(qty * unit_price, 2)
            if abs(expected - stated_total) > TOLERANCE:
                line_item_errors.append({
                    "line": i + 1,
                    "description": item.get("description", f"Line {i+1}"),
                    "expected": expected,
                    "stated": stated_total,
                    "diff": round(stated_total - expected, 2)
                })
            computed_subtotal += expected
        else:
            computed_subtotal += stated_total

    computed_subtotal = round(computed_subtotal, 2)

    # ─── Level 2: Subtotal check ──────────────────────────
    if subtotal is not None and line_items:
        if abs(computed_subtotal - subtotal) > TOLERANCE:
            errors.append(
                f"Subtotal mismatch: line items sum to {computed_subtotal}, "
                f"but stated subtotal is {subtotal}"
            )

    # ─── Level 3: Total check ─────────────────────────────
    if total_amount is not None:
        base = subtotal if subtotal is not None else computed_subtotal
        tax = tax_amount or 0.0
        computed_total = round(base + tax, 2)

        if abs(computed_total - total_amount) > TOLERANCE:
            discrepancy = round(total_amount - computed_total, 2)
            errors.append(
                f"Total mismatch: {base} + {tax} (tax) = {computed_total}, "
                f"but stated total is {total_amount}. Discrepancy: {discrepancy}"
            )
            return {
                "math_valid": False,
                "discrepancy": discrepancy,
                "line_item_errors": line_item_errors,
                "detail": " | ".join(errors) if errors else f"Line item errors found"
            }

    if line_item_errors:
        return {
            "math_valid": False,
            "discrepancy": None,
            "line_item_errors": line_item_errors,
            "detail": f"{len(line_item_errors)} line item(s) have math errors"
        }

    return {
        "math_valid": True,
        "discrepancy": None,
        "line_item_errors": [],
        "detail": "All math checks passed ✓"
    }
