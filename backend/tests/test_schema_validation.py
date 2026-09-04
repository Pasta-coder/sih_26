"""E4 — Tier-2 payload validation + explicit discrepancy semantics."""


class TestTier2Validation:
    def test_tier2_invalid_result_rejected(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        client.post(f"/api/compliance/run/{bidder_id}", headers=headers)
        r = client.post(f"/api/compliance/tier2-verify/{bidder_id}", json={
            "check_name": "udyam_msme", "result": "verified ",  # trailing space
        }, headers=headers)
        assert r.status_code == 422

    def test_tier2_unknown_check_name_rejected(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        r = client.post(f"/api/compliance/tier2-verify/{bidder_id}", json={
            "check_name": "made_up_check", "result": "verified",
        }, headers=headers)
        assert r.status_code == 422


class TestDiscrepancySemantics:
    def test_discrepancy_is_explicit_fail(self):
        from models.compliance import CheckStatus
        from services.rules_engine import rule_tier2
        verdict = rule_tier2("udyam_msme", "discrepancy")
        assert verdict["status"] == CheckStatus.fail
        assert "Override" in verdict["detail"]  # documented escape hatch


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]