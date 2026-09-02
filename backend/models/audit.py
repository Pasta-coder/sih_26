from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class AuditEventType(str, enum.Enum):
    tier1_query = "tier1_query"
    tier2_manual_verify = "tier2_manual_verify"
    tier3_mock_query = "tier3_mock_query"
    document_upload = "document_upload"
    document_extraction = "document_extraction"
    rules_verdict = "rules_verdict"
    recommendation_generated = "recommendation_generated"
    officer_override = "officer_override"
    bidder_created = "bidder_created"
    compliance_run_started = "compliance_run_started"
    compliance_run_completed = "compliance_run_completed"


class AuditLog(Base):
    """
    Immutable audit trail. Every automated query, manual verification,
    AI output, and officer override is logged here with full context.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(SAEnum(AuditEventType), nullable=False)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # null = system

    # What happened
    description = Column(Text, nullable=False)
    # Full JSON payload (request + response / extracted fields / etc.)
    payload = Column(JSON, nullable=True)

    # Immutable timestamp — never updated
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    bidder = relationship("Bidder", back_populates="audit_logs")
    actor = relationship("User", back_populates="audit_entries")
