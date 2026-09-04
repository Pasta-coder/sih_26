# 🛡️ GeM Bid Compliance Verification Platform

**SIH 2026 — Problem Statement 26100**  
Ministry of Petroleum & Natural Gas (MoPNG) / CPCL

> AI-powered, data-sovereign compliance verification for government procurement bids on the GeM portal.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              3-Tier Compliance Engine                    │
├──────────────┬──────────────────┬───────────────────────┤
│    Tier 1    │     Tier 2       │       Tier 3          │
│  Automated   │  Manual Redirect │      Mocked           │
├──────────────┼──────────────────┼───────────────────────┤
│ GST (GSTN)  │ Udyam (MSME)    │ DigiLocker            │
│ PAN (IT Dept)│ BIS (QCI)       │ NSIC                  │
│ EPFO (UAN)  │ Startup India   │ OEM Authorization     │
│ MCA21 (ROC) │ DPIIT            │ Make in India         │
│             │                 │ Blacklist / CVC       │
└──────────────┴──────────────────┴───────────────────────┘
        ↓ Rules Engine (deterministic, PRD §6)
        ↓ Scoring Engine (weighted, 0-100)
        ↓ Recommendation Engine (Python template, Option B)
        ↓ Immutable Audit Trail (SQLite, append-only)
```

## 🚀 Quick Start

### Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# .\venv\Scripts\activate       # Windows

pip install -r requirements.txt
python3 seed.py                  # Create demo users + 25 synthetic bidders
uvicorn main:app --reload --port 8000
```

Backend API: http://localhost:8000  
Swagger Docs: http://localhost:8000/docs

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

### Demo Credentials

| Role    | Email                    | Password      |
|---------|--------------------------|---------------|
| Admin   | `admin@cpcl.gov.in`      | `Admin@1234`  |
| Officer | `officer@cpcl.gov.in`    | `Officer@1234`|

---

## ⚡ Wow Moment — Live Re-Verification

1. Login as **Admin** → go to **Admin Panel**
2. Select the demo tender → toggle **EPFO Required = OFF** (or **MSME Exemption**, **Make in India**)
3. Navigate to any bidder without EPFO → click **Run Verification**
4. Toggle **EPFO Required = ON** → re-run → watch score drop

This demonstrates the system's real-time re-scoring without any manual data entry.
Toggle changes are persisted to the tender (PATCH `/api/admin/mock-toggle/{id}`)
and take effect on the next verification run.

---

## 📂 Project Structure

```
sih_26/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── database.py              # SQLite + SQLAlchemy
│   ├── auth_utils.py            # JWT + bcrypt
│   ├── config.py                # Settings via pydantic-settings
│   ├── seed.py                  # Database seeder
│   ├── models/                  # ORM models
│   ├── schemas/                 # Pydantic schemas
│   ├── routers/                 # API routes
│   │   ├── auth.py              # Login / register / me
│   │   ├── tenders.py           # Tender CRUD
│   │   ├── bidders.py           # Bidder CRUD + CSV upload
│   │   ├── compliance.py        # Full compliance run + overrides
│   │   ├── documents.py         # Document upload + OCR
│   │   ├── audit.py             # Audit trail + PDF export
│   │   └── admin.py             # Rule toggle management
│   ├── tests/                   # pytest suite (rules, scoring, API)
│   └── services/
│       ├── tier1/               # GST, PAN, EPFO, MCA21 adapters
│       ├── tier2/               # Udyam, BIS deep-link generators
│       ├── tier3/               # Blacklist, NSIC, Make in India, DigiLocker, OEM
│       ├── rules_engine.py      # Deterministic compliance rules
│       ├── scoring.py           # Weighted score + risk banding
│       ├── recommendation.py    # Python template engine (Option B)
│       ├── ocr.py               # Tesseract → EasyOCR pipeline
│       ├── extraction.py        # Field extraction (grounded)
│       ├── audit_log.py         # Immutable audit trail
│       └── pdf_export.py        # ReportLab PDF generator
├── frontend/
│   └── src/
│       ├── pages/               # Login, Dashboard, TenderDetail, BidderDetail, AuditLog, AdminPanel
│       ├── components/          # Layout with sidebar
│       ├── context/             # AuthContext (JWT)
│       └── api/                 # Axios client
├── docker-compose.yml
└── PRD.md
```

---

## 🎯 Compliance Engine — Design Decisions

### Why Option B (Template Engine) over LLM?

For a **compliance/legal tool**, consistency and auditability are mandatory:

| Concern | LLM | Template Engine |
|---------|-----|-----------------|
| Same input → same output | ❌ Non-deterministic | ✅ Guaranteed |
| Data sovereignty | ❌ PAN/GST leaves server | ✅ Zero egress |
| Auditability | ❌ Hard to audit | ✅ Sentence-level traceability |
| Offline operation | ❌ Requires API | ✅ Fully offline |
| Latency | ❌ 1–10s per call | ✅ <1ms |

### Why `bcrypt` directly (not passlib)?

Python 3.14 + bcrypt 5.x + passlib 1.7.4 has a known compatibility issue. We use `bcrypt` directly for correctness.

---

## 📋 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Login, returns JWT |
| `/api/auth/me` | GET | Current user |
| `/api/auth/register` | POST | Admin-only · creates officer accounts |
| `/api/tenders/` | GET/POST | List / create tenders |
| `/api/tenders/{id}/bidders` | GET/POST | List / add bidders |
| `/api/compliance/run/{bidder_id}` | POST | Full compliance run |
| `/api/compliance/run-all/{tender_id}` | POST | Run all bidders |
| `/api/compliance/tier2-verify/{id}` | POST | Officer manual verify |
| `/api/compliance/override/{id}` | POST | Officer override |
| `/api/audit/bidder/{id}` | GET | Bidder audit trail |
| `/api/audit/bidder/{id}/export-pdf` | GET | Download PDF report |
| `/api/documents/upload/{id}` | POST | Upload + OCR document (size-limited) |
| `/api/documents/consistency/{id}` | GET | Advisory doc-vs-record cross-check |
| `/api/audit/all` | GET | Full system audit log (**admin only**) |
| `/api/admin/mock-toggle/{id}` | PATCH | Update rule toggles |

---

## 🔒 Security & Data Sovereignty

- **Zero external API calls** in production by default (`USE_REAL_TIER1_APIS=false`)
- **Bidder PAN/GST/financial data never leaves the server**
- **JWT authentication** with role-based access (Officer / Admin)
- **Immutable audit trail** — every action logged with actor, timestamp, payload
- **Officer overrides require mandatory written justification**, always logged
- **Blacklist verdicts (the hard auto-disqualifier) can only be overridden by admins**

---

*Built for SIH 2026 — Problem Statement 26100 | CPCL · Ministry of Petroleum & Natural Gas*
