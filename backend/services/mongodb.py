from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import config

_async_client: AsyncIOMotorClient = None
_async_db = None


def get_async_db():
    global _async_client, _async_db
    if _async_client is None:
        _async_client = AsyncIOMotorClient(config.MONGODB_URI)
        _async_db = _async_client[config.MONGODB_DB_NAME]
    return _async_db


def get_sync_db():
    client = MongoClient(config.MONGODB_URI)
    return client[config.MONGODB_DB_NAME]


def invoices_col():
    return get_async_db()[config.INVOICES_COLLECTION]

def gl_codes_col():
    return get_async_db()[config.GL_CODES_COLLECTION]

def corrections_col():
    return get_async_db()[config.CORRECTIONS_COLLECTION]

def vendor_prompts_col():
    return get_async_db()[config.VENDOR_PROMPTS_COLLECTION]

def vendor_memory_col():
    return get_async_db()[config.VENDOR_MEMORY_COLLECTION]

def po_col():
    return get_async_db()[config.PO_COLLECTION]

def explainability_col():
    return get_async_db()[config.EXPLAINABILITY_COLLECTION]


async def create_indexes():
    db = get_async_db()

    await db[config.INVOICES_COLLECTION].create_index("status")
    await db[config.INVOICES_COLLECTION].create_index("created_at")
    await db[config.INVOICES_COLLECTION].create_index(
        [("extracted_data.invoice_number", 1), ("extracted_data.vendor_name", 1)]
    )
    await db[config.PO_COLLECTION].create_index("po_number")
    await db[config.PO_COLLECTION].create_index("vendor_name")
    await db[config.VENDOR_MEMORY_COLLECTION].create_index("vendor_key", unique=True)

    print("✅ MongoDB indexes created")
