"""
All Gemini prompts — centralized for easy iteration.
"""


def get_extraction_prompt(few_shot_section: str = "") -> str:
    """
    Main invoice extraction prompt.
    Accepts a pre-built few_shot_section from vendor_memory.build_few_shot_section().
    Gemini is ALWAYS called — few-shot examples improve accuracy for known vendors.
    """
    return f"""You are an expert invoice data extraction AI for Indian accounting.
Extract ALL fields from the invoice image/document provided.
Return ONLY valid JSON — no markdown, no explanation, no preamble.

{few_shot_section}

Return this exact JSON structure:
{{
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "po_number": "string or null",
  "line_items": [
    {{
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }}
  ],
  "subtotal": number or null,
  "tax_rate": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "currency": "INR",
  "payment_terms": "string or null",
  "bank_details": "string or null",
  "confidence_score": number between 0 and 100
}}

Rules:
- confidence_score: your honest confidence in the overall extraction (0-100)
- All monetary values as plain numbers (no ₹ symbol)
- null if field not present
- line_items always an array (empty [] if none)
- Dates must be YYYY-MM-DD
- Return ONLY the JSON object
"""


def get_po_extraction_prompt() -> str:
    """Prompt for extracting structured data from a Purchase Order document."""
    return """You are an expert Purchase Order data extraction AI.
Extract ALL fields from the PO document provided.
Return ONLY valid JSON — no markdown, no explanation.

Return this exact structure:
{
  "po_number": "string or null",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "issue_date": "YYYY-MM-DD or null",
  "delivery_date": "YYYY-MM-DD or null",
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ],
  "subtotal": number or null,
  "tax_amount": number or null,
  "total_amount": number or null,
  "currency": "INR",
  "terms": "string or null"
}

Rules:
- All monetary values as plain numbers
- null if field not present
- Return ONLY the JSON object
"""


def get_batch_extraction_prompt(count: int, few_shot_section: str = "") -> str:
    """Batch extraction prompt for multiple invoices in one Gemini call."""
    return f"""You are an expert invoice data extraction AI.
The document contains {count} invoices. Extract data from ALL of them.
Return ONLY a valid JSON array.

{few_shot_section}

Return this exact structure (array of {count} objects):
[
  {{
    "vendor_name": "string or null",
    "vendor_address": "string or null",
    "invoice_number": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "due_date": "YYYY-MM-DD or null",
    "po_number": "string or null",
    "line_items": [
      {{
        "description": "string",
        "quantity": number,
        "unit_price": number,
        "total": number
      }}
    ],
    "subtotal": number or null,
    "tax_rate": number or null,
    "tax_amount": number or null,
    "total_amount": number or null,
    "currency": "INR",
    "payment_terms": "string or null",
    "bank_details": "string or null",
    "confidence_score": number between 0 and 100
  }}
]

Return ONLY the JSON array, nothing else.
"""
