# AI-Powered Integrated Bid Compliance Verification Platform
## SIH 2026 — Problem Statement 26100
### Ministry of Petroleum & Natural Gas — CPCL

---

## Overview
An AI-powered platform for GeM procurement bid compliance verification, built for Procurement Officers to automate, audit, and recommend actions across multi-source compliance checks using a transparent three-tier integration architecture.

## Architecture

| Tier | Sources | Method |
|------|---------|--------|
| **Tier 1** | GST, EPFO/ESIC, MCA21, PAN | Real reseller REST APIs (sandbox) |
| **Tier 2** | Udyam, BIS, Startup India | Deep-link to official portal + officer manual input |
| **Tier 3** | DigiLocker, NSIC, OEM Auth, Blacklist | Seeded mock services |

## Tech Stack
- **Frontend:** React (Vite) + Tailwind CSS
- **Backend:** Python FastAPI
- **Database:** SQLite (demo) / PostgreSQL-ready
- **OCR:** Tesseract + EasyOCR fallback
- **AI Extraction:** NuExtract-based field extraction pipeline
- **Recommendations:** Deterministic Python template engine (data-sovereign, no external LLM)
- **Auth:** JWT (Officer + Admin roles)
- **Deployment:** Docker Compose

## Quick Start

### Prerequisites
- Python 3.11+
- Node 18+
- Tesseract OCR (`brew install tesseract`)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in values
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Mock Services (Tier 3)
```bash
cd mock_services
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Docker (all services)
```bash
docker-compose up --build
```

## Features
- Bulk bidder upload (CSV or manual)
- Per-bidder automated compliance runs across all tiers
- Deterministic rules engine → weighted compliance score → risk band (Low / Medium / High / Critical)
- AI-generated natural-language recommendations via Python template engine
- Tier 2 deep-link panel with officer manual verification recording
- Officer override with mandatory reason (fully logged)
- Immutable audit trail (every query, extract, verdict, override — timestamped)
- PDF export of audit trail per bidder
- Admin panel: mock service toggles, tender-specific rule toggles, full audit logs

## Compliance Scoring
| Score | Risk Level |
|-------|-----------|
| 90–100 | 🟢 Low |
| 70–89 | 🟡 Medium |
| 40–69 | 🔴 High |
| <40 or blacklisted | ⛔ Critical |

## License
Built for SIH 2026. Academic/demo use.
