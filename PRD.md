# Product Requirements Document
## AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

**Problem Statement ID:** 26100
**Organization:** Ministry of Petroleum & Natural Gas — Chennai Petroleum Corporation Limited (CPCL)
**Category:** Software | **Theme:** Smart Automation
**Document version:** 1.0
**Prepared for:** Code generation (Antigravity)

---

## 1. Purpose & Honesty Statement

This PRD describes a working prototype of an AI-powered bid compliance verification platform for GeM procurement. It is written to be **technically honest about what real government-portal integration is actually achievable** by an independent dev team, as opposed to what the problem statement's language ("integrate with relevant Government portals and databases") might suggest is trivially possible.

No dev team — student, hackathon, or otherwise — receives direct institutional API access to GSTN, Udyam, EPFO, ESIC, MCA21, DigiLocker, or the Income Tax Department without formal government empanelment (GSP licensing, MeitY approval, partner onboarding), a process that takes months and is unrelated to team skill. This PRD does **not** pretend otherwise. Instead, it defines a **three-tier integration architecture**, explicit about which sources get real automated integration, which get manual portal redirection, and which are mocked — and *why*, for each one.

This tiering is a feature of the design, not a limitation to hide. It should be presented to evaluators exactly as documented here.

---

## 2. Integration Tier Architecture

### Tier 1 — Fully Automated, Real Data (via licensed reseller/GSP REST APIs)

These sources have legitimate, commercially available, real-time REST APIs backed by actual government data, obtainable via free-tier/sandbox signup with a licensed reseller. No CAPTCHA, no manual steps, no consent-flow blockers.

| Source | Data returned | Integration path |
|---|---|---|
| **GST** (registration + status) | Legal name, trade name, registration status, address, filing metadata | GSP-licensed reseller sandbox (e.g. Sandbox.co.in, Cashfree Verification API, WhiteBooks) |
| **EPFO/ESIC** (establishment compliance) | Establishment name/ID, validity status, ESIC code, ownership type | Reseller APIs (Deepvue, AuthBridge, Decentro) |
| **MCA21** (company master data) | CIN, company status (Active/Struck-off/Liquidation), incorporation date, directors, DIN | Reseller APIs (AuthBridge, Surepass) or free lookup tools (Apify actor, RegisterKaro) |
| **PAN** (validity + name match only — *not* filing status, see §2.3) | PAN validity, registered name | PAN-verification reseller API |

**Engineering note:** These require your team to actually create free-tier developer accounts before build starts. This is a manual, human step — pick one reseller per source, confirm sandbox credit limits cover a ~25-30 bidder demo dataset, and store credentials in environment variables, never hardcoded.

### Tier 2 — Manual Redirect to Official Portal (Procurement Officer completes verification)

These sources have genuine, free, official government verification tools — but either require a CAPTCHA every time (ethically/legally gray to automate around) or have unconfirmed automatability that needs a technical spike before committing engineering time. Rather than fake automation or risk an unverifiable claim under judge scrutiny, the platform **deep-links the Procurement Officer directly to the correct official verification page**, pre-filling the lookup value (URN, license number, certificate number) where the portal's URL structure allows it, and provides an in-app field for the officer to record the verified result (status, screenshot/PDF upload of the portal result) back into the system.

| Source | Official portal | Why manual |
|---|---|---|
| **Udyam/MSME** | udyamregistration.gov.in — "Verify Udyam Registration" | CAPTCHA confirmed on every lookup, no exceptions, across every source checked |
| **BIS (ISI/CRS — Make in India adjacent)** | manakonline.in — "Search a License" | Public search flow's CAPTCHA status is unconfirmed; do not claim automation without a verified technical spike |
| **Startup India / DPIIT recognition** | startupindia.gov.in — Blockchain Certificate Verification | Same — plausible CAPTCHA-free but unconfirmed; verify before automating |

**Officer workflow for Tier 2:** Compliance checklist item shows a "Verify on Official Portal ↗" button → opens portal in new tab with lookup value copied to clipboard → officer performs the lookup manually → officer marks the check as Verified/Failed/Discrepancy Found in the app, optionally attaching a screenshot → this is logged in the audit trail with officer ID + timestamp, same as any AI-driven check.

### Tier 3 — Mocked (no real verification path exists for anyone, for structural or legal reasons)

These are not engineering shortfalls — no third party, including GeM itself, can verify these without a blocker that has nothing to do with development effort.

