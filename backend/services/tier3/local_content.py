"""
Tier 3 Make in India Local-Content Mock
───────────────────────────────────────
Models the DPIIT/local-content self-declaration used to enforce the
"Make in India" requirement (PS item #5: 50% local-content threshold).

In production this would come from the bidder's Make in India declaration
cross-checked against verified procurement records; here it is a static
mock keyed by company name so the demo is deterministic.
"""

MOCK_LOCAL_CONTENT: dict[str, int] = {
    # ≥50% → meets threshold
    "RELIANCE INDUSTRIES LIMITED": 72,
    "BHARAT PETROLEUM CORPORATION LIMITED": 78,
    "PAN NAME MISMATCH CORP": 55,
    "MSME EXEMPTED MICRO PVT LTD": 66,
    "CHENNAI PETROCHEM INDUSTRIES": 62,
    "HINDUSTAN PETROLEUM CORPORATION LIMITED": 75,
    "GAIL INDIA LTD": 68,
    "PETRONET LNG LTD": 55,
    "MANGALORE REFINERY AND PETROCHEMICALS LTD": 58,
    "ADDRESS MISMATCH PVT LTD": 52,
    "ONGC LTD": 82,
    # <50% → below threshold (fails the Make in India requirement)
    "EXPIRED COMPLIANCE PVT LTD": 25,
    "BLACKLISTED VENTURES LTD": 10,
    "GUJARAT GAS COMPANY LTD": 45,
    "STRIKE OFF ENTITY PVT LTD": 15,
    "NO GSTIN VENDOR": 30,
    "CORRUPT SUPPLIES PVT LTD": 12,
    "NEAR EXPIRY CERTIFICATE PVT LTD": 40,
    "ADANI TOTAL GAS LTD": 40,
    "INVALID PAN FORMAT INC": 35,
    "NUMALIGARH REFINERY LTD": 35,
    "MISSING EPFO INDUSTRIAL PVT LTD": 48,
    "PARTIALLY COMPLIANT ENERGY LTD": 48,
    "STARTUP COMPLIANT TECH PVT LTD": 30,
    "THREE FAILURES CORP": 20,
}


def verify_local_content(company_name: str) -> dict:
    """Return the bidder's declared local-content percentage (mock)."""
    percent = MOCK_LOCAL_CONTENT.get((company_name or "").upper().strip())
    if percent is None:
        return {"local_content_percent": None, "status": "not_provided"}
    return {"local_content_percent": percent, "status": "ok"}