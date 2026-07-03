"""
Seed Script — Run once to populate GL codes in MongoDB with embeddings.
Usage: python scripts/seed_gl_codes.py

Creates 50 common GL codes used in Indian accounting (Tally-compatible).
After seeding, create the Atlas Vector Search index manually:
  Collection: gl_codes
  Field: embedding
  Dimensions: 3072
  Similarity: cosine
  Index name: gl_code_vector_index
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
from pymongo import MongoClient
import config
import time

genai.configure(api_key=config.GEMINI_API_KEY)

GL_CODES = [
    # ─── Assets ──────────────────────────────────────────
    {"code": "1001", "description": "Cash in Hand", "category": "Current Assets", "keywords": ["cash", "petty cash", "hand cash"]},
    {"code": "1002", "description": "Bank Account", "category": "Current Assets", "keywords": ["bank", "savings", "current account", "HDFC", "SBI", "ICICI"]},
    {"code": "1003", "description": "Accounts Receivable", "category": "Current Assets", "keywords": ["receivable", "debtor", "customer outstanding", "party receivable"]},
    {"code": "1004", "description": "Inventory / Stock", "category": "Current Assets", "keywords": ["stock", "inventory", "goods", "raw material", "finished goods"]},
    {"code": "1005", "description": "Prepaid Expenses", "category": "Current Assets", "keywords": ["prepaid", "advance payment", "advance rent", "prepaid insurance"]},
    {"code": "1006", "description": "Security Deposit", "category": "Non-Current Assets", "keywords": ["security deposit", "refundable deposit", "EMD", "earnest money"]},
    {"code": "1007", "description": "Fixed Assets - Machinery", "category": "Non-Current Assets", "keywords": ["machinery", "equipment", "plant", "machine", "lathe", "CNC"]},
    {"code": "1008", "description": "Fixed Assets - Computers & IT", "category": "Non-Current Assets", "keywords": ["computer", "laptop", "server", "hardware", "IT equipment"]},
    {"code": "1009", "description": "Fixed Assets - Furniture & Fixtures", "category": "Non-Current Assets", "keywords": ["furniture", "chair", "table", "fixture", "office furniture"]},
    {"code": "1010", "description": "Fixed Assets - Vehicles", "category": "Non-Current Assets", "keywords": ["vehicle", "car", "truck", "bike", "van", "transport"]},

    # ─── Liabilities ─────────────────────────────────────
    {"code": "2001", "description": "Accounts Payable", "category": "Current Liabilities", "keywords": ["payable", "creditor", "supplier outstanding", "vendor payable"]},
    {"code": "2002", "description": "GST Payable", "category": "Current Liabilities", "keywords": ["GST payable", "output GST", "tax payable", "IGST", "CGST", "SGST payable"]},
    {"code": "2003", "description": "TDS Payable", "category": "Current Liabilities", "keywords": ["TDS", "tax deducted at source", "TDS payable"]},
    {"code": "2004", "description": "Salary Payable", "category": "Current Liabilities", "keywords": ["salary payable", "wages payable", "staff due"]},
    {"code": "2005", "description": "Loans & Borrowings", "category": "Non-Current Liabilities", "keywords": ["loan", "borrowing", "term loan", "bank loan", "EMI"]},

    # ─── Revenue ──────────────────────────────────────────
    {"code": "3001", "description": "Sales Revenue", "category": "Revenue", "keywords": ["sales", "revenue", "turnover", "income from sales", "product sale"]},
    {"code": "3002", "description": "Service Revenue", "category": "Revenue", "keywords": ["service income", "consulting fee", "professional fee", "service charges"]},
    {"code": "3003", "description": "Interest Income", "category": "Revenue", "keywords": ["interest income", "bank interest", "FD interest", "investment income"]},
    {"code": "3004", "description": "Other Income", "category": "Revenue", "keywords": ["other income", "miscellaneous income", "sundry income"]},

    # ─── Cost of Goods Sold ───────────────────────────────
    {"code": "4001", "description": "Raw Material Purchases", "category": "COGS", "keywords": ["raw material", "purchase", "material cost", "input material"]},
    {"code": "4002", "description": "Packing Material", "category": "COGS", "keywords": ["packing", "packaging", "carton", "box", "wrapping"]},
    {"code": "4003", "description": "Freight Inward", "category": "COGS", "keywords": ["freight inward", "inbound logistics", "shipping inward", "import freight"]},
    {"code": "4004", "description": "Manufacturing / Job Work Charges", "category": "COGS", "keywords": ["job work", "manufacturing charges", "processing charges", "labour charges"]},

    # ─── Operating Expenses ───────────────────────────────
    {"code": "5001", "description": "Salaries & Wages", "category": "Operating Expenses", "keywords": ["salary", "wages", "payroll", "staff salary", "employee pay"]},
    {"code": "5002", "description": "Rent Expense", "category": "Operating Expenses", "keywords": ["rent", "office rent", "warehouse rent", "shop rent", "lease"]},
    {"code": "5003", "description": "Electricity & Utilities", "category": "Operating Expenses", "keywords": ["electricity", "power bill", "utility", "water bill", "EB bill", "MSEDCL"]},
    {"code": "5004", "description": "Internet & Telephone", "category": "Operating Expenses", "keywords": ["internet", "broadband", "telephone", "mobile bill", "Jio", "Airtel", "BSNL", "communication"]},
    {"code": "5005", "description": "Office Supplies & Stationery", "category": "Operating Expenses", "keywords": ["stationery", "office supplies", "pen", "paper", "printer ink", "toner", "notebook"]},
    {"code": "5006", "description": "Travel & Conveyance", "category": "Operating Expenses", "keywords": ["travel", "conveyance", "cab", "Ola", "Uber", "auto", "fuel", "petrol", "diesel", "train ticket", "flight", "bus"]},
    {"code": "5007", "description": "Repairs & Maintenance", "category": "Operating Expenses", "keywords": ["repair", "maintenance", "AMC", "service contract", "fix", "servicing"]},
    {"code": "5008", "description": "Professional & Legal Fees", "category": "Operating Expenses", "keywords": ["professional fee", "legal fee", "advocate", "CA fee", "audit fee", "consultant"]},
    {"code": "5009", "description": "Advertisement & Marketing", "category": "Operating Expenses", "keywords": ["advertisement", "marketing", "promotion", "branding", "digital marketing", "social media", "ads", "Google ads"]},
    {"code": "5010", "description": "Software & Subscriptions", "category": "Operating Expenses", "keywords": ["software", "subscription", "SaaS", "license", "AWS", "Azure", "Google Cloud", "Microsoft", "Adobe", "Tally", "Zoho"]},
    {"code": "5011", "description": "Insurance Premium", "category": "Operating Expenses", "keywords": ["insurance", "premium", "policy", "health insurance", "vehicle insurance", "fire insurance"]},
    {"code": "5012", "description": "Bank Charges & Fees", "category": "Operating Expenses", "keywords": ["bank charges", "bank fee", "service charge", "processing fee", "transaction fee"]},
    {"code": "5013", "description": "Freight & Courier Outward", "category": "Operating Expenses", "keywords": ["freight outward", "courier", "delivery", "logistics", "Delhivery", "BlueDart", "FedEx", "DHL", "transport charges"]},
    {"code": "5014", "description": "Housekeeping & Security", "category": "Operating Expenses", "keywords": ["housekeeping", "cleaning", "security", "guard", "sanitation", "janitorial"]},
    {"code": "5015", "description": "Staff Welfare & Canteen", "category": "Operating Expenses", "keywords": ["staff welfare", "canteen", "food", "meals", "refreshments", "employee welfare"]},
    {"code": "5016", "description": "Printing & Stationery", "category": "Operating Expenses", "keywords": ["printing", "letterhead", "visiting card", "brochure", "pamphlet"]},
    {"code": "5017", "description": "Depreciation", "category": "Operating Expenses", "keywords": ["depreciation", "amortization", "asset write-off"]},
    {"code": "5018", "description": "Research & Development", "category": "Operating Expenses", "keywords": ["R&D", "research", "development", "prototype", "innovation", "lab expense"]},

    # ─── Tax ──────────────────────────────────────────────
    {"code": "6001", "description": "GST Input Credit (CGST)", "category": "Tax", "keywords": ["CGST", "central GST", "input tax credit", "ITC CGST"]},
    {"code": "6002", "description": "GST Input Credit (SGST)", "category": "Tax", "keywords": ["SGST", "state GST", "input tax credit", "ITC SGST"]},
    {"code": "6003", "description": "GST Input Credit (IGST)", "category": "Tax", "keywords": ["IGST", "integrated GST", "import GST", "interstate tax", "ITC IGST"]},
    {"code": "6004", "description": "Income Tax", "category": "Tax", "keywords": ["income tax", "advance tax", "corporate tax", "self assessment tax"]},
    {"code": "6005", "description": "TDS Receivable", "category": "Tax", "keywords": ["TDS receivable", "26AS", "tax credit", "TDS certificate"]},

    # ─── Miscellaneous ────────────────────────────────────
    {"code": "9001", "description": "Suspense Account", "category": "Miscellaneous", "keywords": ["suspense", "unclear", "pending classification", "unidentified"]},
    {"code": "9002", "description": "Miscellaneous Expenses", "category": "Miscellaneous", "keywords": ["miscellaneous", "sundry", "other expenses", "incidental"]},
    {"code": "9999", "description": "Unclassified", "category": "Miscellaneous", "keywords": ["unclassified", "unknown", "other"]},
]


def embed_text(text: str) -> list:
    """Generate embedding using Gemini gemini-embedding-001 (3072 dims)."""
    result = genai.embed_content(
        model=config.EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]


def seed_gl_codes():
    print("🌱 Seeding GL codes into MongoDB...")
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    col = db[config.GL_CODES_COLLECTION]

    # Clear existing
    col.delete_many({})
    print(f"🗑️  Cleared existing GL codes")

    seeded = 0
    for gl in GL_CODES:
        # Build rich text for embedding
        embed_text_content = (
            f"{gl['description']} {gl['category']} "
            f"{' '.join(gl['keywords'])}"
        )

        print(f"  Embedding: {gl['code']} - {gl['description']}...")
        embedding = embed_text(embed_text_content)

        doc = {
            "code": gl["code"],
            "description": gl["description"],
            "category": gl["category"],
            "keywords": gl["keywords"],
            "embedding": embedding
        }

        col.insert_one(doc)
        seeded += 1

        # Rate limit: gemini-embedding-001 free tier = 100 req/min
        time.sleep(0.7)

    print(f"\n✅ Seeded {seeded} GL codes successfully!")
    print("\n⚠️  NEXT STEP: Create Vector Search Index in MongoDB Atlas UI:")
    print("   Collection: gl_codes")
    print("   Field: embedding")
    print("   Dimensions: 3072")
    print("   Similarity: cosine")
    print("   Index name: gl_code_vector_index")

    client.close()


if __name__ == "__main__":
    seed_gl_codes()
