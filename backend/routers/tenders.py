from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.tender import Tender
from models.user import User
from schemas.tender import TenderCreate, TenderOut, TenderUpdate
from auth_utils import get_current_user
from typing import List

router = APIRouter()


@router.post("/", response_model=TenderOut, status_code=201)
def create_tender(
    payload: TenderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Tender).filter(Tender.tender_number == payload.tender_number).first():
        raise HTTPException(status_code=400, detail="Tender number already exists")
    tender = Tender(**payload.model_dump(), created_by=current_user.id)
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender


@router.get("/", response_model=List[TenderOut])
def list_tenders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Tender).order_by(Tender.created_at.desc()).all()


@router.get("/{tender_id}", response_model=TenderOut)
def get_tender(tender_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender


@router.patch("/{tender_id}", response_model=TenderOut)
def update_tender(
    tender_id: int,
    payload: TenderUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tender, field, value)
    db.commit()
    db.refresh(tender)
    return tender
