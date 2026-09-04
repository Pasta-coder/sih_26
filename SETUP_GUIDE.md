# 📦 SIH 2026 — GeM Bid Compliance Platform
## Complete Setup & Handoff Guide
### *(Pass this file to an LLM to get full context + setup help)*

---

## 🧠 What Is This Project?

This is an **AI-powered bid compliance verification platform** built for:

- **Competition:** Smart India Hackathon (SIH) 2026
- **Problem Statement:** PS-26100
- **Ministry:** Ministry of Petroleum & Natural Gas (MoPNG) — CPCL
- **Goal:** Automate the verification of vendor/bidder compliance documents submitted on the GeM (Government e-Marketplace) portal

The system checks each bidder against multiple Indian government databases (GST, PAN, EPFO, MCA21, Udyam, Blacklists etc.) using a 3-tier architecture, scores them 0–100, assigns a risk level, and generates an AI recommendation — all without sending any sensitive data to external cloud services.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11+ · FastAPI · Uvicorn |
| Database | SQLite (via SQLAlchemy ORM) |
| Auth | JWT (python-jose) · bcrypt password hashing |
| OCR Pipeline | Tesseract · EasyOCR (fallback) |
| PDF Export | ReportLab |
| Fuzzy Matching | RapidFuzz |
| Frontend | React 18 · Vite 5 · Vanilla CSS |
| HTTP Client | Axios |
| Routing | React Router DOM v6 |

---

## 📁 Full Project Structure

```
sih_26/
│
├── backend/
│   ├── main.py                        # FastAPI app entry point
│   ├── database.py                    # SQLite engine + session + create_tables()
│   ├── config.py                      # All settings (reads from .env)
│   ├── auth_utils.py                  # JWT encode/decode, bcrypt hash/verify
│   ├── seed.py                        # Seeds DB with users, tender, 25 bidders
│   ├── requirements.txt               # All Python dependencies (pinned)
│   ├── Dockerfile                     # Backend Docker image
│   │
│   ├── models/                        # SQLAlchemy ORM models
│   │   ├── user.py                    # User (email, role: officer/admin)
│   │   ├── tender.py                  # Tender (number, title, rule_toggles)
│   │   ├── bidder.py                  # Bidder (GSTIN, PAN, CIN, Udyam...)
│   │   ├── compliance.py              # ComplianceCheck, ComplianceOverride
│   │   └── audit.py                   # AuditLog (append-only)
│   │
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── tender.py
│   │   ├── bidder.py
│   │   └── compliance.py
│   │
│   ├── routers/                       # API route handlers
│   │   ├── auth.py                    # POST /api/auth/login, /register, GET /me
│   │   ├── tenders.py                 # CRUD for tenders
│   │   ├── bidders.py                 # CRUD for bidders, CSV bulk upload
│   │   ├── compliance.py              # Run checks, Tier2 manual verify, override
│   │   ├── documents.py               # Upload document → OCR → field extraction
│   │   ├── admin.py                   # Rule toggle management (admin only)
│   │   └── audit.py                   # Audit trail read + PDF export
│   │
│   └── services/
│       ├── tier1/
│       │   ├── gst.py                 # GSTN verification (real API / mock)
│       │   ├── pan.py                 # PAN verification
│       │   ├── epfo.py                # EPFO registration check
│       │   └── mca21.py               # MCA21 company status check
│       ├── tier2/
│       │   └── portals.py             # Deep-link URL generators for manual verify
│       ├── tier3/
│       │   ├── blacklist.py           # CVC/GeM debarred vendor check (mocked)
│       │   ├── nsic.py                # NSIC registration check (mocked)
│       │   ├── digilocker.py          # DigiLocker document check (mocked)
│       │   └── oem.py                 # OEM authorization (document-only)
│       ├── rules_engine.py            # Deterministic per-check verdict logic
│       ├── scoring.py                 # Weighted 0-100 score + risk band
│       ├── recommendation.py          # Python template engine (Option B)
│       ├── ocr.py                     # Tesseract → EasyOCR OCR pipeline
│       ├── extraction.py              # Regex field extraction from OCR text
│       ├── audit_log.py               # Append-only audit log service
│       └── pdf_export.py              # ReportLab PDF report generator
│
├── frontend/
│   ├── vite.config.js                 # Vite config + API proxy to :8000
│   ├── Dockerfile                     # Frontend Docker image
│   └── src/
│       ├── main.jsx                   # React entry point
│       ├── App.jsx                    # Router + PrivateRoute + AdminRoute
│       ├── index.css                  # Complete dark glassmorphism design system
│       ├── api/
│       │   └── client.js              # Axios instance with JWT interceptor
│       ├── context/
│       │   └── AuthContext.jsx        # Global auth state (login/logout/me)
│       ├── components/
│       │   └── Layout.jsx             # Sidebar navigation layout
│       └── pages/
│           ├── Login.jsx              # Login form with demo credentials
│           ├── Dashboard.jsx          # Overview + tender list
│           ├── TenderList.jsx         # Tender list + create tender modal
│           ├── TenderDetail.jsx       # Bidder ranked table + run-all + CSV upload
│           ├── BidderDetail.jsx       # Full compliance detail + PDF export
│           ├── AuditLog.jsx           # Filterable immutable audit trail
│           └── AdminPanel.jsx         # Rule toggle management UI
│
├── docker-compose.yml                 # Run full stack with Docker
├── README.md                          # Project overview
└── SETUP_GUIDE.md                     # THIS FILE
```

