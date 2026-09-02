from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.audit import AuditLog
from models.user import User
from auth_utils import get_current_user, require_admin
from services.audit_log import get_bidder_audit_trail, get_full_audit_trail
from datetime import datetime

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
