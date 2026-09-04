"""
AI Recommendation Engine — Python Template-Based (Option B)
─────────────────────────────────────────────────────────────
Generates structured, human-readable compliance recommendations for the
Procurement Officer based entirely on the rules-engine output.

Design principles:
  1. NEVER makes a compliance decision — narrates the rules engine's decisions
  2. Deterministic: same input → same output (critical for auditability)
  3. Data-sovereign: bidder PAN/GST/financial data never leaves the server
  4. Fast: no API latency, works fully offline
  5. Transparent: every sentence maps to a specific rules-engine finding

This is a stronger engineering choice than a cloud LLM for a compliance/
legal tool where consistency and auditability are the primary requirements.
"""

from models.compliance import CheckStatus


# ─── Risk-level narrative openers ─────────────────────────────────────────────

RISK_OPENERS = {
    "Critical": (
        "This bidder presents a **CRITICAL compliance risk** and is recommended for "
        "immediate disqualification pending review."
    ),
    "High": (
        "This bidder presents a **HIGH compliance risk** with significant statutory "
        "failures requiring resolution before award."
    ),
    "Medium": (
        "This bidder presents a **MEDIUM compliance risk**. Minor issues have been "
        "identified that warrant officer attention before finalizing award."
    ),
    "Low": (
        "This bidder presents a **LOW compliance risk** and appears to meet all "
        "applicable statutory and tender-specific requirements."
    ),
}

# ─── Per-check finding templates ──────────────────────────────────────────────

CHECK_LABELS = {
    "gst_status": "GST Registration",
    "pan_validity": "PAN Validity",
    "mca_status": "MCA21 Company Status",
    "epfo_registration": "EPFO Registration",
    "udyam_msme": "Udyam/MSME Registration",
    "make_in_india": "Make in India Local Content",
    "bis_license": "BIS License",
    "startup_india_dpiit": "Startup India / DPIIT Recognition",
    "nsic_registration": "NSIC Registration",
    "blacklist": "Blacklist / Debarment Check",
}

STATUS_PHRASES = {
    CheckStatus.pass_: "✅ Passed",
    CheckStatus.fail: "❌ Failed",
    CheckStatus.manual_review: "⏳ Pending Officer Verification",
    CheckStatus.not_applicable: "➖ Not Applicable",
    CheckStatus.pending: "⏳ Not Yet Verified",
}


