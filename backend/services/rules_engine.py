"""
Deterministic Rules Engine
───────────────────────────
The ONLY component that makes compliance decisions.
The recommendation engine NEVER makes decisions — it only narrates them.

Per-check verdict: Pass | Fail | Pending | Manual-Review | Not-Applicable
"""
from rapidfuzz import fuzz
from models.compliance import CheckStatus


# Name-match threshold: 80% similarity covers common abbreviations
# (e.g. "Reliance Industries Ltd" vs "RELIANCE INDUSTRIES LIMITED")
NAME_MATCH_THRESHOLD = 80


def _name_match(name_a: str, name_b: str) -> bool:
    if not name_a or not name_b:
        return False
    score = fuzz.token_sort_ratio(name_a.upper().strip(), name_b.upper().strip())
    return score >= NAME_MATCH_THRESHOLD


def rule_gst(gst_result: dict, bidder_name: str) -> dict:
    """
    GST check rules:
    - FAIL if status is not 'Active'
    - FAIL if registered name doesn't fuzzy-match bidder name
    - FAIL if >2 of last 6 GSTR-3B returns are missing
    - MANUAL-REVIEW (held, not failed) if the external service itself errored
    """
    # E1: A transient adapter/registry outage is a system failure, not a bidder
    # finding — hold the check for manual re-check instead of auto-failing.
    if gst_result.get("status") in ("api_error", "error"):
        return {
            "status": CheckStatus.manual_review,
            "detail": "External verification service unavailable. Awaiting manual/officer re-check.",
        }

    if "error" in gst_result and gst_result.get("status") == "Not Found":
        return {"status": CheckStatus.fail, "detail": "GSTIN not found in GST registry."}

    # E2: distinguish "bidder never provided the number" from "registry says bad"
    if gst_result.get("status") == "fail" and "not provided" in (gst_result.get("error") or ""):
        return {
            "status": CheckStatus.fail,
            "detail": "GSTIN not provided on bidder record — required for this tender.",
        }

    if gst_result.get("status", "").lower() != "active":
        return {
            "status": CheckStatus.fail,
            "detail": f"GST registration is {gst_result.get('status', 'Unknown')}. "
                      f"Active status required for participation.",
        }

    # Name match
    registered_name = gst_result.get("legal_name", "")
    if not _name_match(registered_name, bidder_name):
        return {
            "status": CheckStatus.fail,
            "detail": f"GST registered name '{registered_name}' does not match "
                      f"bidder name '{bidder_name}' (fuzzy similarity < {NAME_MATCH_THRESHOLD}%).",
        }

    # Filing status
    filing = gst_result.get("filing_status", {})
    missing = filing.get("missing", 0)
    if missing > 2:
        return {
            "status": CheckStatus.fail,
            "detail": f"{missing} of last 6 GSTR-3B returns are missing. Maximum 2 missing returns allowed.",
        }

    return {"status": CheckStatus.pass_, "detail": f"GST Active. Returns: {6 - missing}/6 filed."}


def rule_pan(pan_result: dict, bidder_name: str) -> dict:
    """PAN must be Valid and name must fuzzy-match."""
    # E1: External-service errors are held for manual re-check, not scored as a failure.
    if pan_result.get("status") in ("api_error", "error"):
        return {
            "status": CheckStatus.manual_review,
            "detail": "External verification service unavailable. Awaiting manual/officer re-check.",
        }

    # E2: distinguish "bidder never provided the number" from "registry says bad"
    if pan_result.get("status") == "fail" and "not provided" in (pan_result.get("error") or ""):
        return {
            "status": CheckStatus.fail,
            "detail": "PAN not provided on bidder record — required for this tender.",
        }

    if pan_result.get("status", "").lower() not in ("valid",):
        return {
            "status": CheckStatus.fail,
            "detail": f"PAN status: {pan_result.get('status', 'Unknown')}. Valid PAN required.",
        }

    registered_name = pan_result.get("name", "")
    if not _name_match(registered_name, bidder_name):
        return {
            "status": CheckStatus.fail,
            "detail": f"PAN registered name '{registered_name}' does not match bidder name '{bidder_name}'.",
        }

    return {"status": CheckStatus.pass_, "detail": f"PAN Valid. Name verified."}


def rule_epfo(epfo_result: dict, epfo_required: bool = True) -> dict:
    """EPFO required for establishments with >20 employees (tender-rule-toggled)."""
    if not epfo_required:
        return {"status": CheckStatus.not_applicable, "detail": "EPFO check not required for this tender."}

    # E1: External-service errors are held for manual re-check, not scored as a failure.
    if epfo_result.get("status") in ("api_error", "error"):
        return {
            "status": CheckStatus.manual_review,
            "detail": "External verification service unavailable. Awaiting manual/officer re-check.",
        }

    if epfo_result.get("status") == "not_provided":
        return {
            "status": CheckStatus.fail,
            "detail": "EPFO code not provided on bidder record — required for this tender.",
        }

    if epfo_result.get("status", "").lower() not in ("active",):
        return {
            "status": CheckStatus.fail,
            "detail": f"EPFO registration status: {epfo_result.get('status', 'Unknown')}.",
        }

    return {"status": CheckStatus.pass_, "detail": "EPFO registration Active."}


