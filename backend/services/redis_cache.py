import redis.asyncio as aioredis
import json
import config

_redis_client = None
_redis_available = None  # None = untested, True = ok, False = broken


async def get_redis():
    """
    Returns Redis client if available, None if Redis is misconfigured or down.
    Redis is optional — caching/status features degrade gracefully without it.
    """
    global _redis_client, _redis_available

    # Already confirmed broken — don't retry every request
    if _redis_available is False:
        return None

    if _redis_client is None:
        if not config.REDIS_URL:
            print("⚠️  REDIS_URL not set — Redis features disabled")
            _redis_available = False
            return None

        # Validate URL scheme before trying to connect
        if not any(config.REDIS_URL.startswith(s) for s in ("redis://", "rediss://", "unix://")):
            print(
                f"⚠️  Invalid REDIS_URL format: '{config.REDIS_URL}'\n"
                f"    Must start with redis://, rediss://, or unix://\n"
                f"    Example: redis://default:password@host:port\n"
                f"    Redis features disabled — fix .env to enable caching."
            )
            _redis_available = False
            return None

        try:
            _redis_client = aioredis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            # Ping to confirm connection works
            await _redis_client.ping()
            _redis_available = True
            print("✅ Redis connected")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}\n    Redis features disabled.")
            _redis_client = None
            _redis_available = False
            return None

    return _redis_client


# ─── Vendor Schema Cache ──────────────────────────────────
async def get_vendor_schema(vendor_name: str) -> dict | None:
    r = await get_redis()
    if not r:
        return None
    try:
        key = f"vendor_schema:{vendor_name.lower().strip().replace(' ', '_')}"
        cached = await r.get(key)
        return json.loads(cached) if cached else None
    except Exception:
        return None


async def set_vendor_schema(vendor_name: str, schema: dict):
    r = await get_redis()
    if not r:
        return
    try:
        key = f"vendor_schema:{vendor_name.lower().strip().replace(' ', '_')}"
        await r.set(key, json.dumps(schema), ex=config.REDIS_VENDOR_CACHE_TTL)
    except Exception:
        pass


async def invalidate_vendor_schema(vendor_name: str):
    r = await get_redis()
    if not r:
        return
    try:
        key = f"vendor_schema:{vendor_name.lower().strip().replace(' ', '_')}"
        await r.delete(key)
    except Exception:
        pass


# ─── Processing Status Cache ──────────────────────────────
async def set_processing_status(invoice_id: str, status: str):
    r = await get_redis()
    if not r:
        return  # Graceful no-op — frontend will poll MongoDB directly
    try:
        await r.set(f"processing:{invoice_id}", status, ex=3600)
    except Exception:
        pass


async def get_processing_status(invoice_id: str) -> str | None:
    r = await get_redis()
    if not r:
        return None
    try:
        return await r.get(f"processing:{invoice_id}")
    except Exception:
        return None