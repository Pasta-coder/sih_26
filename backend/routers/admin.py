from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.tender import Tender
from models.user import User
from auth_utils import require_admin

router = APIRouter()


@router.get("/mock-toggle/{tender_id}")
def get_rule_toggles(tender_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Get current rule toggles for a tender (admin)."""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        return {"error": "Tender not found"}
    return {"tender_id": tender_id, "rule_toggles": tender.rule_toggles}


@router.patch("/mock-toggle/{tender_id}")
def update_rule_toggles(
    tender_id: int,
    toggles: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Update tender rule toggles (admin only).
    e.g. {"epfo_required": false, "msme_exemption": true, "bis_required": true}
    This triggers the 'wow moment': toggle a bidder's mock status and
    re-verify to see real-time score/risk update.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        return {"error": "Tender not found"}
    # Copy before mutating: updating the stored dict in place is invisible to
    # SQLAlchemy's change tracking, so the toggle never reached the database.
    current = dict(tender.rule_toggles or {})
    current.update(toggles)
    tender.rule_toggles = current
    db.commit()
    db.refresh(tender)
    return {"message": "Toggles updated", "rule_toggles": tender.rule_toggles}
