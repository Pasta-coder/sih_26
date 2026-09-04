from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db
from models.bidder import Bidder, BidderStatus
from models.compliance import ComplianceCheck, ComplianceOverride, CheckStatus, CheckTier
from models.audit import AuditEventType
from models.user import User
from schemas.compliance import CheckResultOut, Tier2VerifyInput, OverrideInput, ComplianceRunOut
from auth_utils import get_current_user

from services.tier1 import gst, pan, epfo, mca21
from services.tier2.portals import udyam_verify_url, bis_verify_url, startup_india_verify_url
from services.tier3.blacklist import check_blacklist
from services.tier3.nsic import verify_nsic
from services.tier3.local_content import verify_local_content
from services.rules_engine import (
    rule_gst, rule_pan, rule_epfo, rule_mca,
    rule_blacklist, rule_tier2, rule_nsic, rule_make_in_india,
)
from services.scoring import compute_score
from services.recommendation import generate_recommendation
from services import audit_log as audit_svc

router = APIRouter()


async def _run_compliance_for_bidder(bidder: Bidder, tender_rules: dict, db: Session, actor_id: int | None):
    """
    Execute all compliance checks for a single bidder, persist results,
    compute score, generate recommendation. Returns list of check result dicts.
    """
    company = bidder.company_name

    # ── Preserve officer-verified Tier-2 results; delete the rest for re-run ──
    # (E3) An officer's manual verification on the official portal is ground truth
    # established by a human. Re-running automation must not silently erase it:
    # those rows are kept and re-included in this run's scoring unchanged, while
    # all automated rows (tier2_verified_by IS NULL) are refreshed. Overrides live
    # in the append-only ComplianceOverride table and are never deleted.
    existing_checks = (
        db.query(ComplianceCheck)
        .filter(ComplianceCheck.bidder_id == bidder.id)
        .all()
    )
    preserved = {
        c.check_name: c for c in existing_checks if c.tier2_verified_by is not None
    }
    db.query(ComplianceCheck).filter(
        ComplianceCheck.bidder_id == bidder.id,
        ComplianceCheck.tier2_verified_by.is_(None),
    ).delete(synchronize_session="fetch")  # evict deleted rows from identity map
    db.commit()

    check_results = [
        {"check_name": c.check_name, "status": c.status, "detail": c.detail}
        for c in preserved.values()
    ]
    if preserved:
        audit_svc.log_event(
            db,
            event_type=AuditEventType.compliance_run_started,
            bidder_id=bidder.id,
            actor_id=actor_id,
            description=(
                f"Compliance run started for {bidder.company_name} — "
                f"{len(preserved)} officer-verified Tier-2 result(s) preserved from previous run"
            ),
        )

    async def _save_check(name: str, tier: CheckTier, verdict: dict, raw: dict = None, portal_url: str = None):
        if name in preserved:
            # E3: officer-verified Tier-2 verdict survives re-runs — don't overwrite it.
            return
        status = verdict["status"]
        check = ComplianceCheck(
            bidder_id=bidder.id,
            check_name=name,
            check_tier=tier,
            status=status,
            detail=verdict.get("detail"),
            raw_response=raw,
            tier2_portal_url=portal_url,
        )
        db.add(check)
        db.commit()
        check_results.append({"check_name": name, "status": status, "detail": verdict.get("detail")})

        audit_svc.log_event(
            db,
            event_type=AuditEventType.rules_verdict,
            bidder_id=bidder.id,
            actor_id=actor_id,
            description=f"[{tier.value.upper()}] {name}: {status.value}",
            payload={"raw_response": raw, "verdict": verdict},
        )

    # ── Tier 1: GST ──────────────────────────────────────────────────────────
    gst_raw = await gst.verify_gst(bidder.gstin or "")
    audit_svc.log_event(db, AuditEventType.tier1_query, f"GST query for {bidder.gstin}",
                        bidder.id, actor_id, {"request": bidder.gstin, "response": gst_raw})
    await _save_check("gst_status", CheckTier.tier1, rule_gst(gst_raw, company), gst_raw)

    # ── Tier 1: PAN ──────────────────────────────────────────────────────────
    pan_raw = await pan.verify_pan(bidder.pan or "")
    audit_svc.log_event(db, AuditEventType.tier1_query, f"PAN query for {bidder.pan}",
                        bidder.id, actor_id, {"request": bidder.pan, "response": pan_raw})
    await _save_check("pan_validity", CheckTier.tier1, rule_pan(pan_raw, company), pan_raw)

    # ── Tier 1: EPFO ─────────────────────────────────────────────────────────
    epfo_required = tender_rules.get("epfo_required", True)
    # M4: MSME exemption — a bidder with a valid Udyam/MSME registration is
    # exempt from the EPFO requirement when the tender enables msme_exemption.
    if (
        epfo_required
        and tender_rules.get("msme_exemption", False)
        and bool(bidder.udyam_number)
    ):
        epfo_required = False
    epfo_raw = await epfo.verify_epfo(bidder.epfo_code or "")
    audit_svc.log_event(db, AuditEventType.tier1_query, f"EPFO query for {bidder.epfo_code}",
                        bidder.id, actor_id, {"request": bidder.epfo_code, "response": epfo_raw})
    await _save_check("epfo_registration", CheckTier.tier1, rule_epfo(epfo_raw, epfo_required), epfo_raw)

    # ── Tier 1: MCA21 ────────────────────────────────────────────────────────
    mca_raw = await mca21.verify_mca(bidder.cin or "")
    audit_svc.log_event(db, AuditEventType.tier1_query, f"MCA21 query for {bidder.cin}",
                        bidder.id, actor_id, {"request": bidder.cin, "response": mca_raw})
    await _save_check("mca_status", CheckTier.tier1, rule_mca(mca_raw), mca_raw)

    # ── Tier 2: Udyam ────────────────────────────────────────────────────────
    udyam_url_info = udyam_verify_url(bidder.udyam_number or "N/A")
    await _save_check(
        "udyam_msme", CheckTier.tier2,
        rule_tier2("udyam_msme", None),
        portal_url=udyam_url_info["url"]
    )

    # ── Tier 2: Startup India / DPIIT (always created; N/A unless claimed) ────
    # (M1) Every known check is created per bidder so the dashboard is a complete
    # checklist. Non-applicable checks are excluded from scoring and shown as N/A.
    if tender_rules.get("startup_india_eligible", False):
        si_url_info = startup_india_verify_url("")
        await _save_check("startup_india_dpiit", CheckTier.tier2,
                          rule_tier2("startup_india_dpiit", None),
                          portal_url=si_url_info["url"])
    else:
        await _save_check("startup_india_dpiit", CheckTier.tier2,
                          {"status": CheckStatus.not_applicable,
                           "detail": "Startup India/DPIIT recognition not claimed/required for this tender."})

    # ── Tier 2: BIS (always created; N/A when toggle off) ────────────────────
    if tender_rules.get("bis_required", False):
        bis_url_info = bis_verify_url("")
        await _save_check("bis_license", CheckTier.tier2, rule_tier2("bis_license", None),
                          portal_url=bis_url_info["url"])
    else:
        await _save_check("bis_license", CheckTier.tier2,
                          {"status": CheckStatus.not_applicable,
                           "detail": "BIS license not required for this tender."})

    # ── Tier 3: Blacklist ────────────────────────────────────────────────────
    bl_raw = check_blacklist(company, bidder.pan, bidder.gstin)
    audit_svc.log_event(db, AuditEventType.tier3_mock_query, f"Blacklist check for {company}",
                        bidder.id, actor_id, {"response": bl_raw})
    bl_verdict = rule_blacklist(bl_raw)
    await _save_check("blacklist", CheckTier.tier3, bl_verdict, bl_raw)

    # ── Tier 3: NSIC (always created) ────────────────────────────────────────
    # (M2) Previously dead code: verify_nsic was called with an empty number and
    # the result was never saved as a ComplianceCheck. Now bidders with an NSIC
    # number get a scored verdict; bidders without one get N/A.
    nsic_raw = verify_nsic(bidder.nsic_number or "", company)
    audit_svc.log_event(db, AuditEventType.tier3_mock_query, f"NSIC check for {company}",
                        bidder.id, actor_id, {"request": bidder.nsic_number, "response": nsic_raw})
    await _save_check("nsic_registration", CheckTier.tier3, rule_nsic(nsic_raw), nsic_raw)

    # ── Tier 3: Make in India local content (always created) ─────────────────
    # (M4) PS item #5: enforce the 50% local-content threshold when the tender
    # requires it; N/A otherwise.
    mii_raw = verify_local_content(company)
    mii_required = tender_rules.get("make_in_india", False)
    audit_svc.log_event(db, AuditEventType.tier3_mock_query,
                        f"Make in India local-content check for {company}",
                        bidder.id, actor_id, {"response": mii_raw})
    await _save_check("make_in_india", CheckTier.tier3,
                      rule_make_in_india(mii_raw, mii_required), mii_raw)

    # ── Score + Risk ──────────────────────────────────────────────────────────
    score, risk = compute_score(check_results)

    # ── Recommendation ────────────────────────────────────────────────────────
    pending_tier2 = [c["check_name"] for c in check_results if c["status"] == CheckStatus.manual_review]
    recommendation = generate_recommendation(company, score, risk, check_results, pending_tier2)
    audit_svc.log_event(db, AuditEventType.recommendation_generated, "Template recommendation generated",
                        bidder.id, actor_id, {"score": score, "risk": risk})

    # ── Persist to bidder ─────────────────────────────────────────────────────
    bidder.compliance_score = score
    bidder.risk_level = risk
    bidder.recommendation = recommendation
    bidder.status = BidderStatus.completed
    bidder.last_verified_at = datetime.now(timezone.utc)
    db.commit()

    return check_results


