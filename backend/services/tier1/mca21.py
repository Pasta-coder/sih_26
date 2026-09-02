"""
Tier 1 MCA21 Adapter
─────────────────────
Real path: AuthBridge / Surepass MCA21 company master data API.
Demo path: Mock.
"""
import httpx
from config import get_settings

settings = get_settings()

MOCK_MCA_DATA = {
    "L17110MH1973PLC019786": {
        "cin": "L17110MH1973PLC019786",
        "company_name": "RELIANCE INDUSTRIES LIMITED",
        "status": "Active",
        "incorporation_date": "1973-05-08",
        "company_type": "Public Limited",
        "registered_address": "MAKER CHAMBERS IV, NARIMAN POINT, MUMBAI",
    },
    "U23201MH1952GOI008956": {
        "cin": "U23201MH1952GOI008956",
        "company_name": "BHARAT PETROLEUM CORPORATION LIMITED",
        "status": "Active",
        "incorporation_date": "1952-11-03",
        "company_type": "Central Govt Company",
        "registered_address": "BHARAT BHAVAN, BALLARD ESTATE, MUMBAI",
    },
    "U74999DL2015PTC999999": {
        "cin": "U74999DL2015PTC999999",
        "company_name": "STRUCK OFF ENTITY PVT LTD",
        "status": "Strike-off",
        "incorporation_date": "2015-01-15",
        "company_type": "Private Limited",
        "registered_address": "DELHI",
    },
}


async def verify_mca(cin: str) -> dict:
    if not cin:
        return {"error": "CIN not provided", "status": "not_provided"}

    if settings.use_real_tier1_apis and settings.mca_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.mca_api_base_url}/company/{cin}",
                    headers={"x-api-key": settings.mca_api_key},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "api_error"}

    return MOCK_MCA_DATA.get(
        cin.upper(),
        {"cin": cin, "status": "Not Found", "error": "Company not found in MCA21"},
    )
