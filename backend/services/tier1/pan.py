"""
Tier 1 PAN Adapter
──────────────────
Real path: PAN verification reseller (Sandbox.co.in /kyc/pan).
Demo path: Realistic mock.
"""
import httpx
from config import get_settings

settings = get_settings()

MOCK_PAN_DATA = {
    "AAACR5055K": {"pan": "AAACR5055K", "name": "RELIANCE INDUSTRIES LIMITED", "status": "Valid", "type": "Company"},
    "AADCB2230M": {"pan": "AADCB2230M", "name": "BHARAT PETROLEUM CORPORATION LIMITED", "status": "Valid", "type": "Company"},
    "AAGCE4783F": {"pan": "AAGCE4783F", "name": "EXPIRED COMPLIANCE PVT LTD", "status": "Valid", "type": "Company"},
    "AABCU9603R": {"pan": "AABCU9603R", "name": "BLACKLISTED VENTURES LTD", "status": "Valid", "type": "Company"},
    "ZZZZZ9999Z": {"pan": "ZZZZZ9999Z", "name": "INVALID ENTITY", "status": "Invalid", "type": None},
}


async def verify_pan(pan: str) -> dict:
    """Verify PAN validity and registered name."""
    if not pan:
        return {"error": "PAN not provided", "status": "fail"}

    pan = pan.upper().strip()

    # Format validation (AAAAA9999A pattern)
    import re
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        return {"pan": pan, "status": "Invalid", "error": "PAN format invalid"}

    if settings.use_real_tier1_apis and settings.pan_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{settings.pan_api_base_url}/verify",
                    json={"pan": pan},
                    headers={"x-api-key": settings.pan_api_key},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "api_error"}

    return MOCK_PAN_DATA.get(pan, {"pan": pan, "status": "Not Found", "error": "PAN not in registry"})
