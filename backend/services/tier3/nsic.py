"""
Tier 3 NSIC Mock Service
────────────────────────
No public verification portal or reseller API exists for NSIC.
This mock simulates an NSIC registry lookup.
"""

MOCK_NSIC_DATA = {
    "NSIC/MH/2021/001234": {
        "nsic_number": "NSIC/MH/2021/001234",
        "company_name": "RELIANCE INDUSTRIES LIMITED",
        "status": "Valid",
        "valid_upto": "2026-12-31",
        "category": "Raw Material",
    },
    "NSIC/DL/2020/005678": {
        "nsic_number": "NSIC/DL/2020/005678",
        "company_name": "TECH SOLUTIONS PVT LTD",
        "status": "Expired",
        "valid_upto": "2024-03-31",
        "category": "Engineering",
    },
}


def verify_nsic(nsic_number: str, company_name: str) -> dict:
    if not nsic_number:
        return {"status": "not_provided", "note": "NSIC registration number not submitted"}

    data = MOCK_NSIC_DATA.get(nsic_number.upper())
    if not data:
        return {"nsic_number": nsic_number, "status": "Not Found"}
    return data
