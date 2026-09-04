import os, shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from models.bidder import Bidder, BidderDocument
from models.user import User
from models.audit import AuditEventType
from auth_utils import get_current_user
from config import get_settings
from services.ocr import extract_text
from services.extraction import extract_fields
from services.rules_engine import _name_match
from services import audit_log as audit_svc

settings = get_settings()
router = APIRouter()

ALLOWED_TYPES = {
    "pan_card", "gst_certificate", "udyam_certificate",
    "epfo_certificate", "itr_v_acknowledgment", "oem_authorization_letter",
}


@router.post("/upload/{bidder_id}")
async def upload_document(
    bidder_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a compliance document for a bidder.
    Pipeline: Save → OCR → Field Extraction → Store → Audit Log
    """
    if doc_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"doc_type must be one of: {', '.join(ALLOWED_TYPES)}")

    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    # M3: MAX_UPLOAD_SIZE_MB was configured but never enforced.
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_size_mb} MB upload limit.",
        )

    # Save file
    upload_dir = os.path.join(settings.upload_dir, str(bidder_id))
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{doc_type}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # OCR pipeline
    ocr_result = extract_text(file_path)
    ocr_text = ocr_result["text"]

    # Field extraction
    extracted = extract_fields(ocr_text, doc_type)

    # Persist document record
    doc = BidderDocument(
        bidder_id=bidder_id,
        doc_type=doc_type,
        filename=safe_name,
        filepath=file_path,
        ocr_text=ocr_text,
        extracted_fields=extracted,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Audit: document upload
    audit_svc.log_event(
        db,
        AuditEventType.document_upload,
        f"Document uploaded: {doc_type} for bidder {bidder.company_name}",
        bidder_id=bidder_id,
        actor_id=current_user.id,
        payload={"doc_type": doc_type, "filename": safe_name, "ocr_method": ocr_result["method"]},
    )

    # Audit: field extraction
    audit_svc.log_event(
        db,
        AuditEventType.document_extraction,
        f"Fields extracted from {doc_type}: {list(extracted.keys())}",
        bidder_id=bidder_id,
        actor_id=current_user.id,
        payload={"extracted_fields": extracted, "confidence": ocr_result.get("confidence")},
    )

    return {
        "document_id": doc.id,
        "doc_type": doc_type,
        "ocr_method": ocr_result["method"],
        "ocr_confidence": ocr_result["confidence"],
        "extracted_fields": extracted,
    }


@router.get("/{bidder_id}")
def get_documents(bidder_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Get all uploaded documents for a bidder."""
    docs = db.query(BidderDocument).filter(BidderDocument.bidder_id == bidder_id).all()
    return [
        {
            "id": d.id,
            "doc_type": d.doc_type,
            "filename": d.filename,
            "extracted_fields": d.extracted_fields,
            "uploaded_at": d.uploaded_at.isoformat(),
        }
        for d in docs
    ]


# Which extracted raw-id field maps to which bidder record column for a doc type.
# (M3) Advisory-only cross-check — registry rules stay authoritative.
_DOC_RECORD_FIELDS = {
    "pan_card": [("pan", "pan")],
    "gst_certificate": [("gstin", "gstin")],
    "udyam_certificate": [("udyam", "udyam_number")],
    "epfo_certificate": [("epfo_code", "epfo_code")],
    "itr_v_acknowledgment": [("pan", "pan")],
    "oem_authorization_letter": [],
}

# Extracted-name key per doc type for the fuzzy name cross-check.
_DOC_NAME_FIELD = {
    "pan_card": "name",
    "gst_certificate": "legal_name",
    "udyam_certificate": "company_name",
    "epfo_certificate": "establishment_name",
    "itr_v_acknowledgment": "name",
}


@router.get("/consistency/{bidder_id}")
def document_consistency(
    bidder_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    (M3) Advisory cross-check of extracted document fields against the bidder
    record (PRD §5). Compares each doc's extracted PAN/GSTIN/Udyam/EPFO codes
    and registered names against the bidder's declared identifiers. This is a
    decision-support panel only — it never auto-fails a bidder.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    docs = db.query(BidderDocument).filter(BidderDocument.bidder_id == bidder_id).all()
    report = []
    for d in docs:
        extracted = d.extracted_fields or {}
        raw_ids = extracted.get("raw_ids_found", {})
        matches = []
        for extract_key, record_attr in _DOC_RECORD_FIELDS.get(d.doc_type, []):
            record_val = getattr(bidder, record_attr, None)
            extracted_val = raw_ids.get(extract_key)
            if not record_val:
                matches.append({"field": extract_key, "extracted": extracted_val,
                                "record": None, "status": "no_record"})
            elif not extracted_val:
                matches.append({"field": extract_key, "extracted": None,
                                "record": record_val, "status": "no_extract"})
            elif str(extracted_val).upper() == str(record_val).upper():
                matches.append({"field": extract_key, "extracted": extracted_val,
                                "record": record_val, "status": "matched"})
            else:
                matches.append({"field": extract_key, "extracted": extracted_val,
                                "record": record_val, "status": "mismatch"})

        # Fuzzy name cross-check (advisory)
        name_key = _DOC_NAME_FIELD.get(d.doc_type)
        extracted_name = extracted.get(name_key) if name_key else None
        if extracted_name and bidder.company_name:
            if _name_match(str(extracted_name), bidder.company_name):
                matches.append({"field": "name", "extracted": extracted_name,
                                "record": bidder.company_name, "status": "matched"})
            else:
                matches.append({"field": "name", "extracted": extracted_name,
                                "record": bidder.company_name, "status": "mismatch"})

        report.append({
            "document_id": d.id,
            "doc_type": d.doc_type,
            "filename": d.filename,
            "extracted": extracted,
            "checks": matches,
        })

    return {"bidder_id": bidder.id, "company_name": bidder.company_name, "documents": report}
