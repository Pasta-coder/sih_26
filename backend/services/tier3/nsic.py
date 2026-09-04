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
    "NSIC/MH/2020/004321": {
        "nsic_number": "NSIC/MH/2020/004321",
        "company_name": "BHARAT PETROLEUM CORPORATION LIMITED",
        "status": "Valid",
        "valid_upto": "2027-06-30",
        "category": "Engineering",
    },
    "NSIC/GJ/2019/008765": {
        "nsic_number": "NSIC/GJ/2019/008765",
        "company_name": "GUJARAT GAS COMPANY LTD",
        "status": "Valid",
        "valid_upto": "2025-11-15",
        "category": "Engineering",
    },
    "NSIC/DL/2020/005678": {
        "nsic_number": "NSIC/DL/2020/005678",
        "company_name": "EXPIRED COMPLIANCE PVT LTD",
        "status": "Expired",
        "valid_upto": "2024-03-31",
        "category": "Engineering",
    },
    "NSIC/TN/2021/009999": {
        "nsic_number": "NSIC/TN/2021/009999",
        "company_name": "CHENNAI PETROCHEM INDUSTRIES",
        "status": "Expired",
        "valid_upto": "2025-01-10",
        "category": "Raw Material",
    },
}


def verify_nsic(nsic_number: str, company_name: str) -> dict:
    if not nsic_number:
        return {"status": "not_provided", "note": "NSIC registration number not submitted"}

    data = MOCK_NSIC_DATA.get(nsic_number.upper())
    if not data:
        return {"nsic_number": nsic_number, "status": "Not Found"}
    return data