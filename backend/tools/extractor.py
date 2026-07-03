"""
Extractor — Gemini 2.5 Flash extraction with few-shot vendor memory.

KEY CHANGE from v1:
OLD: Known vendor → skip Gemini (bad — breaks on layout changes)
NEW: Known vendor → fetch examples → inject as few-shot → run Gemini normally
"""

import google.generativeai as genai
import json
import base64
from typing import List

import config
from agents.prompts import get_extraction_prompt, get_batch_extraction_prompt, get_po_extraction_prompt
from services.vendor_memory import get_vendor_examples, build_few_shot_section

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel(config.GEMINI_MODEL)


def _encode_file(file_bytes: bytes, mime_type: str) -> dict:
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(file_bytes).decode("utf-8")
        }
    }


def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return raw.strip()


async def extract_single_invoice(
    file_bytes: bytes,
    mime_type: str,
    vendor_hint: str = None
) -> dict:
    """
    Extract invoice data using Gemini 2.5 Flash.
    For known vendors: injects few-shot examples from vendor memory.
    Gemini is ALWAYS called — we never skip it.
    """
    # Fetch vendor examples for few-shot prompting
    examples = []
    if vendor_hint:
        examples = await get_vendor_examples(vendor_hint)

    few_shot_section = build_few_shot_section(examples) if examples else ""
    prompt = get_extraction_prompt(few_shot_section=few_shot_section)

    file_part = _encode_file(file_bytes, mime_type)
    response = model.generate_content([{"text": prompt}, file_part])

    cleaned = _clean_json(response.text)
    try:
        extracted = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {response.text[:300]}")

    extracted["_few_shot_count"] = len(examples)  # Store for explainability
    return extracted


async def extract_po(file_bytes: bytes, mime_type: str) -> dict:
    """Extract structured data from a Purchase Order document."""
    prompt = get_po_extraction_prompt()
    file_part = _encode_file(file_bytes, mime_type)
    response = model.generate_content([{"text": prompt}, file_part])

    cleaned = _clean_json(response.text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"PO extraction failed: {e}")


async def extract_batch_invoices(files: List[tuple], vendor_hint: str = None) -> List[dict]:
    """Batch extraction — multiple invoices in one Gemini call."""
    count = len(files)

    examples = []
    if vendor_hint:
        examples = await get_vendor_examples(vendor_hint)

    few_shot_section = build_few_shot_section(examples) if examples else ""
    prompt = get_batch_extraction_prompt(count, few_shot_section=few_shot_section)

    parts = [{"text": prompt}]
    for file_bytes, mime_type in files:
        parts.append(_encode_file(file_bytes, mime_type))

    response = model.generate_content(parts)
    cleaned = _clean_json(response.text)

    try:
        results = json.loads(cleaned)
        if not isinstance(results, list):
            results = [results]
    except json.JSONDecodeError as e:
        raise ValueError(f"Batch extraction failed: {e}")

    return results