def rule_mca(mca_result: dict) -> dict:
    """Company must be Active in MCA21."""
    # E1: External-service errors are held for manual re-check, not scored as a failure.
    if mca_result.get("status") in ("api_error", "error"):
        return {
            "status": CheckStatus.manual_review,
            "detail": "External verification service unavailable. Awaiting manual/officer re-check.",
        }

    status = mca_result.get("status", "")

    if "error" in mca_result and status == "Not Found":
        return {"status": CheckStatus.fail, "detail": "Company not found in MCA21 registry."}

    # E2: distinguish "bidder never provided the number" from "registry says bad"
    if status == "not_provided":
        return {
            "status": CheckStatus.fail,
            "detail": "CIN not provided on bidder record — required for this tender.",
        }

    if status.lower() not in ("active",):
        return {
            "status": CheckStatus.fail,
            "detail": f"Company status in MCA21: '{status}'. Active status required.",
        }

    return {"status": CheckStatus.pass_, "detail": f"Company Active in MCA21 since {mca_result.get('incorporation_date', 'N/A')}."}


def rule_nsic(nsic_result: dict) -> dict:
    """
    NSIC registration check (Tier 3 mock).
    - PASS if status is Valid
    - FAIL if Expired or not found in the registry
    - N/A if the bidder did not provide a number (registration not claimed)
    """
    status = nsic_result.get("status")
    if status == "not_provided":
        return {
            "status": CheckStatus.not_applicable,
            "detail": "NSIC registration number not provided on bidder record — not claimed.",
        }
    if status == "Not Found":
        return {
            "status": CheckStatus.fail,
            "detail": "NSIC number not found in NSIC registry.",
        }
    if status != "Valid":
        return {
            "status": CheckStatus.fail,
            "detail": f"NSIC registration status: {status}. Active registration required.",
        }
    return {"status": CheckStatus.pass_, "detail": "NSIC registration valid."}


def rule_make_in_india(mii_result: dict, required: bool = False) -> dict:
    """
    Make in India local-content check (PS item #5).
    - N/A when the tender does not require local content
    - FAIL when declared local content is below the 50% threshold
    - PASS when local content is >= 50%
    """
    if not required:
        return {
            "status": CheckStatus.not_applicable,
            "detail": "Make in India local-content requirement not applicable for this tender.",
        }

    percent = mii_result.get("local_content_percent")
    if percent is None:
        return {
            "status": CheckStatus.fail,
            "detail": "Local-content data not provided on bidder record — required for this tender.",
        }
    if percent < 50:
        return {
            "status": CheckStatus.fail,
            "detail": f"Local content {percent}% does not meet the 50% Make in India threshold.",
        }
    return {
        "status": CheckStatus.pass_,
        "detail": f"Local content {percent}% meets the 50% Make in India threshold.",
    }


def rule_blacklist(blacklist_result: dict) -> dict:
    """Blacklisting is an automatic disqualifier — overrides all other checks."""
    if blacklist_result.get("blacklisted"):
        match = blacklist_result["match"]
        return {
            "status": CheckStatus.fail,
            "detail": (
                f"CRITICAL: Entity found on CVC/GeM debarred vendor list. "
                f"Debarred by: {match.get('debarred_by')}. "
                f"Reason: {match.get('debarment_reason')}. "
                f"Debarment period: {match.get('debarment_date')} to {match.get('debarment_end_date')}."
            ),
            "is_blacklisted": True,
        }
    return {"status": CheckStatus.pass_, "detail": "No match found on debarred vendor lists."}


def rule_tier2(check_name: str, officer_result: str | None) -> dict:
    """Tier 2 checks are Pending until officer records a result."""
    if not officer_result:
        return {
            "status": CheckStatus.manual_review,
            "detail": f"Awaiting Procurement Officer manual verification on official portal.",
        }
    if officer_result.lower() == "verified":
        return {"status": CheckStatus.pass_, "detail": "Manually verified by Procurement Officer."}
    if officer_result.lower() == "failed":
        return {"status": CheckStatus.fail, "detail": "Procurement Officer recorded: FAILED on official portal."}
    # E4: "discrepancy" is an explicit officer-recorded Fail (names/details on the
    # statutory ID don't match the bidder record). It can be cleared only via the
    # Override flow, which requires a written justification.
    return {
        "status": CheckStatus.fail,
        "detail": (
            "Procurement Officer recorded a discrepancy on the official portal — "
            "recorded as Fail. Use Override (with written justification) to clear "
            "if determined benign."
        ),
    }
