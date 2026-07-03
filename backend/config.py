import os
from dotenv import load_dotenv

load_dotenv()

# ─── Gemini ───────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# ─── MongoDB ──────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "invoiceiq")

# Collections
INVOICES_COLLECTION = "invoices"
GL_CODES_COLLECTION = "gl_codes"
CORRECTIONS_COLLECTION = "corrections"
VENDOR_PROMPTS_COLLECTION = "vendor_prompts"
VENDOR_MEMORY_COLLECTION = "vendor_memory"
PO_COLLECTION = "purchase_orders"
EXPLAINABILITY_COLLECTION = "explainability"
ANALYTICS_COLLECTION = "analytics"

# ─── Redis ────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL")
REDIS_VENDOR_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days

# ─── Confidence Thresholds ───────────────────────────────
AUTO_APPROVE_THRESHOLD = 95
FLAG_THRESHOLD = 75

# ─── PO Matching ─────────────────────────────────────────
PO_MATCH_TOLERANCE_PERCENT = 5.0   # 5% variance allowed before flagging

# ─── Vendor Memory ───────────────────────────────────────
VENDOR_MEMORY_MAX_EXAMPLES = 5     # Max few-shot examples per vendor

# ─── App ──────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
