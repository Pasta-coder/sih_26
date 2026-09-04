from pydantic import BaseModel, Field
from typing import Literal
from models.compliance import CheckStatus, CheckTier
from datetime import datetime


class CheckResultOut(BaseModel):
    id: int
    check_name: str
    check_tier: CheckTier
    status: CheckStatus
    detail: str | None
    raw_response: dict | None
    tier2_portal_url: str | None
    tier2_officer_result: str | None
    tier2_officer_notes: str | None
    tier2_verified_by: int | None
    tier2_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Tier2VerifyInput(BaseModel):
    check_name: str
    result: str       # "verified" | "failed" | "discrepancy: <detail>"
    notes: str | None = None


class OverrideInput(BaseModel):
    check_name: str
    new_status: Literal["pass", "fail"]
    reason: str = Field(min_length=20, description="Mandatory written justification (min 20 characters)")


class ComplianceRunOut(BaseModel):
    bidder_id: int
    company_name: str
    compliance_score: float | None
    risk_level: str | None
    recommendation: str | None
    checks: list[CheckResultOut]
