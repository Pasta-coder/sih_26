"""
Immutable Audit Trail Service
──────────────────────────────
Every automated query, manual verification entry, AI output,
and officer override is logged here. Entries are NEVER updated
or deleted — this is append-only by design.

See PRD §12 for full audit trail requirements.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.audit import AuditLog, AuditEventType


def log_event(
    db: Session,
    event_type: AuditEventType,
    description: str,
    bidder_id: int | None = None,
    actor_id: int | None = None,
    payload: dict | None = None,
) -> AuditLog:
    """
    Append an immutable audit event.
    All fields are timestamped at call time.
    """
    entry = AuditLog(
        event_type=event_type,
        bidder_id=bidder_id,
        actor_id=actor_id,
        description=description,
        payload=payload,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_bidder_audit_trail(db: Session, bidder_id: int) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.bidder_id == bidder_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )


def get_full_audit_trail(db: Session, limit: int = 500) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