---

## 🔧 Environment Variables

The backend reads from a `.env` file placed inside the `backend/` directory.
**The app works out of the box without a `.env` file** — all variables have safe defaults for local development.

### Create `backend/.env` (copy-paste this entire block):

```
# ── App ─────────────────────────────────────────────────────────────────────
APP_ENV=development

# IMPORTANT: Change this in production to a long random string.
# Generate one: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=dev-secret-key-change-in-production

# JWT token expiry in minutes (480 = 8 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=480

# ── Database ─────────────────────────────────────────────────────────────────
# SQLite file path relative to the backend/ directory
DATABASE_URL=sqlite:///./compliance.db

# ── Feature Flags ─────────────────────────────────────────────────────────────
# false = use mock API responses (works offline, no keys needed) — RECOMMENDED for demo
# true  = call real Tier 1 government APIs (requires API keys below)
USE_REAL_TIER1_APIS=false

# ── Tier 1 API Keys ──────────────────────────────────────────────────────────
# Only needed if USE_REAL_TIER1_APIS=true
# The system works fully without these.

# Sandbox.co.in — GST verification
GST_API_KEY=
GST_API_BASE_URL=https://api.sandbox.co.in/gst

# Sandbox.co.in — PAN verification
PAN_API_KEY=
PAN_API_BASE_URL=https://api.sandbox.co.in/kyc/pan

# Deepvue.tech — EPFO verification
EPFO_API_KEY=
EPFO_API_BASE_URL=https://api.deepvue.tech/v1

# AuthBridge — MCA21 company status
MCA_API_KEY=
MCA_API_BASE_URL=https://api.authbridge.com/mca

# ── File Uploads ─────────────────────────────────────────────────────────────
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=20

# ── CORS ─────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed frontend origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

> If you skip creating `.env`, the app uses these same values as built-in defaults automatically.

---

## 🚀 Local Setup — Step by Step

### Prerequisites

```bash
python3 --version    # Need 3.11 or higher
node --version       # Need 22.x (22.11+ works with Vite 5)
git --version        # Any version
```

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Pasta-coder/sih_26.git
cd sih_26
```

---

### Step 2 — Backend Setup

```bash
cd backend
```

**Create virtual environment:**

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat
```

You should see `(venv)` in your terminal prompt after activation.

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Create `.env` file** (paste content from above into `backend/.env`), or skip for defaults.

**Seed the database:**

```bash
python3 seed.py
```

Expected output:
```
✅ Created admin: admin@cpcl.gov.in / Admin@1234
✅ Created officer: officer@cpcl.gov.in / Officer@1234
✅ Created tender: CPCL/2026/SIH-DEMO/001
✅ Seeded 25 bidders into tender CPCL/2026/SIH-DEMO/001
```

**Start the server:**

```bash
uvicorn main:app --reload --port 8000
```

Backend live at → **http://localhost:8000**
Swagger docs at → **http://localhost:8000/docs**

---

### Step 3 — Frontend Setup (new terminal tab)

```bash
# From the sih_26/ root directory
cd frontend
npm install
npm run dev
```

Frontend live at → **http://localhost:5173**

---

### Step 4 — Login

Open **http://localhost:5173**

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@cpcl.gov.in` | `Admin@1234` |
| Officer | `officer@cpcl.gov.in` | `Officer@1234` |