| Source | Why it's structurally unverifiable by any third party | Mock approach |
|---|---|---|
| **DigiLocker document pull** | Requires the actual document owner's live Aadhaar-OTP consent. Cannot function for synthetic dummy bidders under any circumstances — this isn't an API-access problem, it's a consent-flow problem | Mock DigiLocker service simulating document issuance for seeded dummy bidders |
| **PAN / Income Tax return-filing compliance** | Confidential taxpayer data protected under the Income Tax Act. No commercial or government API exposes ITR filing status to any third party — ever. Only the taxpayer's own e-filing login can see this | Bidder uploads ITR-V acknowledgment PDF; system validates acknowledgment number format only; filing status itself is self-declared + document-verified, not portal-checked |
| **NSIC registration** | No public verification portal or reseller API exists; only an applicant-login status page. Real-world equivalent is contacting the NSIC field office directly | Mock NSIC registry lookup service |
| **OEM authorization** | Not a government check at all — it's a private B2B letter from a manufacturer to a reseller. No government database of these exists to query, by design | Document upload + AI field-extraction/consistency check only (no portal to mock a lookup against, since none exists in reality either) |
| **Blacklisting/debarment** | CVC/GeM publish debarred-vendor lists as periodic downloadable data, not a live API | Mock service seeded from a static snapshot of published debarred-vendor data, refreshed manually — this is "real data, static refresh," not a fabricated list |

---

## 3. Scope

### 3.1 In scope (MVP)
- Bulk bidder verification for a single tender (list of bidders → per-bidder compliance run)
- Tier 1 automated checks: GST, EPFO/ESIC, MCA21, PAN validity
- Tier 2 manual-redirect checks: Udyam, BIS, Startup India/DPIIT
- Tier 3 mocked checks: DigiLocker, PAN/IT filing status (document-based), NSIC, OEM authorization, blacklisting (static real data)
- Document upload + AI extraction pipeline (OCR + structured extraction) for: Udyam certificate, GST certificate + GSTR-3B, PAN card, ITR-V acknowledgment, EPFO/ESIC registration certificate, OEM authorization letter
- Deterministic rules engine producing per-check pass/fail/pending/manual-review
- Weighted Compliance Score + Risk Level (Low/Medium/High/Critical)
- AI-generated natural-language recommendation (local LLM, not portal-dependent)
- Compliance Dashboard: per-bidder detail view + tender-level ranked comparison view
- Officer override with mandatory reason, logged
- Audit trail: every automated query, every manual-verification record, every AI output, every override
- PDF export of audit trail per bidder

### 3.2 Out of scope (explicitly, and why)
- Direct GeM portal integration for tender/bid ingestion (no public API; bidder data entered/CSV-uploaded)
- Document tampering/forensic authenticity detection (genuinely hard problem, no reliable open-source solution to build on credibly in this timeframe)
- Bidder self-service portal (adds UI surface with no benefit to the Procurement-Officer-centric workflow the problem statement describes)
- Real-time DigiLocker document pull (structurally blocked, see §2.3 Tier 3)
- Any CAPTCHA-bypassing automation (ethical/ToS line we will not cross)

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Tailwind)               │
│   Bidder Upload · Tender Setup · Compliance Dashboard ·           │
│   Tier-2 Manual Verify Panel · Officer Override · Audit Export    │
└───────────────────────────┬─────────────────────────────────────┘
                             │ REST (FastAPI)
