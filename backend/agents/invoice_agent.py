"""
Invoice Agent v2 — Updated 8-node LangGraph pipeline.

New pipeline:
Extract → Math Validation → Duplicate Detection → PO Matching
→ GL Assignment → Explainability Generation → Confidence Routing
→ (Human Review via API) → Learning Loop (via API)
"""

import time
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

from tools.extractor import extract_single_invoice
from tools.math_validator import validate_math
from tools.duplicate_detector import check_duplicate
from tools.po_matcher import match_po
from tools.gl_assigner import assign_gl_codes_batch
from tools.explainability import (
    explain_extraction, explain_math_validation,
    explain_duplicate_check, explain_po_match,
    explain_gl_assignment, explain_confidence_routing,
    store_explanations
)
from tools.confidence_scorer import compute_final_confidence, get_missing_critical_fields
from models.invoice import InvoiceStatus


class InvoiceAgentState(TypedDict):
    # Input
    file_bytes: bytes
    mime_type: str
    invoice_id: str
    vendor_hint: Optional[str]
    start_time: float

    # Intermediate
    extracted_data: Optional[dict]
    math_result: Optional[dict]
    duplicate_result: Optional[dict]
    po_result: Optional[dict]
    enriched_line_items: Optional[list]
    explanations: Optional[list]

    # Output
    final_confidence: Optional[float]
    final_status: Optional[str]
    flagged_fields: Optional[list]
    routing_reason: Optional[str]
    processing_time_ms: Optional[float]
    error: Optional[str]


# ─── NODE 1: Extract ──────────────────────────────────────
async def node_extract(state: InvoiceAgentState) -> dict:
    print(f"🔍 [1/6] Extracting — {state['invoice_id']}")
    try:
        extracted = await extract_single_invoice(
            file_bytes=state["file_bytes"],
            mime_type=state["mime_type"],
            vendor_hint=state.get("vendor_hint")
        )
        return {"extracted_data": extracted}
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}


# ─── NODE 2: Math Validation ──────────────────────────────
async def node_validate_math(state: InvoiceAgentState) -> dict:
    print("🔢 [2/6] Math validation")
    if state.get("error"):
        return {}
    data = state.get("extracted_data", {})
    result = validate_math(
        line_items=data.get("line_items", []),
        subtotal=data.get("subtotal"),
        tax_amount=data.get("tax_amount"),
        total_amount=data.get("total_amount")
    )
    return {"math_result": result}


# ─── NODE 3: Duplicate Detection ──────────────────────────
async def node_check_duplicate(state: InvoiceAgentState) -> dict:
    print("🔁 [3/6] Duplicate detection")
    if state.get("error"):
        return {}
    data = state.get("extracted_data", {})
    result = await check_duplicate(
        invoice_number=data.get("invoice_number"),
        vendor_name=data.get("vendor_name"),
        total_amount=data.get("total_amount"),
        current_invoice_id=state.get("invoice_id")
    )
    return {"duplicate_result": result}


# ─── NODE 4: PO Matching ──────────────────────────────────
async def node_po_match(state: InvoiceAgentState) -> dict:
    print("📋 [4/6] PO matching")
    if state.get("error"):
        return {}
    data = state.get("extracted_data", {})
    result = await match_po(
        invoice_number=data.get("invoice_number"),
        po_number=data.get("po_number"),
        vendor_name=data.get("vendor_name"),
        invoice_line_items=data.get("line_items", []),
        invoice_total=data.get("total_amount"),
        invoice_tax=data.get("tax_amount")
    )
    return {"po_result": result}


# ─── NODE 5: GL Assignment ────────────────────────────────
async def node_assign_gl_codes(state: InvoiceAgentState) -> dict:
    print("📂 [5/6] GL code assignment")
    if state.get("error"):
        return {}
    data = state.get("extracted_data", {})
    line_items = data.get("line_items", [])
    if not line_items:
        return {"enriched_line_items": []}
    enriched = await assign_gl_codes_batch(line_items)
    return {"enriched_line_items": enriched}