---

## 🐳 Docker Setup (Alternative)

Run the entire stack with one command:

```bash
# From the sih_26/ root directory
docker-compose up --build
```

Then seed the database:
```bash
docker exec -it sih_26-backend-1 python3 seed.py
```

Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## 🔌 Full API Reference

All endpoints require `Authorization: Bearer <token>` header except `/api/auth/login`.

Get a token:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@cpcl.gov.in","password":"Officer@1234"}'
```

### Auth
| Method | Endpoint | Body / Notes |
|--------|----------|-------------|
| POST | `/api/auth/login` | `{"email":"...","password":"..."}` → returns `access_token` |
| GET | `/api/auth/me` | Returns current user info |

### Tenders
| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/tenders/` | List all tenders |
| POST | `/api/tenders/` | Create tender. Body: `{tender_number, title, department, rule_toggles}` |
| GET | `/api/tenders/{id}` | Tender detail |
| GET | `/api/tenders/{id}/bidders` | All bidders ranked by compliance score |

### Bidders
| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/tenders/{id}/bidders` | Add bidder. Body: `{company_name, gstin, pan, cin, ...}` |
| POST | `/api/tenders/{id}/bidders/upload-csv` | Multipart CSV upload |

### Compliance
| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/compliance/run/{bidder_id}` | Run all Tier 1/2/3 checks for one bidder |
| POST | `/api/compliance/run-all/{tender_id}` | Run checks for every bidder in a tender |
| GET | `/api/compliance/{bidder_id}` | Get results + recommendation |
| POST | `/api/compliance/tier2-verify/{bidder_id}` | Body: `{check_name, result, notes}` |
| POST | `/api/compliance/override/{bidder_id}` | Body: `{check_name, new_status, reason}` |

### Documents
| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/documents/upload/{bidder_id}` | Form: `doc_type` + `file`. Runs OCR + extraction |
| GET | `/api/documents/{bidder_id}` | List uploaded docs and extracted fields |

Valid `doc_type` values: `pan_card`, `gst_certificate`, `udyam_certificate`, `epfo_certificate`, `itr_v_acknowledgment`, `oem_authorization_letter`

### Audit
| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/audit/bidder/{bidder_id}` | All audit events for one bidder |
| GET | `/api/audit/bidder/{bidder_id}/export-pdf` | Download PDF audit report |
| GET | `/api/audit/all` | Full system log (Admin only) |

### Admin
| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/api/admin/mock-toggle/{tender_id}` | Get rule toggles |
| PATCH | `/api/admin/mock-toggle/{tender_id}` | Body: `{"epfo_required": true, "bis_required": false, ...}` |

---

## 📊 CSV Import Format

```csv
company_name,gstin,pan,cin,udyam_number,epfo_code,email,phone,address
Reliance Industries Ltd,27AAACR5055K1ZK,AAACR5055K,L17110MH1973PLC019786,UDYAM-MH-23-0001234,MHBAN0012345000,proc@ril.com,9100000001,"Nariman Point, Mumbai"
No GSTIN Vendor,,AABCN5555F,,,,,9100000002,"Hyderabad, Telangana"
```

Only `company_name` is required. All other fields are optional.

---

## 🏛️ Compliance Engine — How It Works

### 3-Tier Architecture

```
Tier 1 — Fully Automated (results in seconds)
  GST status check        → GSTN reseller API (mock when USE_REAL_TIER1_APIS=false)
  PAN validity            → IT Dept API + fuzzy name match
  EPFO registration       → EPFO/Deepvue API
  MCA21 company status    → Active / Struck-off / Dissolved

Tier 2 — Officer-Assisted (deep-link redirect)
  Udyam / MSME            → Opens udyamregistration.gov.in in new tab
  BIS License             → Opens bis.gov.in (only if tender has bis_required=true)
  Startup India / DPIIT   → Opens startupindia.gov.in

