"""run-all end-to-end coverage: expected check rows + blacklist auto-zero."""


class TestRunAll:
    def test_run_all_creates_core_checks(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        tender_id = seeded["tender"].id
        r = client.post(f"/api/compliance/run-all/{tender_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["processed"] == 1

        names = {c["check_name"] for c in _checks(client, headers, seeded["bidder"].id)}
        # M1 convention: every known check is created per bidder (N/A when not
        # applicable) so the dashboard is a complete checklist.
        assert {
            "gst_status", "pan_validity", "mca_status", "epfo_registration",
            "udyam_msme", "blacklist", "nsic_registration", "make_in_india",
            "bis_license", "startup_india_dpiit",
        } <= names

    def test_run_blacklisted_bidder_scores_zero(self, seeded, blacklisted_bidder):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = blacklisted_bidder.id
        r = client.post(f"/api/compliance/run/{bidder_id}", headers=headers)
        assert r.status_code == 200
        data = client.get(f"/api/compliance/{bidder_id}", headers=headers).json()
        assert data["compliance_score"] == 0.0
        assert data["risk_level"] == "Critical"


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]


def _checks(client, headers, bidder_id):
    r = client.get(f"/api/compliance/{bidder_id}", headers=headers)
    assert r.status_code == 200
    return r.json()["checks"]