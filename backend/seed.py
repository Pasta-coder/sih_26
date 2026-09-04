"""
Database Seed Script
─────────────────────
Seeds the database with:
  1. Admin user + Officer user
  2. Demo tender with realistic rule toggles
  3. 25 synthetic bidders from seed_data/bidders.json
"""
import json
import sys
import os
from pathlib import Path

# O3: anchor to this file so seed.py works from any CWD (repo root, backend/, docker exec)
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, create_tables
from models.user import User, UserRole
from models.tender import Tender
from models.bidder import Bidder
from auth_utils import hash_password

create_tables()
db = SessionLocal()


def seed():
    # ── Users ──────────────────────────────────────────────────────────────
    if not db.query(User).filter(User.email == "admin@cpcl.gov.in").first():
        admin = User(
            email="admin@cpcl.gov.in",
            full_name="CPCL Admin",
            hashed_password=hash_password("Admin@1234"),
            role=UserRole.admin,
        )
        db.add(admin)
        print("✅ Created admin: admin@cpcl.gov.in / Admin@1234")

    if not db.query(User).filter(User.email == "officer@cpcl.gov.in").first():
        officer = User(
            email="officer@cpcl.gov.in",
            full_name="Procurement Officer",
            hashed_password=hash_password("Officer@1234"),
            role=UserRole.officer,
        )
        db.add(officer)
        print("✅ Created officer: officer@cpcl.gov.in / Officer@1234")

    db.commit()

    # ── Tender ─────────────────────────────────────────────────────────────
    admin = db.query(User).filter(User.email == "admin@cpcl.gov.in").first()
    tender = db.query(Tender).filter(Tender.tender_number == "CPCL/2026/SIH-DEMO/001").first()
    if not tender:
        tender = Tender(
            tender_number="CPCL/2026/SIH-DEMO/001",
            title="Supply of Petroleum Processing Equipment — SIH Demo Tender",
            department="CPCL — Ministry of Petroleum & Natural Gas",
            description="SIH 2026 demonstration tender for AI-powered bid compliance verification. Problem Statement 26100.",
            created_by=admin.id,
            rule_toggles={
                "epfo_required": True,
                "msme_exemption": False,
                "bis_required": False,
                "make_in_india": True,
                "startup_india_eligible": False,
            },
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)
        print(f"✅ Created tender: {tender.tender_number}")

    # ── Bidders ────────────────────────────────────────────────────────────
    with open(BACKEND_DIR / "seed_data" / "bidders.json") as f:
        bidders_data = json.load(f)

    existing_count = db.query(Bidder).filter(Bidder.tender_id == tender.id).count()
    if existing_count == 0:
        for b in bidders_data:
            bidder = Bidder(
                tender_id=tender.id,
                company_name=b["company_name"],
                gstin=b.get("gstin"),
                pan=b.get("pan"),
                cin=b.get("cin"),
                udyam_number=b.get("udyam_number"),
                epfo_code=b.get("epfo_code"),
                nsic_number=b.get("nsic_number"),
                email=b.get("email"),
                phone=b.get("phone"),
                address=b.get("address"),
            )
            db.add(bidder)
        db.commit()
        print(f"✅ Seeded {len(bidders_data)} bidders into tender {tender.tender_number}")
    else:
        print(f"ℹ️  Bidders already seeded ({existing_count} found)")

    db.close()
    print("\n🚀 Seed complete! Login at http://localhost:8000/docs")
    print("   Admin:   admin@cpcl.gov.in / Admin@1234")
    print("   Officer: officer@cpcl.gov.in / Officer@1234")


if __name__ == "__main__":
    seed()
