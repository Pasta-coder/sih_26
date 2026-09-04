"""Shared test fixtures.

Sets up an isolated SQLite database (in a tmp dir) and a FastAPI TestClient
before any app module is imported, plus helpers to seed users/tender/bidder.
"""
import os
import sys
import tempfile

# Make backend/ importable regardless of CWD (mirrors seed.py).
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Point the app at an isolated SQLite DB BEFORE any app module is imported —
# database.py builds its engine from settings at import time.
_TMP_DIR = tempfile.mkdtemp(prefix="compliance_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP_DIR, 'test.db')}"
os.environ["APP_ENV"] = "test"
os.environ["UPLOAD_DIR"] = os.path.join(_TMP_DIR, "uploads")

import pytest
from fastapi.testclient import TestClient

from database import Base, engine, SessionLocal
from main import app
from models.user import User, UserRole
from models.tender import Tender
from models.bidder import Bidder
from auth_utils import hash_password

ADMIN_EMAIL = "admin@test.gov.in"
ADMIN_PW = "Admin@1234"
OFFICER_EMAIL = "officer@test.gov.in"
OFFICER_PW = "Officer@1234"


@pytest.fixture()
def clean_db():
    """Fresh schema for every test — full isolation between tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(clean_db):
    """TestClient with lifespan (create_tables) running."""
    with TestClient(app) as c:
        yield c


def _login(client, email: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded(client):
    """Admin + officer users, one tender, one compliant bidder.

    Returns a dict with user objects, the bidder, and ready-made auth headers.
    """
    session = SessionLocal()
    admin = User(
        email=ADMIN_EMAIL, full_name="Test Admin",
        hashed_password=hash_password(ADMIN_PW), role=UserRole.admin,
    )
    officer = User(
        email=OFFICER_EMAIL, full_name="Test Officer",
        hashed_password=hash_password(OFFICER_PW), role=UserRole.officer,
    )
    session.add_all([admin, officer])
    session.commit()
    session.refresh(admin)
    session.refresh(officer)

    tender = Tender(
        tender_number="CPCL/TEST/001",
        title="Test Tender",
        created_by=admin.id,
        rule_toggles={
            "epfo_required": True,
            "msme_exemption": False,
            "bis_required": False,
            "make_in_india": False,
            "startup_india_eligible": False,
        },
    )
    session.add(tender)
    session.commit()
    session.refresh(tender)

    bidder = Bidder(
        tender_id=tender.id,
        company_name="ACME SUPPLIERS PVT LTD",
        gstin="27AAACR5055K1ZK",
        pan="AAACR5055K",
        cin="L17110MH1973PLC019786",
        udyam_number="UDYAM-MH-01-0000001",
        epfo_code="MHBAN0012345000",
        email="acme@example.com",
    )
    session.add(bidder)
    session.commit()
    # Re-load ids after commit expires the instances, so callers can safely
    # read .id off the detached objects returned below.
    session.refresh(bidder)
    session.refresh(tender)
    session.close()

    return {
        "client": client,
        "admin": admin,
        "officer": officer,
        "tender": tender,
        "bidder": bidder,
        "admin_headers": _auth(_login(client, ADMIN_EMAIL, ADMIN_PW)),
        "officer_headers": _auth(_login(client, OFFICER_EMAIL, OFFICER_PW)),
    }


@pytest.fixture()
def blacklisted_bidder(client, seeded):
    """Add a second, blacklisted bidder to the seeded tender."""
    session = SessionLocal()
    bidder = Bidder(
        tender_id=seeded["tender"].id,
        company_name="BLACKLISTED VENTURES LTD",
        gstin="07AABCU9603R1ZP",
        pan="AABCU9603R",
    )
    session.add(bidder)
    session.commit()
    session.refresh(bidder)
    session.close()
    return bidder