# ─── NODE 6: Explainability + Confidence Routing ──────────
async def node_explain_and_route(state: InvoiceAgentState) -> dict:
    print("⚖️  [6/6] Explainability + routing")

    data = state.get("extracted_data", {})
    math_result = state.get("math_result", {})
    dup_result = state.get("duplicate_result", {})
    po_result = state.get("po_result", {})
    enriched = state.get("enriched_line_items", [])

    # Build explanations for each decision
    explanations = []

    if state.get("error"):
        explanations.append({
            "decision": "Processing Error",
            "output": state["error"],
            "confidence": 0,
            "reason": [state["error"]]
        })
        elapsed = (time.time() - state.get("start_time", time.time())) * 1000
        return {
            "final_status": InvoiceStatus.REVIEW_REQUIRED,
            "final_confidence": 0,
            "flagged_fields": ["extraction_error"],
            "routing_reason": state["error"],
            "explanations": explanations,
            "processing_time_ms": round(elapsed, 1)
        }

    # 1. Extraction explanation
    few_shot_count = data.get("_few_shot_count", 0)
    explanations.append(explain_extraction(data, few_shot_count))

    # 2. Math validation explanation
    if math_result:
        explanations.append(explain_math_validation(math_result))

    # 3. Duplicate explanation
    if dup_result:
        explanations.append(explain_duplicate_check(dup_result))

    # 4. PO match explanation
    if po_result:
        explanations.append(explain_po_match(po_result))

    # 5. GL assignment explanations (one per line item)
    for item in enriched:
        if item.get("gl_code"):
            gl_result = {
                "gl_code": item.get("gl_code"),
                "gl_description": item.get("gl_description"),
                "confidence": item.get("gl_confidence", 0),
                "category": item.get("gl_category", "")
            }
            explanations.append(
                explain_gl_assignment(item.get("description", ""), gl_result)
            )

    # 6. Confidence routing
    gemini_confidence = data.get("confidence_score", 50)
    math_valid = math_result.get("math_valid", True)
    is_duplicate = dup_result.get("is_duplicate", False)
    po_flagged = po_result.get("po_status") in ["FLAGGED", "MISSING"] if po_result else False
    missing_fields = get_missing_critical_fields(data)

    # PO issues lower confidence
    if po_flagged:
        gemini_confidence = min(gemini_confidence, 70)
        missing_fields.append("po_mismatch")

    from tools.confidence_scorer import compute_final_confidence
    routing = compute_final_confidence(
        gemini_confidence=gemini_confidence,
        math_valid=math_valid,
        is_duplicate=is_duplicate,
        missing_critical_fields=missing_fields
    )

    explanations.append(explain_confidence_routing(
        score=routing["final_score"],
        status=routing["status"],
        flagged_fields=routing["flagged_fields"],
        reason=routing["reason"]
    ))

    # Store explanations
    await store_explanations(state["invoice_id"], explanations)

    elapsed = (time.time() - state.get("start_time", time.time())) * 1000
    print(f"✅ Done — {routing['final_score']}% | {routing['status']} | {round(elapsed)}ms")

    return {
        "final_confidence": routing["final_score"],
        "final_status": routing["status"],
        "flagged_fields": routing["flagged_fields"],
        "routing_reason": routing["reason"],
        "explanations": explanations,
        "processing_time_ms": round(elapsed, 1)
    }


# ─── Build Graph ──────────────────────────────────────────
def build_invoice_agent():
    graph = StateGraph(InvoiceAgentState)

    graph.add_node("extract",          node_extract)
    graph.add_node("validate_math",    node_validate_math)
    graph.add_node("check_duplicate",  node_check_duplicate)
    graph.add_node("po_match",         node_po_match)
    graph.add_node("assign_gl_codes",  node_assign_gl_codes)
    graph.add_node("explain_and_route",node_explain_and_route)

    graph.set_entry_point("extract")
    graph.add_edge("extract",          "validate_math")
    graph.add_edge("validate_math",    "check_duplicate")
    graph.add_edge("check_duplicate",  "po_match")
    graph.add_edge("po_match",         "assign_gl_codes")
    graph.add_edge("assign_gl_codes",  "explain_and_route")
    graph.add_edge("explain_and_route", END)

    return graph.compile()


invoice_agent = build_invoice_agent()


async def run_invoice_agent(
    file_bytes: bytes,
    mime_type: str,
    invoice_id: str,
    vendor_hint: str = None
) -> dict:
    initial_state = InvoiceAgentState(
        file_bytes=file_bytes,
        mime_type=mime_type,
        invoice_id=invoice_id,
        vendor_hint=vendor_hint,
        start_time=time.time(),
        extracted_data=None,
        math_result=None,
        duplicate_result=None,
        po_result=None,
        enriched_line_items=None,
        explanations=None,
        final_confidence=None,
        final_status=None,
        flagged_fields=None,
        routing_reason=None,
        processing_time_ms=None,
        error=None
    )
    return await invoice_agent.ainvoke(initial_state)
