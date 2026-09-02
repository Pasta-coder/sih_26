from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class CheckStatus(str, enum.Enum):
    pending = "pending"
    pass_ = "pass"
    fail = "fail"
    manual_review = "manual_review"   # Tier 2: awaiting officer manual input
    not_applicable = "not_applicable"


class CheckTier(str, enum.Enum):
    tier1 = "tier1"
    tier2 = "tier2"
    tier3 = "tier3"


class ComplianceCheck(Base):
    """One row per check type per bidder verification run."""
    __tablename__ = "compliance_checks"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    check_name = Column(String, nullable=False)   # e.g. "gst_status", "epfo_registration"
    check_tier = Column(SAEnum(CheckTier), nullable=False)
    status = Column(SAEnum(CheckStatus), default=CheckStatus.pending, nullable=False)

    # Raw API/mock response (JSON)
    raw_response = Column(JSON, nullable=True)
    # Human-readable detail about why pass/fail
    detail = Column(Text, nullable=True)
    # Weight used in scoring (0.0–1.0)
    weight = Column(Float, default=1.0)

    # Tier 2 manual verification fields
    tier2_portal_url = Column(String, nullable=True)
    tier2_officer_result = Column(String, nullable=True)   # "verified"/"failed"/"discrepancy"
    tier2_officer_notes = Column(Text, nullable=True)
    tier2_screenshot_path = Column(String, nullable=True)
    tier2_verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    tier2_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    bidder = relationship("Bidder", back_populates="compliance_checks")
    verifier = relationship("User", foreign_keys=[tier2_verified_by])


class ComplianceOverride(Base):
    """Officer override of a compliance check verdict."""
    __tablename__ = "compliance_overrides"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    check_name = Column(String, nullable=False)
    original_status = Column(String, nullable=False)
    overridden_status = Column(String, nullable=False)
    reason = Column(Text, nullable=False)   # Mandatory reason text
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    overridden_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bidder = relationship("Bidder", back_populates="overrides")
    officer = relationship("User", back_populates="overrides")
