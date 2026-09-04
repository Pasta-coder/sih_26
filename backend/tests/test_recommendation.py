"""Recommendation engine tests (Q1): determinism + guardrails."""
from models.compliance import CheckStatus
from services.recommendation import generate_recommendation


def _check(name, status, detail=None):
    return {"check_name": name, "status": status, "detail": detail}


ALL_PASS = [
    _check("gst_status", CheckStatus.pass_, "GST Active"),
    _check("pan_validity", CheckStatus.pass_, "PAN Valid"),
    _check("mca_status", CheckStatus.pass_, "Company Active"),
    _check("epfo_registration", CheckStatus.pass_, "EPFO Active"),
    _check("udyam_msme", CheckStatus.pass_, "Manually verified"),
    _check("blacklist", CheckStatus.pass_, "No match"),
]


class TestDeterminism:
    def test_same_input_same_output(self):
        a = generate_recommendation("ACME LTD", 90.0, "Low", ALL_PASS, [])
        b = generate_recommendation("ACME LTD", 90.0, "Low", ALL_PASS, [])
        assert a == b


class TestGuardrails:
    def test_blacklist_fail_mentions_automatic_disqualification(self):
        results = ALL_PASS + [_check("blacklist", CheckStatus.fail, "CRITICAL: found on list")]
        text = generate_recommendation("ACME LTD", 0.0, "Critical", results, [])
        assert "AUTOMATIC DISQUALIFICATION TRIGGERED" in text
        assert "Immediate Disqualification Recommended" in text

    def test_never_proceed_to_award_while_pending(self):
        results = [
            _check("gst_status", CheckStatus.pass_, "GST Active"),
            _check("udyam_msme", CheckStatus.manual_review, "Awaiting officer"),
        ]
        text = generate_recommendation("ACME LTD", 100.0, "Low", results, ["udyam_msme"])
        assert "Proceed to Award" not in text
        assert "Complete Manual Verification" in text

    def test_proceed_to_award_when_all_clear(self):
        text = generate_recommendation("ACME LTD", 100.0, "Low", ALL_PASS, [])
        assert "Proceed to Award Evaluation" in text