from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


class BidderStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class Bidder(Base):
    __tablename__ = "bidders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)

    # Core identifiers
    company_name = Column(String, nullable=False)
    gstin = Column(String, index=True)
    pan = Column(String, index=True)
    cin = Column(String)          # MCA21 Company Identification Number
    udyam_number = Column(String) # Udyam registration (UDYAM-XX-00-0000000)
    epfo_code = Column(String)
    esic_code = Column(String)

    # Contact
    email = Column(String)
    phone = Column(String)
    address = Column(Text)

    # Status tracking
    status = Column(SAEnum(BidderStatus), default=BidderStatus.pending)
    compliance_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # Low/Medium/High/Critical

    # AI recommendation (Python template engine output)
    recommendation = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified_at = Column(DateTime, nullable=True)

    # Relationships
    tender = relationship("Tender", back_populates="bidders")
    compliance_checks = relationship("ComplianceCheck", back_populates="bidder")
    documents = relationship("BidderDocument", back_populates="bidder")
    overrides = relationship("ComplianceOverride", back_populates="bidder")
    audit_logs = relationship("AuditLog", back_populates="bidder")


class BidderDocument(Base):
    __tablename__ = "bidder_documents"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    doc_type = Column(String, nullable=False)   # e.g. "gst_certificate", "pan_card", "itr_v"
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    extracted_fields = Column(JSON, nullable=True)  # NuExtract output
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bidder = relationship("Bidder", back_populates="documents")
