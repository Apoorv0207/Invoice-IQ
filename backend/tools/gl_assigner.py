"""
GL Code Assigner — RAG-based semantic GL code assignment.
Uses gemini-embedding-001 to embed line item descriptions (3072 dims),
then searches MongoDB Atlas Vector Search for closest GL code.
"""

import google.generativeai as genai
import config
from services.mongodb import gl_codes_col

genai.configure(api_key=config.GEMINI_API_KEY)


async def embed_text(text: str) -> list:
    """Generate embedding for a text using gemini-embedding-001 (3072 dims)."""
    result = genai.embed_content(
        model=config.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return result["embedding"]


async def assign_gl_code(line_item_description: str) -> dict:
    """
    Semantically assigns a GL code to a line item description.
    Uses MongoDB Atlas Vector Search (cosine similarity).
    
    Returns:
        {
            "gl_code": str,
            "gl_description": str,
            "confidence": float (0-100),
            "category": str
        }
    """
    col = gl_codes_col()

    # Generate embedding for the line item
    query_embedding = await embed_text(line_item_description)

    # Atlas Vector Search query
    # NOTE: You must create the vector search index in Atlas UI first
    # Index name: gl_code_vector_index
    # Field: embedding, Dimensions: 3072, Similarity: cosine
    pipeline = [
        {
            "$vectorSearch": {
                "index": "gl_code_vector_index",
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": 20,
                "limit": 1
            }
        },
        {
            "$project": {
                "code": 1,
                "description": 1,
                "category": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = await col.aggregate(pipeline).to_list(1)

    if not results:
        return {
            "gl_code": "9999",
            "gl_description": "Unclassified",
            "confidence": 0,
            "category": "Unknown"
        }

    best = results[0]
    # Convert cosine similarity score (0-1) to confidence percentage
    confidence = round(best.get("score", 0) * 100, 1)

    return {
        "gl_code": best.get("code"),
        "gl_description": best.get("description"),
        "confidence": confidence,
        "category": best.get("category")
    }


async def assign_gl_codes_batch(line_items: list) -> list:
    """
    Assign GL codes to all line items in an invoice.
    Returns line_items with gl_code, gl_description, gl_confidence added.
    """
    enriched = []
    for item in line_items:
        description = item.get("description", "")
        if description:
            gl_result = await assign_gl_code(description)
            enriched.append({
                **item,
                "gl_code": gl_result["gl_code"],
                "gl_description": gl_result["gl_description"],
                "gl_confidence": gl_result["confidence"]
            })
        else:
            enriched.append(item)
    return enriched
