"""S2 — blacklist override RBAC + OverrideInput validation.

Also covers the existing audit-endpoint RBAC as regression coverage.
"""


class TestBlacklistOverride:
    def test_officer_cannot_override_blacklist(self, seeded, blacklisted_bidder):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = blacklisted_bidder.id
        assert client.post(f"/api/compliance/run/{bidder_id}", headers=headers).status_code == 200
        r = client.post(f"/api/compliance/override/{bidder_id}", json={
            "check_name": "blacklist", "new_status": "pass",
            "reason": "This entity is actually a different company with same name.",
        }, headers=headers)
        assert r.status_code == 403

    def test_admin_can_override_blacklist_with_reason(self, seeded, blacklisted_bidder):
        client, headers = _client_and_headers(seeded, "admin")
        bidder_id = blacklisted_bidder.id
        assert client.post(f"/api/compliance/run/{bidder_id}", headers=headers).status_code == 200
        r = client.post(f"/api/compliance/override/{bidder_id}", json={
            "check_name": "blacklist", "new_status": "pass",
            "reason": "Verified with vigilance dept — this is a name-collision case.",
        }, headers=headers)
        assert r.status_code == 200
        assert r.json()["new_score"] > 0  # auto-zero lifted by admin override

    def test_officer_can_override_normal_check(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        assert client.post(f"/api/compliance/run/{bidder_id}", headers=headers).status_code == 200
        r = client.post(f"/api/compliance/override/{bidder_id}", json={
            "check_name": "pan_validity", "new_status": "pass",
            "reason": "Officer re-checked on the official portal and confirmed validity.",
        }, headers=headers)
        assert r.status_code == 200

    def test_override_short_reason_rejected(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        bidder_id = seeded["bidder"].id
        client.post(f"/api/compliance/run/{bidder_id}", headers=headers)
        r = client.post(f"/api/compliance/override/{bidder_id}", json={
            "check_name": "pan_validity", "new_status": "pass", "reason": "short",
        }, headers=headers)
        assert r.status_code == 422

    def test_override_invalid_new_status_rejected(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        bidder_id = seeded["bidder"].id
        client.post(f"/api/compliance/run/{bidder_id}", headers=headers)
        r = client.post(f"/api/compliance/override/{bidder_id}", json={
            "check_name": "pan_validity", "new_status": "maybe",
            "reason": "This is a sufficiently long justification for the override.",
        }, headers=headers)
        assert r.status_code == 422


class TestAuditRbac:
    def test_officer_denied_full_audit(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        r = client.get("/api/audit/all", headers=headers)
        assert r.status_code == 403

    def test_admin_allowed_full_audit(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.get("/api/audit/all", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_officer_can_read_bidder_audit_trail(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        r = client.get(f"/api/audit/bidder/{bidder_id}", headers=headers)
        assert r.status_code == 200


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]