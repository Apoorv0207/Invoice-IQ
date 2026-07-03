"""
Analytics Route — dashboard metrics for InvoiceIQ.
Aggregates from MongoDB — no caching needed for academic project.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from services.mongodb import invoices_col, po_col

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/summary")
async def get_summary():
    """
    Core dashboard metrics:
    - Counts by status
    - Average confidence score
    - Average processing time
    - Duplicate count
    - Auto-approve rate
    """
    col = invoices_col()

    # Status counts
    status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_results = await col.aggregate(status_pipeline).to_list(20)
    status_counts = {r["_id"]: r["count"] for r in status_results if r["_id"]}
    total = sum(status_counts.values())

    # Average confidence
    conf_pipeline = [
        {"$match": {"confidence_score": {"$ne": None}}},
        {"$group": {"_id": None, "avg_confidence": {"$avg": "$confidence_score"}}}
    ]
    conf_result = await col.aggregate(conf_pipeline).to_list(1)
    avg_confidence = round(conf_result[0]["avg_confidence"], 1) if conf_result else 0

    # Average processing time
    time_pipeline = [
        {"$match": {"processing_time_ms": {"$ne": None}}},
        {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time_ms"}}}
    ]
    time_result = await col.aggregate(time_pipeline).to_list(1)
    avg_time_ms = round(time_result[0]["avg_time"], 0) if time_result else 0

    # Duplicate count
    dup_count = await col.count_documents({"validation.is_duplicate": True})

    # Auto-approve rate
    auto_approved = status_counts.get("auto_approved", 0)
    auto_approve_rate = round((auto_approved / total * 100), 1) if total > 0 else 0

    return {
        "total_processed": total,
        "status_breakdown": {
            "auto_approved": status_counts.get("auto_approved", 0),
            "approved": status_counts.get("approved", 0),
            "flagged": status_counts.get("flagged", 0),
            "review_required": status_counts.get("review_required", 0),
            "rejected": status_counts.get("rejected", 0),
            "processing": status_counts.get("processing", 0),
        },
        "auto_approve_rate_percent": auto_approve_rate,
        "avg_confidence_score": avg_confidence,
        "avg_processing_time_ms": avg_time_ms,
        "duplicates_detected": dup_count,
        "manual_review_count": (
            status_counts.get("flagged", 0) +
            status_counts.get("review_required", 0)
        )
    }


@router.get("/analytics/vendors")
async def get_vendor_analytics():
    """
    Top vendors by:
    - Invoice count
    - Total invoice value
    - Approval accuracy (auto_approved + approved / total for vendor)
    """
    col = invoices_col()

    pipeline = [
        {"$match": {"extracted_data.vendor_name": {"$ne": None}}},
        {"$group": {
            "_id": "$extracted_data.vendor_name",
            "invoice_count": {"$sum": 1},
            "total_value": {"$sum": "$extracted_data.total_amount"},
            "avg_confidence": {"$avg": "$confidence_score"},
            "auto_approved": {
                "$sum": {"$cond": [{"$eq": ["$status", "auto_approved"]}, 1, 0]}
            },
            "approved": {
                "$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}
            },
            "rejected": {
                "$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}
            }
        }},
        {"$sort": {"invoice_count": -1}},
        {"$limit": 10}
    ]

    results = await col.aggregate(pipeline).to_list(10)
    vendors = []
    for r in results:
        total_v = r["invoice_count"]
        approved_total = r["auto_approved"] + r["approved"]
        approval_rate = round(approved_total / total_v * 100, 1) if total_v > 0 else 0
        vendors.append({
            "vendor_name": r["_id"],
            "invoice_count": r["invoice_count"],
            "total_value": round(r.get("total_value") or 0, 2),
            "avg_confidence": round(r.get("avg_confidence") or 0, 1),
            "approval_accuracy_percent": approval_rate,
            "rejected_count": r["rejected"]
        })

    return {"top_vendors": vendors}


@router.get("/analytics/trend")
async def get_processing_trend(days: int = 14):
    """
    Daily invoice processing trend for the last N days.
    Used for the line chart on the dashboard.
    """
    col = invoices_col()
    since = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {
            "_id": {
                "year":  {"$year":  "$created_at"},
                "month": {"$month": "$created_at"},
                "day":   {"$dayOfMonth": "$created_at"}
            },
            "count": {"$sum": 1},
            "auto_approved": {
                "$sum": {"$cond": [{"$eq": ["$status", "auto_approved"]}, 1, 0]}
            },
            "avg_confidence": {"$avg": "$confidence_score"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]

    results = await col.aggregate(pipeline).to_list(days)
    trend = []
    for r in results:
        d = r["_id"]
        date_str = f"{d['year']}-{str(d['month']).zfill(2)}-{str(d['day']).zfill(2)}"
        trend.append({
            "date": date_str,
            "total": r["count"],
            "auto_approved": r["auto_approved"],
            "avg_confidence": round(r.get("avg_confidence") or 0, 1)
        })

    return {"trend": trend, "days": days}


@router.get("/analytics/gl-codes")
async def get_gl_code_distribution():
    """Most frequently assigned GL codes across all invoices."""
    col = invoices_col()

    pipeline = [
        {"$unwind": "$extracted_data.line_items"},
        {"$match": {"extracted_data.line_items.gl_code": {"$ne": None}}},
        {"$group": {
            "_id": {
                "code": "$extracted_data.line_items.gl_code",
                "description": "$extracted_data.line_items.gl_description"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    results = await col.aggregate(pipeline).to_list(10)
    return {
        "top_gl_codes": [
            {
                "gl_code": r["_id"]["code"],
                "description": r["_id"]["description"],
                "usage_count": r["count"]
            }
            for r in results
        ]
    }


@router.get("/analytics/po-stats")
async def get_po_stats():
    """PO matching statistics."""
    col = invoices_col()
    pipeline = [
        {"$match": {"po_match": {"$ne": None}}},
        {"$group": {
            "_id": "$po_match.po_status",
            "count": {"$sum": 1}
        }}
    ]
    results = await col.aggregate(pipeline).to_list(10)
    po_stats = {r["_id"]: r["count"] for r in results if r["_id"]}
    total_with_po = sum(po_stats.values())
    return {
        "total_invoices_with_po": total_with_po,
        "po_pass": po_stats.get("PASS", 0),
        "po_flagged": po_stats.get("FLAGGED", 0),
        "po_missing": po_stats.get("MISSING", 0),
        "po_match_rate_percent": round(
            po_stats.get("PASS", 0) / total_with_po * 100, 1
        ) if total_with_po > 0 else 0
    }
