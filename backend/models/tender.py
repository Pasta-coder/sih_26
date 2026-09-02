from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    tender_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    department = Column(String)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Tender-specific rule toggles (JSON object with flags)
    # e.g. {"msme_exemption": true, "epfo_required": true, "make_in_india": false}
    rule_toggles = Column(JSON, default=dict)

    is_active = Column(Boolean, default=True)

    # Relationships
    bidders = relationship("Bidder", back_populates="tender")
    creator = relationship("User", foreign_keys=[created_by])
