"""E3 — officer-verified Tier-2 verdicts survive compliance re-runs."""


class TestTier2Preservation:
    def test_verified_verdict_survives_rerun(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id

        # 1. Run compliance → udyam is manual_review
        assert client.post(f"/api/compliance/run/{bidder_id}", headers=headers).status_code == 200
        udyam = _check_by_name(client, headers, bidder_id, "udyam_msme")
        assert udyam["status"] == "manual_review"

        # 2. Officer manually verifies Udyam
        r = client.post(f"/api/compliance/tier2-verify/{bidder_id}", json={
            "check_name": "udyam_msme", "result": "verified", "notes": "checked on portal",
        }, headers=headers)
        assert r.status_code == 200

        # 3. Re-run compliance (the demo wow-moment flow)
        assert client.post(f"/api/compliance/run/{bidder_id}", headers=headers).status_code == 200

        # 4. The officer's verdict must survive
        udyam = _check_by_name(client, headers, bidder_id, "udyam_msme")
        assert udyam["status"] == "pass"
        assert udyam["tier2_officer_result"] == "verified"
        assert udyam["tier2_verified_by"] is not None

    def test_rerun_preservation_is_audited(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        client.post(f"/api/compliance/run/{bidder_id}", headers=headers)
        client.post(f"/api/compliance/tier2-verify/{bidder_id}", json={
            "check_name": "udyam_msme", "result": "verified", "notes": "ok",
        }, headers=headers)
        client.post(f"/api/compliance/run/{bidder_id}", headers=headers)

        admin_client, admin_headers = _client_and_headers(seeded, "admin")
        r = admin_client.get(f"/api/audit/bidder/{bidder_id}", headers=admin_headers)
        descriptions = [e["description"] for e in r.json()]
        assert any("preserved" in d.lower() for d in descriptions)


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]


def _checks(client, headers, bidder_id):
    r = client.get(f"/api/compliance/{bidder_id}", headers=headers)
    assert r.status_code == 200
    return r.json()["checks"]


def _check_by_name(client, headers, bidder_id, name):
    return next(c for c in _checks(client, headers, bidder_id) if c["check_name"] == name)