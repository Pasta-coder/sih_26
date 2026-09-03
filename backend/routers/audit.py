from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from models.bidder import Bidder
from models.compliance import ComplianceCheck, ComplianceOverride
from models.user import User
from auth_utils import get_current_user, require_admin
from services.audit_log import get_bidder_audit_trail, get_full_audit_trail
from services.pdf_export import generate_bidder_pdf

router = APIRouter()


@router.get("/bidder/{bidder_id}")
def get_bidder_audit(bidder_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Get full audit trail for a specific bidder."""
    entries = get_bidder_audit_trail(db, bidder_id)
    return [
        {
            "id": e.id,
            "event_type": e.event_type.value,
            "description": e.description,
            "actor_id": e.actor_id,
            "timestamp": e.timestamp.isoformat(),
            "payload": e.payload,
        }
        for e in entries
    ]


@router.get("/bidder/{bidder_id}/export-pdf")
def export_bidder_pdf(bidder_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Export full compliance audit trail as a professional PDF report."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    audit_entries = get_bidder_audit_trail(db, bidder_id)
    overrides = db.query(ComplianceOverride).filter(ComplianceOverride.bidder_id == bidder_id).all()

    bidder_data = {
        "company_name": bidder.company_name,
        "gstin": bidder.gstin,
        "pan": bidder.pan,
        "cin": bidder.cin,
        "compliance_score": bidder.compliance_score,
        "risk_level": bidder.risk_level,
        "recommendation": bidder.recommendation,
        "last_verified_at": bidder.last_verified_at.isoformat() if bidder.last_verified_at else None,
    }
    checks_data = [{"check_name": c.check_name, "check_tier": c.check_tier.value, "status": c.status.value, "detail": c.detail} for c in checks]
    audit_data = [{"event_type": e.event_type.value, "description": e.description, "timestamp": e.timestamp.isoformat()} for e in audit_entries]
    overrides_data = [{"check_name": o.check_name, "original_status": o.original_status, "overridden_status": o.overridden_status, "reason": o.reason, "officer_id": o.officer_id, "overridden_at": o.overridden_at.isoformat()} for o in overrides]

    pdf_bytes = generate_bidder_pdf(bidder_data, checks_data, audit_data, overrides_data)
    filename = f"compliance_audit_{bidder.company_name.replace(' ', '_')}_{bidder_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/all")
def get_all_audit(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Full system audit log — admin only."""
    entries = get_full_audit_trail(db)
    return [
        {
            "id": e.id,
            "event_type": e.event_type.value,
            "bidder_id": e.bidder_id,
            "actor_id": e.actor_id,
            "description": e.description,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in entries
    ]