Tier 3 — Mocked with realistic fixtures
  CVC Blacklist           → Seeded debarment database (10 known bad entities)
  NSIC                    → Seeded mock registry
  DigiLocker              → Document fetch simulation
  OEM Authorization       → Upload letter → OCR → field consistency check only
```

### Why Tier 3 is Mocked

- CVC/GeM blacklist has no real-time public API — production would sync daily from ministry data
- NSIC portal has no machine-readable API
- DigiLocker requires Aadhaar citizen login — not applicable for companies
- OEM is a private B2B document, no government registry to check against

### Scoring Weights

| Check | Max Points |
|-------|-----------|
| GST Status | 25 |
| PAN Validity | 20 |
| MCA21 Status | 15 |
| EPFO Registration | 15 |
| Udyam / MSME | 10 |
| BIS License | 10 (if required) |
| Startup India | 5 |
| **Blacklisted** | **Score = 0, overrides all** |

**Risk Bands:** Low (90-100) · Medium (70-89) · High (40-69) · Critical (0-39)

### Why Python Templates, Not an LLM

| Concern | Cloud LLM (GPT-4 etc.) | Template Engine (this system) |
|---------|------------------------|-------------------------------|
| Deterministic output | No | Yes |
| Data sovereignty | No — PAN/GST leaves server | Yes — zero data egress |
| Offline operation | No | Yes |
| Auditability | No — black box | Yes — every sentence is traceable |
| Speed | 1-10 seconds per call | Under 1 ms |
| Cost | Paid per call | Free |

---

## 🔐 Security Notes

- JWT tokens expire in 8 hours (change via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passwords hashed with bcrypt (cost factor 12)
- All officer overrides require a written justification — logged permanently
- Audit trail is append-only — no UPDATE or DELETE on audit records, ever
- No bidder data leaves the server when `USE_REAL_TIER1_APIS=false`
- **For production:** generate a real secret key:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```
  Put the output as `SECRET_KEY` in `backend/.env`

---

## 🐛 Troubleshooting

**`ModuleNotFoundError` on backend start**
```bash
# Make sure venv is activated (you should see (venv) in prompt)
source venv/bin/activate
pip install -r requirements.txt
```

**`bcrypt` / passlib version error**
```bash
pip install "bcrypt==4.2.0" --force-reinstall
```

**`email-validator is not installed`**
```bash
pip install "pydantic[email]"
```

**Frontend `rolldown native binding` error**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Port already in use**
```bash
# Backend on different port
uvicorn main:app --reload --port 8001

# Then update frontend/vite.config.js line:
# target: 'http://localhost:8001'
```

**Fresh database start (wipe everything)**
```bash
cd backend
rm compliance.db
python3 seed.py
```

**Tesseract not found (OCR warnings)**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows — download from:
# https://github.com/UB-Mannheim/tesseract/wiki
```
App works without Tesseract — document upload just won't extract text.

---

## 📋 5-Minute Judge Demo Script

1. Open **http://localhost:5173** → Login as Officer
2. Click **Tenders** → `CPCL/2026/SIH-DEMO/001`
3. Click **"Run All Compliance"** → all 25 bidders verified in ~10 seconds
4. Show ranked table: scores, risk badges, status
5. Click **"Blacklisted Ventures Ltd"** → Score: 0, Risk: Critical (auto-disqualified)
6. Click **"Reliance Industries Limited"** → Score: 100, Risk: Low (all green)
7. Click **"Export PDF"** → download the audit report
8. Click **Audit Log** in sidebar → show every event with timestamp
9. Logout → Login as **Admin**
10. Go to **Admin Panel** → toggle `EPFO Required = ON`
11. Go back to a bidder without EPFO → **"Run Verification"** → score drops live
12. This is the "Wow Moment" — no code change, instant re-scoring

---

## 👥 Repository Info

- **GitHub:** https://github.com/Pasta-coder/sih_26
- **Default branch:** `main`
- **Built for:** SIH 2026 · Problem Statement 26100 · CPCL · Ministry of Petroleum & Natural Gas