┌───────────────────────────┴─────────────────────────────────────┐
│                          BACKEND (Python FastAPI)                 │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ Document Pipeline │  │ Integration Layer │  │  Rules Engine    │ │
│  │ Tesseract→EasyOCR │  │ Tier1: reseller   │  │  Deterministic   │ │
│  │ fallback → NuExtract│  │ REST adapters    │  │  pass/fail/score │ │
│  │ (3.8B, grounded    │  │ Tier2: deep-link  │  │  per source      │ │
│  │ extraction, JSON   │  │ generator + officer│  │                  │ │
│  │ schema per doc type)│  │ manual-entry form │  │                  │ │
│  │ + regex ID validation│ │ Tier3: mock       │  │                  │ │
│  │ + fuzzy name match  │  │ services (FastAPI)│  │                  │ │
│  └─────────────────┘  └──────────────────┘  └────────┬─────────┘ │
│                                                          │           │
│  ┌───────────────────────────────────────────────────┐ │           │
│  │  Local LLM (Qwen2.5-3B-Instruct / Llama-3.2-3B,     │◄┘           │
│  │  served via Ollama) — recommendation text generation │             │
│  │  ONLY. Never makes the compliance decision itself.   │             │
│  └───────────────────────────────────────────────────┘             │
│                                                                       │
│  ┌───────────────────────────────────────────────────┐             │
│  │  Audit Log (every query, extraction, verdict,         │             │
│  │  override — timestamped, immutable, exportable)        │             │
│  └───────────────────────────────────────────────────┘             │
└───────────────────────────┬───────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────────┐┌────────────┐┌────────────────┐
     │ Tier 1 Resellers ││ Tier 2      ││ Tier 3 Mock     │
     │ (GST, EPFO/ESIC, ││ Official    ││ Services        │
     │ MCA21, PAN)       ││ Portals     ││ (FastAPI, seeded│
     │ — real REST calls ││ (browser    ││ fixtures, admin │
     │                   ││ deep-link)  ││ toggle UI)      │
     └────────────────┘└────────────┘└────────────────┘
```

---

## 5. Document Processing Pipeline

```
Uploaded PDF/image
   │
   ▼
Tesseract OCR (primary)
   │  low-confidence or sanity-check failure (e.g. no PAN-shaped
   │  string found where expected)
   ▼
EasyOCR (fallback, better on skewed/low-quality scans)
   │
   ▼
NuExtract-3.8B (numind/NuExtract, pre-fine-tuned from Phi-3-mini)
   — given raw OCR text + a JSON schema per document type,
   — PURELY EXTRACTIVE: output is only ever text present in the
     source document — cannot hallucinate a PAN, date, or GSTIN.
     This grounded-extraction property is the core audit-safety
     guarantee of the pipeline and should be stated as such.
   │
   ▼
Regex validation layer
   — sanity-checks extracted PAN (AAAAA9999A), GSTIN (15-char),
     Udyam (UDYAM-XX-00-0000000) against known format patterns
   │
   ▼
Cross-check against Tier 1/2/3 verification result
   — exact match on IDs
   — fuzzy match (RapidFuzz/Levenshtein) on names — names across
     PAN/GST/Udyam documents are rarely byte-identical, so exact-
     match would produce false negatives
   │
   ▼
Rules Engine (deterministic Python — NOT the LLM)
   → per-check verdict: Pass / Fail / Pending / Manual-Review-Required
