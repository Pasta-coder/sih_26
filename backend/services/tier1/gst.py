"""
Tier 1 GST Adapter
──────────────────
Real path: GSP-licensed reseller (Sandbox.co.in, Cashfree, WhiteBooks).
Demo path: Realistic mock response seeded from mock_services fixture data,
           toggled by USE_REAL_TIER1_APIS env flag.
"""
import httpx
from config import get_settings

settings = get_settings()

MOCK_GST_DATA = {
    "27AAACR5055K1ZK": {
        "gstin": "27AAACR5055K1ZK",
        "legal_name": "RELIANCE INDUSTRIES LIMITED",
        "trade_name": "RELIANCE",
        "status": "Active",
        "registration_date": "2017-07-01",
        "address": "3RD FLOOR, MAKER CHAMBERS IV, NARIMAN POINT, MUMBAI",
        "filing_status": {"last_6_months": 6, "missing": 0},
    },
    "27AADCB2230M1ZT": {
        "gstin": "27AADCB2230M1ZT",
        "legal_name": "BHARAT PETROLEUM CORPORATION LIMITED",
        "trade_name": "BPCL",
        "status": "Active",
        "registration_date": "2017-07-01",
        "address": "BHARAT BHAVAN, 4&6 CURRIMBHOY ROAD, BALLARD ESTATE, MUMBAI",
        "filing_status": {"last_6_months": 5, "missing": 1},
    },
    "29AAGCE4783F1ZY": {
        "gstin": "29AAGCE4783F1ZY",
        "legal_name": "EXPIRED COMPLIANCE PVT LTD",
        "trade_name": "EXPIRED CO",
        "status": "Cancelled",
        "registration_date": "2018-03-15",
        "cancellation_date": "2024-03-01",
        "filing_status": {"last_6_months": 2, "missing": 4},
    },
}


async def verify_gst(gstin: str) -> dict:
    """Verify GST registration and return structured compliance data."""
    if not gstin:
        return {"error": "GSTIN not provided", "status": "fail"}

    if settings.use_real_tier1_apis and settings.gst_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.gst_api_base_url}/v3/taxpayers/{gstin}",
                    headers={"x-api-key": settings.gst_api_key},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "api_error"}

    # Mock path
    data = MOCK_GST_DATA.get(gstin.upper())
    if not data:
        return {
            "gstin": gstin,
            "status": "Not Found",
            "error": "GSTIN not found in registry",
        }
    return data
