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


def seed(db=None):
    """
    Seed demo data. Pass an existing db session (for startup auto-seed)
    or leave None to create a new one (for manual CLI runs).
    """
    _own_session = db is None
    if _own_session:
        db = SessionLocal()

    try:
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

        # ── Tenders ────────────────────────────────────────────────────────────
        admin = db.query(User).filter(User.email == "admin@cpcl.gov.in").first()

        TENDERS = [
            {
                "tender_number": "GEM/2026/B/5291847",
                "title": "Supply of High-Speed Diesel (HSD) & Lubricants for Fleet Operations",
                "department": "Indian Oil Corporation Ltd (IOCL)",
                "description": (
                    "Procurement of High-Speed Diesel and industrial lubricants for IOCL fleet "
                    "and refinery operations across North India. Vendors must hold active GST, "
                    "valid PAN, EPFO registration and maintain Make in India compliance."
                ),
                "rule_toggles": {
                    "epfo_required": True,
                    "msme_exemption": False,
                    "bis_required": False,
                    "make_in_india": True,
                    "startup_india_eligible": False,
                },
            },
            {
                "tender_number": "GEM/2026/B/5318902",
                "title": "Annual Maintenance Contract — Industrial Safety Equipment & PPE",
                "department": "Bharat Petroleum Corporation Ltd (BPCL)",
                "description": (
                    "AMC for industrial safety equipment including fire suppression systems, gas "
                    "detectors, breathing apparatus, and personal protective equipment across "
                    "BPCL refineries. BIS certification mandatory for all PPE items."
                ),
                "rule_toggles": {
                    "epfo_required": True,
                    "msme_exemption": False,
                    "bis_required": True,
                    "make_in_india": True,
                    "startup_india_eligible": False,
                },
            },
            {
                "tender_number": "GEM/2026/B/5340217",
                "title": "IT Infrastructure Modernisation — Servers, Networking & Cybersecurity",
                "department": "ONGC — Ministry of Petroleum & Natural Gas",
                "description": (
                    "Supply and installation of enterprise-grade servers, core network switches, "
                    "firewalls, and endpoint security solutions for ONGC's digital transformation "
                    "initiative. Startups registered under DPIIT are eligible to bid."
                ),
                "rule_toggles": {
                    "epfo_required": True,
                    "msme_exemption": True,
                    "bis_required": False,
                    "make_in_india": True,
                    "startup_india_eligible": True,
                },
            },
            {
                "tender_number": "GEM/2026/B/5367445",
                "title": "Construction of EV Charging Infrastructure at Fuel Retail Outlets",
                "department": "Hindustan Petroleum Corporation Ltd (HPCL)",
                "description": (
                    "Design, supply, installation and commissioning of EV fast-charging stations "
                    "at 200 HPCL retail outlets across Maharashtra and Gujarat. Vendors must have "
                    "NSIC registration or MSME certificate. Make in India compliance required."
                ),
                "rule_toggles": {
                    "epfo_required": True,
                    "msme_exemption": True,
                    "bis_required": False,
                    "make_in_india": True,
                    "startup_india_eligible": True,
                },
            },
            {
                "tender_number": "GEM/2026/B/5389001",
                "title": "Supply of Petroleum Processing Equipment — Refinery Modernisation",
                "department": "CPCL — Ministry of Petroleum & Natural Gas",
                "description": (
                    "Procurement of heat exchangers, pressure vessels, control valves, and "
                    "instrumentation equipment for CPCL's Chennai refinery upgrade project. "
                    "Compliance with EPFO, GST, PAN and Make in India mandate is mandatory."
                ),
                "rule_toggles": {
                    "epfo_required": True,
                    "msme_exemption": False,
                    "bis_required": False,
                    "make_in_india": True,
                    "startup_india_eligible": False,
                },
            },
        ]

        for t in TENDERS:
            exists = db.query(Tender).filter(Tender.tender_number == t["tender_number"]).first()
            if not exists:
                new_tender = Tender(
                    tender_number=t["tender_number"],
                    title=t["title"],
                    department=t["department"],
                    description=t["description"],
                    created_by=admin.id,
                    rule_toggles=t["rule_toggles"],
                )
                db.add(new_tender)
                db.commit()
                db.refresh(new_tender)
                print(f"✅ Created tender: {new_tender.tender_number}")

        # Use first tender for bidder seeding
        tender = db.query(Tender).filter(
            Tender.tender_number == "GEM/2026/B/5291847"
        ).first()

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

        print("\n🚀 Seed complete! Login at http://localhost:8000/docs")
        print("   Admin:   admin@cpcl.gov.in / Admin@1234")
        print("   Officer: officer@cpcl.gov.in / Officer@1234")

    finally:
        if _own_session:
            db.close()


if __name__ == "__main__":
    seed()