@router.post("/run/{bidder_id}", response_model=ComplianceRunOut)
async def run_compliance(
    bidder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run full compliance verification for a single bidder."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    tender_rules = bidder.tender.rule_toggles or {}
    bidder.status = BidderStatus.in_progress
    db.commit()

    audit_svc.log_event(db, AuditEventType.compliance_run_started,
                        f"Compliance run started for {bidder.company_name}",
                        bidder.id, current_user.id)

    await _run_compliance_for_bidder(bidder, tender_rules, db, current_user.id)

    audit_svc.log_event(db, AuditEventType.compliance_run_completed,
                        f"Compliance run completed: score={bidder.compliance_score}, risk={bidder.risk_level}",
                        bidder.id, current_user.id)

    checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    return ComplianceRunOut(
        bidder_id=bidder.id,
        company_name=bidder.company_name,
        compliance_score=bidder.compliance_score,
        risk_level=bidder.risk_level,
        recommendation=bidder.recommendation,
        checks=[CheckResultOut.model_validate(c) for c in checks],
    )


@router.post("/run-all/{tender_id}")
async def run_all_compliance(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run compliance for all bidders in a tender."""
    bidders = db.query(Bidder).filter(Bidder.tender_id == tender_id).all()
    if not bidders:
        raise HTTPException(status_code=404, detail="No bidders found for this tender")

    results = []
    for bidder in bidders:
        tender_rules = bidder.tender.rule_toggles or {}
        bidder.status = BidderStatus.in_progress
        db.commit()
        await _run_compliance_for_bidder(bidder, tender_rules, db, current_user.id)
        results.append({"bidder_id": bidder.id, "company_name": bidder.company_name,
                        "score": bidder.compliance_score, "risk": bidder.risk_level})

    return {"processed": len(results), "results": results}


@router.get("/{bidder_id}", response_model=ComplianceRunOut)
def get_compliance_results(
    bidder_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    return ComplianceRunOut(
        bidder_id=bidder.id,
        company_name=bidder.company_name,
        compliance_score=bidder.compliance_score,
        risk_level=bidder.risk_level,
        recommendation=bidder.recommendation,
        checks=[CheckResultOut.model_validate(c) for c in checks],
    )


@router.post("/tier2-verify/{bidder_id}")
def tier2_manual_verify(
    bidder_id: int,
    payload: Tier2VerifyInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Officer records result of Tier 2 manual portal verification."""
    check = (
        db.query(ComplianceCheck)
        .filter(ComplianceCheck.bidder_id == bidder_id, ComplianceCheck.check_name == payload.check_name)
        .first()
    )
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")

    verdict = rule_tier2(payload.check_name, payload.result)
    check.status = verdict["status"]
    check.detail = verdict["detail"]
    check.tier2_officer_result = payload.result
    check.tier2_officer_notes = payload.notes
    check.tier2_verified_by = current_user.id
    check.tier2_verified_at = datetime.now(timezone.utc)
    db.commit()

    # Recalculate score after officer input
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    all_checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    check_results = [{"check_name": c.check_name, "status": c.status, "detail": c.detail} for c in all_checks]
    score, risk = compute_score(check_results)
    pending_tier2 = [c["check_name"] for c in check_results if c["status"] == CheckStatus.manual_review]
    recommendation = generate_recommendation(bidder.company_name, score, risk, check_results, pending_tier2)

    bidder.compliance_score = score
    bidder.risk_level = risk
    bidder.recommendation = recommendation
    db.commit()

    audit_svc.log_event(
        db, AuditEventType.tier2_manual_verify,
        f"Officer manual verification: {payload.check_name} → {payload.result}",
        bidder_id, current_user.id,
        {"check": payload.check_name, "result": payload.result, "notes": payload.notes},
    )

    return {"message": "Verified", "new_score": score, "new_risk": risk}


@router.post("/override/{bidder_id}")
def officer_override(
    bidder_id: int,
    payload: OverrideInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Officer override of any check result. Reason is mandatory and logged."""
    # SECURITY (S2): The blacklist verdict is the system's hard auto-disqualifier
    # (PRD §6 — score 0/Critical regardless of all other checks). Only an admin
    # may override it, and always with written justification. Officers keep
    # override authority for all other checks (PRD §8).
    if payload.check_name == "blacklist" and current_user.role.value != "admin":
        raise HTTPException(
            status_code=403,
            detail="Blacklist verdicts are a hard auto-disqualifier and can only be "
                   "overridden by an Admin with written justification.",
        )

    check = (
        db.query(ComplianceCheck)
        .filter(ComplianceCheck.bidder_id == bidder_id, ComplianceCheck.check_name == payload.check_name)
        .first()
    )
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")

    original_status = check.status.value
    new_status = CheckStatus.pass_ if payload.new_status == "pass" else CheckStatus.fail
    check.status = new_status
    check.detail = f"[OFFICER OVERRIDE] {payload.reason} (Original: {original_status})"

    # Log override record
    override = ComplianceOverride(
        bidder_id=bidder_id,
        check_name=payload.check_name,
        original_status=original_status,
        overridden_status=payload.new_status,
        reason=payload.reason,
        officer_id=current_user.id,
    )
    db.add(override)

    # Recalculate score
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    all_checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    check_results = [{"check_name": c.check_name, "status": c.status, "detail": c.detail} for c in all_checks]
    score, risk = compute_score(check_results)
    pending_tier2 = [c["check_name"] for c in check_results if c["status"] == CheckStatus.manual_review]
    recommendation = generate_recommendation(bidder.company_name, score, risk, check_results, pending_tier2)
    bidder.compliance_score = score
    bidder.risk_level = risk
    bidder.recommendation = recommendation
    db.commit()

    audit_svc.log_event(
        db, AuditEventType.officer_override,
        f"Officer override: {payload.check_name} {original_status}→{payload.new_status}. Reason: {payload.reason}",
        bidder_id, current_user.id,
        {"check": payload.check_name, "original": original_status, "new": payload.new_status, "reason": payload.reason},
    )

    return {"message": "Override applied", "new_score": score, "new_risk": risk}
