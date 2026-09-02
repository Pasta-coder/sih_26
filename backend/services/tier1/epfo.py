"""
Tier 1 EPFO/ESIC Adapter
────────────────────────
Real path: Deepvue / AuthBridge reseller APIs.
Demo path: Mock.
"""
import httpx
from config import get_settings

settings = get_settings()

MOCK_EPFO_DATA = {
    "MHBAN0012345000": {
        "epfo_code": "MHBAN0012345000",
        "establishment_name": "RELIANCE INDUSTRIES LIMITED",
        "status": "Active",
        "employee_count_range": ">500",
        "coverage_start": "2017-07-01",
    },
    "MHBAN0054321000": {
        "epfo_code": "MHBAN0054321000",
        "establishment_name": "BHARAT PETROLEUM CORPORATION LIMITED",
        "status": "Active",
        "employee_count_range": ">500",
        "coverage_start": "2017-07-01",
    },
}


async def verify_epfo(epfo_code: str) -> dict:
    if not epfo_code:
        return {"error": "EPFO code not provided", "status": "not_provided"}

    if settings.use_real_tier1_apis and settings.epfo_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.epfo_api_base_url}/epfo/establishment/{epfo_code}",
                    headers={"Authorization": f"Bearer {settings.epfo_api_key}"},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "api_error"}

    return MOCK_EPFO_DATA.get(
        epfo_code.upper(),
        {"epfo_code": epfo_code, "status": "Not Found", "error": "Establishment not registered with EPFO"},
    )
