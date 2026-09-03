"""
Tier 3 OEM Authorization Mock
──────────────────────────────
OEM authorization is a private B2B letter from a manufacturer to a reseller.
No government database exists to query. 
Verification = document upload + AI field-extraction consistency check only.
"""

OEM_KNOWN_AUTHORIZATIONS = {
    "RELIANCE INDUSTRIES LIMITED": {
        "oem_name": "PETROTECH EQUIPMENT CORP",
        "authorized_distributor": "RELIANCE INDUSTRIES LIMITED",
        "product_category": "Petroleum Processing Equipment",
        "valid_upto": "2027-06-30",
        "authorization_number": "PEC/AUTH/2025/001",
    },
}


def verify_oem(company_name: str, oem_letter_fields: dict = None) -> dict:
    """
    Check extracted OEM letter fields for consistency.
    No portal to verify against — document-only check.
    """
    if not oem_letter_fields:
        return {
            "status": "not_provided",
            "note": "OEM authorization letter not uploaded. Required if reselling OEM products.",
        }

    # Basic consistency: extracted distributor name should match bidder company name
    extracted_distributor = oem_letter_fields.get("authorized_distributor", "")
    if company_name.upper().strip() not in extracted_distributor.upper():
        return {
            "status": "inconsistency",
            "note": f"Extracted distributor '{extracted_distributor}' does not match bidder '{company_name}'. Manual review required.",
        }

    return {
        "status": "document_verified",
        "note": "OEM authorization letter fields extracted and consistent. No portal verification available by design.",
        "extracted_fields": oem_letter_fields,
    }
