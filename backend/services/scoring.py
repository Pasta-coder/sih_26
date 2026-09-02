"""
Weighted Compliance Scoring Engine
────────────────────────────────────
Weighted by severity, not flat percentage.
See PRD §6 for full specification.

Check weights (sum = 100):
- blacklist:       AUTOMATIC 0 override if hit
- gst_status:      25 (mandatory statutory)
- pan_validity:    20 (mandatory statutory)
- mca_status:      15 (mandatory statutory)
- epfo_registration: 15 (conditional: tender rule toggle)
- udyam_msme:      10 (Tier 2 manual)
- bis_license:      5 (Tier 2 manual, conditional)
- startup_india:    5 (Tier 2 manual, conditional)
- nsic:             5 (Tier 3 mock)

Risk bands:
  90-100 → Low
  70-89  → Medium
  40-69  → High
  <40 or blacklisted → Critical
"""
from models.compliance import CheckStatus

CHECK_WEIGHTS: dict[str, float] = {
    "gst_status": 25.0,
    "pan_validity": 20.0,
    "mca_status": 15.0,
    "epfo_registration": 15.0,
    "udyam_msme": 10.0,
    "bis_license": 5.0,
    "startup_india_dpiit": 5.0,
    "nsic_registration": 5.0,
}

TOTAL_WEIGHT = sum(CHECK_WEIGHTS.values())  # 100.0


def compute_score(check_results: list[dict]) -> tuple[float, str]:
    """
    Args:
        check_results: list of dicts with keys 'check_name', 'status'
    Returns:
        (score: float 0-100, risk_level: str)
    """
    # Index checks by name
    checks_by_name = {c["check_name"]: c for c in check_results}

    # Blacklist auto-override
    blacklist = checks_by_name.get("blacklist")
    if blacklist and blacklist["status"] == CheckStatus.fail:
        return 0.0, "Critical"

    earned = 0.0
    applicable_weight = 0.0

    for check_name, weight in CHECK_WEIGHTS.items():
        check = checks_by_name.get(check_name)
        if check is None:
            continue

        status = check["status"]

        if status == CheckStatus.not_applicable:
            # Don't count not-applicable checks against the score
            continue

        applicable_weight += weight

        if status == CheckStatus.pass_:
            earned += weight
        elif status == CheckStatus.manual_review:
            # Pending Tier 2 — held, not assumed pass or fail
            # Exclude from scoring until officer records result
            applicable_weight -= weight  # don't include in denominator either
        # fail → 0 points for this check

    if applicable_weight == 0:
        return 0.0, "Critical"

    score = round((earned / applicable_weight) * 100, 1)
    risk = _risk_band(score)
    return score, risk


def _risk_band(score: float) -> str:
    if score >= 90:
        return "Low"
    elif score >= 70:
        return "Medium"
    elif score >= 40:
        return "High"
    else:
        return "Critical"
