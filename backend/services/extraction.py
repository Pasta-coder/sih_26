"""
NuExtract-based Field Extraction
──────────────────────────────────
Uses regex + pattern matching to extract structured fields from OCR text.
In production: replace with numind/NuExtract-3.8B (grounded extraction model).

Grounded extraction guarantee: output only contains text present in the source.
Cannot hallucinate a PAN, GSTIN, date, or registration number — this is the
core audit-safety guarantee of the pipeline.

Document types supported:
  - pan_card
  - gst_certificate
  - udyam_certificate
  - epfo_certificate
  - itr_v_acknowledgment
  - oem_authorization_letter
"""
import re


# ── Regex patterns for known Indian government document IDs ────────────────
PATTERNS = {
    "gstin": r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b",
    "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "udyam": r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b",
    "cin": r"\b[LUu][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b",
    "epfo_code": r"\b[A-Z]{2}[A-Z]{3}[0-9]{7}[0-9]{3}\b",
    "ack_number": r"\b[0-9]{15}\b",  # ITR-V acknowledgment number
    "date": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
}

# ── Document type schemas ──────────────────────────────────────────────────
SCHEMAS = {
    "pan_card": ["pan", "name", "date_of_birth", "father_name"],
    "gst_certificate": ["gstin", "legal_name", "trade_name", "registration_date", "address"],
    "udyam_certificate": ["udyam", "company_name", "registration_date", "enterprise_type"],
    "epfo_certificate": ["epfo_code", "establishment_name", "registration_date"],
    "itr_v_acknowledgment": ["pan", "ack_number", "assessment_year", "name"],
    "oem_authorization_letter": ["oem_name", "authorized_distributor", "product_category", "valid_upto", "authorization_number"],
}


def _extract_ids(text: str) -> dict:
    """Extract all known ID patterns from text."""
    found = {}
    for field, pattern in PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found[field] = matches[0]  # Take first match
    return found


def _extract_name_lines(text: str) -> list[str]:
    """Extract capitalized name-like lines from OCR text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name_lines = [l for l in lines if re.match(r"^[A-Z][A-Z\s&\.]{5,50}$", l) and len(l.split()) >= 2]
    return name_lines[:3]


def extract_fields(ocr_text: str, doc_type: str) -> dict:
    """
    Extract structured fields from OCR text for a given document type.
    
    Args:
        ocr_text: Raw text from OCR pipeline
        doc_type: One of the SCHEMAS keys
    
    Returns:
        Dict of extracted fields. Only fields found in the text are included.
        This is the grounded-extraction guarantee.
    """
    if not ocr_text or not ocr_text.strip():
        return {"error": "No text to extract from"}

    ids = _extract_ids(ocr_text)
    name_lines = _extract_name_lines(ocr_text)
    schema = SCHEMAS.get(doc_type, [])

    extracted = {"doc_type": doc_type, "raw_ids_found": ids}

    # Map extracted IDs to document schema
    for field in schema:
        if field in ids:
            extracted[field] = ids[field]
        elif field in ("name", "legal_name", "company_name", "establishment_name",
                       "authorized_distributor", "oem_name") and name_lines:
            extracted[field] = name_lines[0] if name_lines else None

    # Extract dates from text
    dates = re.findall(PATTERNS["date"], ocr_text)
    if dates:
        extracted["dates_found"] = dates

    extracted["_grounded"] = True
    extracted["_note"] = "Fields extracted only from source document text. No hallucination possible."

    return extracted
