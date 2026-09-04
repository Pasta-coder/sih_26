import csv, io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from database import get_db
from models.bidder import Bidder
from models.tender import Tender
from models.user import User
from schemas.bidder import BidderCreate, BidderOut, BidderSummary
from auth_utils import get_current_user
from typing import List

router = APIRouter()


def _get_tender_or_404(tender_id: int, db: Session) -> Tender:
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender


@router.post("/{tender_id}/bidders", response_model=BidderOut, status_code=201)
def add_bidder(
    tender_id: int,
    payload: BidderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _get_tender_or_404(tender_id, db)
    bidder = Bidder(**payload.model_dump(), tender_id=tender_id)
    db.add(bidder)
    db.commit()
    db.refresh(bidder)
    return bidder


@router.post("/{tender_id}/bidders/upload-csv", status_code=201)
async def upload_bidders_csv(
    tender_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Bulk import bidders via CSV.
    Expected columns: company_name, gstin, pan, cin, udyam_number, epfo_code, esic_code, nsic_number, email, phone, address
    """
    _get_tender_or_404(tender_id, db)
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    created = []
    for row in reader:
        row = {k.strip(): v.strip() for k, v in row.items() if v.strip()}
        if "company_name" not in row:
            continue
        bidder = Bidder(tender_id=tender_id, **{
            k: row.get(k) for k in [
                "company_name", "gstin", "pan", "cin",
                "udyam_number", "epfo_code", "esic_code", "nsic_number",
                "email", "phone", "address"
            ]
        })
        db.add(bidder)
        created.append(bidder.company_name)
    db.commit()
    return {"imported": len(created), "companies": created}


@router.get("/{tender_id}/bidders", response_model=List[BidderSummary])
def list_bidders(
    tender_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    _get_tender_or_404(tender_id, db)
    return (
        db.query(Bidder)
        .filter(Bidder.tender_id == tender_id)
        .order_by(Bidder.compliance_score.desc().nullslast())
        .all()
    )


@router.get("/bidder/{bidder_id}", response_model=BidderOut)
def get_bidder(bidder_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")
    return bidder
