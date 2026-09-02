"""
Tier 3 DigiLocker Mock Service
───────────────────────────────
Real DigiLocker requires the document owner's live Aadhaar-OTP consent.
Cannot function for synthetic dummy bidders — this is a consent-flow
blocker, not an API-access problem.
This mock simulates document issuance for seeded dummy bidders.
"""

MOCK_DIGILOCKER_DOCS = {
    "AAACR5055K": {
        "pan_card": {"issued": True, "number": "AAACR5055K", "name": "RELIANCE INDUSTRIES LIMITED"},
        "gst_certificate": {"issued": True, "gstin": "27AAACR5055K1ZK"},
    },
    "AADCB2230M": {
        "pan_card": {"issued": True, "number": "AADCB2230M", "name": "BHARAT PETROLEUM CORPORATION LIMITED"},
        "gst_certificate": {"issued": True, "gstin": "27AADCB2230M1ZT"},
    },
}


def fetch_digilocker_doc(pan: str, doc_type: str) -> dict:
    """Simulate DigiLocker document pull for seeded bidders."""
    bidder_docs = MOCK_DIGILOCKER_DOCS.get(pan.upper())
    if not bidder_docs:
        return {"status": "not_found", "note": "No DigiLocker documents found for this PAN (mock)"}
    doc = bidder_docs.get(doc_type)
    if not doc:
        return {"status": "not_found", "doc_type": doc_type}
    return {"status": "found", "doc_type": doc_type, "data": doc}
