"""
Tier 3 Blacklist Mock Service
──────────────────────────────
Seeded from a static snapshot of published CVC/GeM debarred-vendor data.
In production: refresh manually when CVC/GeM publishes updated lists.
A blacklisting match → automatic score override to 0, Risk = Critical.
"""

# Static snapshot of debarred entities (seeded from published CVC data)
BLACKLISTED_ENTITIES: list[dict] = [
    {
        "entity_name": "BLACKLISTED VENTURES LTD",
        "pan": "AABCU9603R",
        "gstin": "07AABCU9603R1ZP",
        "debarment_reason": "Fraudulent bid documents submitted in GeM tender TN/2023/001",
        "debarred_by": "Central Vigilance Commission",
        "debarment_date": "2023-06-15",
        "debarment_end_date": "2026-06-14",
    },
    {
        "entity_name": "CORRUPT SUPPLIES PVT LTD",
        "pan": "AACCC1234D",
        "gstin": "19AACCC1234D1ZR",
        "debarment_reason": "Price cartelization in petroleum equipment tender",
        "debarred_by": "Ministry of Petroleum",
        "debarment_date": "2024-01-10",
        "debarment_end_date": "2027-01-09",
    },
]


def check_blacklist(company_name: str, pan: str = None, gstin: str = None) -> dict:
    """
    Check if entity matches any debarred vendor.
    Matches on: PAN (exact), GSTIN (exact), or company_name (case-insensitive).
    Returns match details or clean status.
    """
    pan = (pan or "").upper().strip()
    gstin = (gstin or "").upper().strip()
    name_lower = company_name.lower().strip()

    for entry in BLACKLISTED_ENTITIES:
        if (
            (pan and entry.get("pan", "").upper() == pan)
            or (gstin and entry.get("gstin", "").upper() == gstin)
            or entry["entity_name"].lower() == name_lower
        ):
            return {
                "blacklisted": True,
                "match": entry,
                "note": "AUTOMATIC DISQUALIFICATION: Entity found on CVC/GeM debarred vendor list.",
            }

    return {"blacklisted": False, "match": None}