```

---

## 6. Compliance Scoring Model

Weighted by severity, not flat percentage:

- **Blacklisting/debarment match** → automatic score override to 0, Risk Level = Critical, regardless of all other checks
- **Statutory mandatory checks failing** (GST inactive, PAN invalid) → heavy deduction
- **Conditional/tender-specific checks failing** (EPFO required but missing, Make in India mandatory but unmet) → moderate deduction
- **Tier 2 checks pending officer manual verification** → held at "Pending" status, excluded from score until officer records a result (never silently assumed pass or fail)
- **Minor inconsistencies** (address mismatch, near-expiry certificate) → small deduction

**Risk bands:**
| Score | Risk Level |
|---|---|
| 90–100 | Low |
| 70–89 | Medium |
| 40–69 | High |
| <40 or any blacklisting match | Critical |

---

## 7. AI Recommendation Engine

- **Model:** Qwen2.5-3B-Instruct or Llama-3.2-3B-Instruct, served locally via Ollama (4-bit quantized GGUF)
- **Input:** Structured rules-engine output only (e.g. `{check: "GST_returns", status: "fail", detail: "3 of last 6 months missing"}`) — never raw documents, never asked to make the compliance decision
- **Output:** Human-readable recommendation paragraph for the Procurement Officer
- **Why local, not a cloud LLM API:** bidder PAN/GST/financial data never leaves the on-prem/local environment — a genuine data-sovereignty advantage for a CPSE context, not just a cost-saving choice
- **Stretch goal (Phase 2, not MVP-blocking):** LoRA fine-tune on ~200-500 synthetically generated (rule-output → recommendation-text) pairs via `peft`, to improve tone/format consistency. This does **not** improve factual correctness — that remains entirely the rules engine's responsibility — and should not be presented as improving accuracy.

---

## 8. Roles

- **Procurement Officer:** runs verification, completes Tier 2 manual checks, reviews AI recommendations, makes final qualify/disqualify decision, can override any AI/rules verdict with a mandatory logged reason
- **Admin:** manages tender-specific rule toggles (e.g. "MSME exemption applicable," "EPFO required"), manages Tier 3 mock-service fixture data via an admin toggle UI, views full audit logs

*(No bidder self-service role in MVP — see §3.2.)*

---

## 9. Dashboard

- **Per-bidder detail view:** compliance score, risk badge, per-check status grid (color-coded Pass/Fail/Pending/Manual-Review), side-by-side extracted-vs-verified field comparison, AI recommendation text, Tier 2 "Verify on Official Portal ↗" buttons, override control
- **Tender-level comparison view:** ranked table of all bidders by score/risk for a given tender
- **Audit export:** per-bidder PDF containing full verification history, timestamps, and officer actions

---

## 10. Sample Dataset

~25-30 synthetic bidders seeded into Tier 3 mock services and Tier 1 sandbox test accounts, with deliberately mixed compliance profiles: expired Udyam, GSTIN/PAN name mismatch, EPFO missing for an establishment with >20 employees, one blacklisted entity (static real published data), one fully clean bidder. This dataset is what makes the AI pipeline demonstrably work rather than trivially pass everything.

---

## 11. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + Tailwind |
| Backend | Python FastAPI |
| Database | PostgreSQL (or SQLite for local demo) |
| OCR | Tesseract (primary) + EasyOCR (fallback) |
| Extraction | NuExtract-3.8B (numind/NuExtract) |
| Recommendation LLM | Qwen2.5-3B-Instruct / Llama-3.2-3B-Instruct via Ollama |
| Fuzzy matching | RapidFuzz |
| Tier 1 integrations | Reseller REST APIs — team must create free-tier accounts before build (GST: e.g. Sandbox.co.in; EPFO/ESIC + MCA21 + PAN: e.g. Deepvue/AuthBridge) |
| Tier 3 mocks | Separate FastAPI service, seeded fixtures, admin toggle UI |
| Auth | Simple email/password + role (Officer/Admin) |
| Deployment | Docker, local or single cloud VM for demo |

---

## 12. Audit Trail Requirements

Every one of the following is logged with timestamp and actor:
- Every Tier 1 API query + raw response
- Every Tier 2 manual-verification entry (officer ID, portal result, optional screenshot)
- Every Tier 3 mock-service query
- Every document upload + extracted fields
- Every rules-engine verdict
- Every AI-generated recommendation
- Every officer override + mandatory reason text

---

## 13. Demo "Wow Moment"

Live re-verification loop: admin toggles a bidder's GST status in the Tier 3/mock admin panel (or, for a Tier 1 source, uses a real sandbox test GSTIN with a known non-compliant state) → officer clicks re-verify → AI flags the new inconsistency, score and risk level update in real time, recommendation text regenerates. This demonstrates the full value proposition — automated detection of change — in one continuous, honest, non-faked action.

---

## 14. Pre-Build Checklist (manual steps required before code generation can fully proceed)

1. Create free-tier developer accounts with one Tier 1 reseller each for GST, EPFO/ESIC, MCA21, PAN — confirm sandbox credit limits cover the demo dataset size
2. Technical spike: inspect manakonline.in "Search a License" and startupindia.gov.in blockchain-verify pages (network tab / page source) to confirm CAPTCHA-free status before building any automation attempt for these two — if either turns out to require CAPTCHA, move it to Tier 2 manual-only alongside Udyam
3. Source and store a static snapshot of published CVC/GeM debarred-vendor data for the Tier 3 blacklist mock
4. Confirm laptop hardware (RAM, GPU availability) to finalize local LLM model size (3B/3.8B assumed; drop to NuExtract-tiny 0.5B or a smaller Ollama model if hardware is constrained)

---

## 15. Expected Impact (per problem statement, achievable within this honest architecture)

- Meaningful reduction in verification effort for the 4 Tier 1 fully-automated sources + 5 Tier 3 mocked sources (structured, consistent, auditable even where mocked)
- Faster evaluation for Tier 2 sources via deep-linking and structured officer-input capture, even without full automation
- Improved consistency and auditability across all ten sources, regardless of tier
- Final qualify/disqualify authority remains with the Procurement Officer throughout — the platform is decision-support, not decision-making, exactly as the problem statement requires
