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
