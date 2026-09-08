from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from config import get_settings
from database import create_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    create_tables()
    # Auto-seed on first deploy (Railway / fresh environment)
    _auto_seed_if_empty()
    yield
    # Shutdown


def _auto_seed_if_empty():
    """Seed demo data if the database has no users yet (first deploy)."""
    from database import SessionLocal
    from models.user import User
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            import seed as seed_module
            seed_module.seed(db)
    except Exception as e:
        print(f"[startup] Auto-seed skipped or failed: {e}")
    finally:
        db.close()



app = FastAPI(
    title="GeM Bid Compliance Verification API",
    description=(
        "AI-powered compliance verification platform for GeM procurement. "
        "SIH 2026 — Problem Statement 26100 — CPCL / Ministry of Petroleum & Natural Gas."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
from routers import auth, tenders, bidders, compliance, documents, admin, audit

app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(tenders.router,    prefix="/api/tenders",    tags=["Tenders"])
# Bidders are a sub-resource of tenders; bidders.py declares /{tender_id}/bidders
# routes, so the router must be mounted at /api/tenders to match the frontend
# and the documented API (/api/tenders/{id}/bidders).
app.include_router(bidders.router,    prefix="/api/tenders",    tags=["Bidders"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(documents.router,  prefix="/api/documents",  tags=["Documents"])
app.include_router(admin.router,      prefix="/api/admin",      tags=["Admin"])
app.include_router(audit.router,      prefix="/api/audit",      tags=["Audit"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "env": settings.app_env,
        "tier1_live": settings.use_real_tier1_apis,
    }
