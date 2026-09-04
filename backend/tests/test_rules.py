"""Rules engine tests — the deterministic decision core.

Matrix coverage: every rule × (pass / fail / not_found / not_provided /
api_error / blank) so the E1/E4 fixes can't silently regress.
"""
import pytest

from models.compliance import CheckStatus
from services.rules_engine import (
    rule_gst, rule_pan, rule_epfo, rule_mca,
    rule_blacklist, rule_tier2, rule_nsic, rule_make_in_india,
)

BIDDER = "ACME SUPPLIERS PVT LTD"


# ── GST ───────────────────────────────────────────────────────────────────────
class TestRuleGst:
    def test_active_and_matching_name_passes(self):
        raw = {"status": "Active", "legal_name": "ACME SUPPLIERS PRIVATE LIMITED", "filing_status": {"missing": 0}}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.pass_

    def test_not_found_is_fail(self):
        raw = {"status": "Not Found", "error": "GSTIN not found in registry"}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.fail

    def test_cancelled_is_fail(self):
        raw = {"status": "Cancelled", "legal_name": BIDDER, "filing_status": {"missing": 2}}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.fail

    def test_name_mismatch_is_fail(self):
        raw = {"status": "Active", "legal_name": "SOME OTHER COMPANY LTD", "filing_status": {"missing": 0}}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.fail

    def test_too_many_missing_returns_is_fail(self):
        raw = {"status": "Active", "legal_name": BIDDER, "filing_status": {"missing": 4}}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.fail

    def test_blank_identifier_is_fail(self):
        raw = {"error": "GSTIN not provided", "status": "fail"}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.fail

    @pytest.mark.parametrize("status", ["api_error", "error"])
    def test_adapter_error_holds_for_manual_review(self, status):
        raw = {"error": "connection refused", "status": status}
        assert rule_gst(raw, BIDDER)["status"] == CheckStatus.manual_review


# ── PAN ───────────────────────────────────────────────────────────────────────
class TestRulePan:
    def test_valid_and_matching_name_passes(self):
        raw = {"status": "Valid", "name": "ACME SUPPLIERS PRIVATE LIMITED"}
        assert rule_pan(raw, BIDDER)["status"] == CheckStatus.pass_

    def test_invalid_is_fail(self):
        raw = {"status": "Invalid", "name": None}
        assert rule_pan(raw, BIDDER)["status"] == CheckStatus.fail

    def test_not_found_is_fail(self):
        raw = {"status": "Not Found", "error": "PAN not in registry"}
        assert rule_pan(raw, BIDDER)["status"] == CheckStatus.fail

    def test_blank_identifier_is_fail(self):
        raw = {"error": "PAN not provided", "status": "fail"}
        assert rule_pan(raw, BIDDER)["status"] == CheckStatus.fail

    @pytest.mark.parametrize("status", ["api_error", "error"])
    def test_adapter_error_holds_for_manual_review(self, status):
        raw = {"error": "timeout", "status": status}
        assert rule_pan(raw, BIDDER)["status"] == CheckStatus.manual_review


# ── EPFO ──────────────────────────────────────────────────────────────────────
class TestRuleEpfo:
    def test_active_passes(self):
        raw = {"status": "Active"}
        assert rule_epfo(raw, True)["status"] == CheckStatus.pass_

    def test_not_required_is_not_applicable(self):
        assert rule_epfo({"status": "Active"}, False)["status"] == CheckStatus.not_applicable

    def test_not_provided_is_fail(self):
        raw = {"error": "EPFO code not provided", "status": "not_provided"}
        assert rule_epfo(raw, True)["status"] == CheckStatus.fail

    def test_not_found_is_fail(self):
        raw = {"status": "Not Found", "error": "Establishment not registered"}
        assert rule_epfo(raw, True)["status"] == CheckStatus.fail

    @pytest.mark.parametrize("status", ["api_error", "error"])
    def test_adapter_error_holds_for_manual_review(self, status):
        raw = {"error": "500 from provider", "status": status}
        assert rule_epfo(raw, True)["status"] == CheckStatus.manual_review


