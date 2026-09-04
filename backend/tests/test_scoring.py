"""Scoring invariants (Q1): weights sum, blacklist auto-zero, exclusions."""
from models.compliance import CheckStatus
from services.scoring import compute_score, CHECK_WEIGHTS


def _check(name, status, detail=None):
    return {"check_name": name, "status": status, "detail": detail}


ALL_PASS = [
    _check("gst_status", CheckStatus.pass_),
    _check("pan_validity", CheckStatus.pass_),
    _check("mca_status", CheckStatus.pass_),
    _check("epfo_registration", CheckStatus.pass_),
    _check("udyam_msme", CheckStatus.pass_),
    _check("make_in_india", CheckStatus.pass_),
    _check("bis_license", CheckStatus.pass_),
    _check("startup_india_dpiit", CheckStatus.pass_),
    _check("nsic_registration", CheckStatus.pass_),
]


class TestWeights:
    def test_weights_sum_to_100(self):
        assert sum(CHECK_WEIGHTS.values()) == 100.0

    def test_all_pass_scores_100_low(self):
        score, risk = compute_score(ALL_PASS)
        assert score == 100.0
        assert risk == "Low"

    def test_single_fail_reduces_score_proportionally(self):
        results = [_check("gst_status", CheckStatus.fail)] + ALL_PASS[1:]
        score, risk = compute_score(results)
        # gst = 20 of 100 weight fails → 80%
        assert score == 80.0
        assert risk == "Medium"


class TestBlacklist:
    def test_blacklist_fail_is_automatic_zero_critical(self):
        results = ALL_PASS + [_check("blacklist", CheckStatus.fail)]
        score, risk = compute_score(results)
        assert score == 0.0
        assert risk == "Critical"

    def test_blacklist_pass_does_not_affect_score(self):
        results = ALL_PASS + [_check("blacklist", CheckStatus.pass_)]
        score, _ = compute_score(results)
        assert score == 100.0


class TestExclusions:
    def test_manual_review_excluded_from_both_sides(self):
        # Udyam pending (manual_review) must not count against the bidder.
        results = ALL_PASS[:4] + [_check("udyam_msme", CheckStatus.manual_review)]
        score, _ = compute_score(results)
        assert score == 100.0

    def test_not_applicable_excluded_from_both_sides(self):
        results = [
            _check("gst_status", CheckStatus.pass_),
            _check("pan_validity", CheckStatus.pass_),
            _check("mca_status", CheckStatus.pass_),
            _check("epfo_registration", CheckStatus.not_applicable),
            _check("udyam_msme", CheckStatus.pass_),
        ]
        score, _ = compute_score(results)
        assert score == 100.0

    def test_missing_check_not_counted(self):
        # A check that simply doesn't exist is not scored.
        results = ALL_PASS[:5]
        score, _ = compute_score(results)
        assert score == 100.0

    def test_override_pass_restores_score(self):
        # Simulates: gst fails → officer overrides to pass → score back to full.
        failed = [_check("gst_status", CheckStatus.fail)] + ALL_PASS[1:]
        score_before, _ = compute_score(failed)
        assert score_before == 80.0
        score_after, _ = compute_score(ALL_PASS)
        assert score_after == 100.0