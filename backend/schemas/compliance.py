from pydantic import BaseModel, Field, field_validator
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


# Known Tier-2 manual-verification checks (must stay in sync with the rules
# engine / CHECK_LABELS). Anything else is a malformed payload.
TIER2_CHECK_NAMES = frozenset({"udyam_msme", "bis_license", "startup_india_dpiit"})


class Tier2VerifyInput(BaseModel):
    check_name: str
    # E4: Only these three tokens are meaningful verdicts. Free-text strings
    # previously fell through to an automatic Fail — a silent wrong verdict.
    result: Literal["verified", "failed", "discrepancy"]
    notes: str | None = None

    @field_validator("check_name")
    @classmethod
    def _check_name_known(cls, v: str) -> str:
        if v not in TIER2_CHECK_NAMES:
            raise ValueError(
                f"check_name must be one of: {', '.join(sorted(TIER2_CHECK_NAMES))}"
            )
        return v


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