# ── MCA21 ─────────────────────────────────────────────────────────────────────
class TestRuleMca:
    def test_active_passes(self):
        raw = {"status": "Active", "incorporation_date": "1973-05-08"}
        assert rule_mca(raw)["status"] == CheckStatus.pass_

    def test_struck_off_is_fail(self):
        raw = {"status": "Strike-off", "incorporation_date": "2015-01-15"}
        assert rule_mca(raw)["status"] == CheckStatus.fail

    def test_not_found_is_fail(self):
        raw = {"status": "Not Found", "error": "Company not found in MCA21"}
        assert rule_mca(raw)["status"] == CheckStatus.fail

    def test_blank_identifier_is_fail(self):
        raw = {"error": "CIN not provided", "status": "not_provided"}
        assert rule_mca(raw)["status"] == CheckStatus.fail

    @pytest.mark.parametrize("status", ["api_error", "error"])
    def test_adapter_error_holds_for_manual_review(self, status):
        raw = {"error": "rate limited", "status": status}
        assert rule_mca(raw)["status"] == CheckStatus.manual_review


# ── NSIC ──────────────────────────────────────────────────────────────────────
class TestRuleNsic:
    def test_valid_passes(self):
        raw = {"nsic_number": "NSIC/MH/2021/001234", "status": "Valid"}
        assert rule_nsic(raw)["status"] == CheckStatus.pass_

    def test_expired_is_fail(self):
        raw = {"nsic_number": "NSIC/DL/2020/005678", "status": "Expired"}
        assert rule_nsic(raw)["status"] == CheckStatus.fail

    def test_not_found_is_fail(self):
        raw = {"nsic_number": "NSIC/XX/0000/000000", "status": "Not Found"}
        assert rule_nsic(raw)["status"] == CheckStatus.fail

    def test_not_provided_is_not_applicable(self):
        raw = {"status": "not_provided", "note": "not submitted"}
        assert rule_nsic(raw)["status"] == CheckStatus.not_applicable

    def test_unknown_status_is_fail(self):
        assert rule_nsic({})["status"] == CheckStatus.fail


# ── Make in India ──────────────────────────────────────────────────────────────
class TestRuleMakeInIndia:
    def test_not_required_is_not_applicable(self):
        raw = {"local_content_percent": 72}
        assert rule_make_in_india(raw, False)["status"] == CheckStatus.not_applicable

    def test_meets_threshold_passes(self):
        raw = {"local_content_percent": 72}
        assert rule_make_in_india(raw, True)["status"] == CheckStatus.pass_

    def test_below_threshold_fails(self):
        raw = {"local_content_percent": 35}
        verdict = rule_make_in_india(raw, True)
        assert verdict["status"] == CheckStatus.fail
        assert "50%" in verdict["detail"]

    def test_missing_data_fails_when_required(self):
        raw = {"local_content_percent": None, "status": "not_provided"}
        assert rule_make_in_india(raw, True)["status"] == CheckStatus.fail


# ── Blacklist ─────────────────────────────────────────────────────────────────
class TestRuleBlacklist:
    def test_hit_is_automatic_fail(self):
        raw = {"blacklisted": True, "match": {"debarred_by": "CVC", "debarment_reason": "fraud", "debarment_date": "2023-01-01", "debarment_end_date": "2026-01-01"}}
        verdict = rule_blacklist(raw)
        assert verdict["status"] == CheckStatus.fail
        assert verdict.get("is_blacklisted") is True

    def test_clean_passes(self):
        raw = {"blacklisted": False, "match": None}
        assert rule_blacklist(raw)["status"] == CheckStatus.pass_


# ── Tier 2 ────────────────────────────────────────────────────────────────────
class TestRuleTier2:
    def test_no_officer_input_is_manual_review(self):
        assert rule_tier2("udyam_msme", None)["status"] == CheckStatus.manual_review

    def test_verified_passes(self):
        assert rule_tier2("udyam_msme", "verified")["status"] == CheckStatus.pass_

    def test_failed_is_fail(self):
        assert rule_tier2("udyam_msme", "failed")["status"] == CheckStatus.fail

    def test_discrepancy_is_fail(self):
        assert rule_tier2("udyam_msme", "discrepancy")["status"] == CheckStatus.fail