def generate_recommendation(
    company_name: str,
    score: float,
    risk_level: str,
    check_results: list[dict],
    pending_tier2_checks: list[str] = None,
) -> str:
    """
    Generate a structured natural-language compliance recommendation.

    Args:
        company_name: Bidder's company name
        score: Computed compliance score (0–100)
        risk_level: Low / Medium / High / Critical
        check_results: List of {check_name, status, detail} dicts from rules engine
        pending_tier2_checks: Names of Tier 2 checks still awaiting officer input

    Returns:
        Multi-paragraph recommendation string (Markdown-formatted)
    """
    pending_tier2_checks = pending_tier2_checks or []
    checks_by_name = {c["check_name"]: c for c in check_results}

    # ── Opener ────────────────────────────────────────────────────────────────
    opener = RISK_OPENERS.get(risk_level, RISK_OPENERS["High"])
    header = (
        f"### Compliance Recommendation: {company_name}\n\n"
        f"**Compliance Score:** {score}/100 &nbsp;|&nbsp; **Risk Level:** {risk_level}\n\n"
        f"{opener}\n"
    )

    # ── Blacklist critical block ───────────────────────────────────────────────
    blacklist_block = ""
    bl = checks_by_name.get("blacklist")
    if bl and bl["status"] == CheckStatus.fail:
        blacklist_block = (
            "\n> ⛔ **AUTOMATIC DISQUALIFICATION TRIGGERED**\n"
            f"> {bl.get('detail', '')}\n"
            "> No further scoring applies. Override requires Admin-level written justification.\n"
        )

    # ── Failed checks ─────────────────────────────────────────────────────────
    failed = [c for c in check_results if c["status"] == CheckStatus.fail and c["check_name"] != "blacklist"]
    failed_block = ""
    if failed:
        failed_block = "\n#### ❌ Failed Checks\n"
        for c in failed:
            label = CHECK_LABELS.get(c["check_name"], c["check_name"])
            failed_block += f"- **{label}:** {c.get('detail', 'No detail available.')}\n"

    # ── Pending Tier 2 block ───────────────────────────────────────────────────
    pending_block = ""
    pending = [c for c in check_results if c["status"] == CheckStatus.manual_review]
    if pending:
        pending_block = "\n#### ⏳ Awaiting Officer Manual Verification\n"
        for c in pending:
            label = CHECK_LABELS.get(c["check_name"], c["check_name"])
            pending_block += (
                f"- **{label}:** Use the 'Verify on Official Portal ↗' button "
                f"to complete this check. Score will update once result is recorded.\n"
            )

    # ── Passed checks ─────────────────────────────────────────────────────────
    passed = [c for c in check_results if c["status"] == CheckStatus.pass_]
    passed_block = ""
    if passed:
        passed_block = "\n#### ✅ Passed Checks\n"
        for c in passed:
            label = CHECK_LABELS.get(c["check_name"], c["check_name"])
            passed_block += f"- **{label}:** {c.get('detail', 'Verified.')}\n"

    # ── Not applicable ────────────────────────────────────────────────────────
    na = [c for c in check_results if c["status"] == CheckStatus.not_applicable]
    na_block = ""
    if na:
        na_block = "\n#### ➖ Not Applicable for This Tender\n"
        for c in na:
            label = CHECK_LABELS.get(c["check_name"], c["check_name"])
            na_block += f"- **{label}:** {c.get('detail', 'Not required.')}\n"

    # ── Action recommendation ──────────────────────────────────────────────────
    action = _action_recommendation(score, risk_level, failed, pending, bl)

    # ── Audit disclaimer ──────────────────────────────────────────────────────
    disclaimer = (
        "\n---\n*This recommendation is generated by the rules engine based on automated "
        "and officer-verified data. The final qualify/disqualify decision rests with "
        "the Procurement Officer. Any override must include a written justification, "
        "which is logged in the immutable audit trail.*"
    )

    return "".join([
        header,
        blacklist_block,
        failed_block,
        pending_block,
        passed_block,
        na_block,
        "\n#### 📋 Recommended Action\n",
        action,
        disclaimer,
    ])


def _action_recommendation(
    score: float,
    risk_level: str,
    failed_checks: list[dict],
    pending_checks: list[dict],
    blacklist_check: dict | None,
) -> str:
    if blacklist_check and blacklist_check["status"] == CheckStatus.fail:
        return (
            "**Immediate Disqualification Recommended.** This entity appears on "
            "the CVC/GeM debarred vendor list. Do not proceed to award. "
            "Contact your legal/vigilance department if you believe this is an error.\n"
        )

    if not failed_checks and not pending_checks:
        return (
            "**Proceed to Award Evaluation.** All automated and manual checks have "
            "passed. This bidder meets all statutory and tender-specific compliance "
            "requirements. No further compliance action needed.\n"
        )

    if failed_checks and not pending_checks:
        check_names = ", ".join(
            CHECK_LABELS.get(c["check_name"], c["check_name"]) for c in failed_checks
        )
        return (
            f"**Disqualification Recommended.** The following mandatory checks have failed: "
            f"{check_names}. Request the bidder to provide corrective documentation or "
            f"clarification. If no satisfactory response is received, disqualify the bid. "
            f"Document your decision in the override log if proceeding despite failures.\n"
        )

    if pending_checks:
        check_names = ", ".join(
            CHECK_LABELS.get(c["check_name"], c["check_name"]) for c in pending_checks
        )
        msg = (
            f"**Action Required: Complete Manual Verification.** "
            f"The following checks require officer manual verification before a final "
            f"decision can be made: {check_names}. "
            f"Use the 'Verify on Official Portal ↗' buttons to complete these checks.\n"
        )
        if failed_checks:
            fail_names = ", ".join(
                CHECK_LABELS.get(c["check_name"], c["check_name"]) for c in failed_checks
            )
            msg += (
                f"Additionally, the following checks have failed: {fail_names}. "
                f"Consider these when making your final determination.\n"
            )
        return msg

    return "**Hold for further review.** Contact your procurement supervisor.\n"
