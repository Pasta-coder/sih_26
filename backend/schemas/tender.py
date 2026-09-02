from pydantic import BaseModel
from datetime import datetime
from typing import Any


class TenderCreate(BaseModel):
    tender_number: str
    title: str
    department: str | None = None
    description: str | None = None
    rule_toggles: dict[str, Any] = {}


class TenderOut(BaseModel):
    id: int
    tender_number: str
    title: str
    department: str | None
    description: str | None
    rule_toggles: dict[str, Any]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TenderUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    description: str | None = None
    rule_toggles: dict[str, Any] | None = None
    is_active: bool | None = None
