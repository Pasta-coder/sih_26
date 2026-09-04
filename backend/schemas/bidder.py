from pydantic import BaseModel
from models.bidder import BidderStatus
from datetime import datetime
from typing import Any


class BidderCreate(BaseModel):
    company_name: str
    gstin: str | None = None
    pan: str | None = None
    cin: str | None = None
    udyam_number: str | None = None
    epfo_code: str | None = None
    esic_code: str | None = None
    nsic_number: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class BidderOut(BaseModel):
    id: int
    tender_id: int
    company_name: str
    gstin: str | None
    pan: str | None
    cin: str | None
    udyam_number: str | None
    epfo_code: str | None
    esic_code: str | None
    nsic_number: str | None
    email: str | None
    phone: str | None
    address: str | None
    status: BidderStatus
    compliance_score: float | None
    risk_level: str | None
    recommendation: str | None
    created_at: datetime
    last_verified_at: datetime | None

    model_config = {"from_attributes": True}


class BidderSummary(BaseModel):
    """Lightweight summary for tender-level ranked list."""
    id: int
    company_name: str
    gstin: str | None
    status: BidderStatus
    compliance_score: float | None
    risk_level: str | None

    model_config = {"from_attributes": True}
