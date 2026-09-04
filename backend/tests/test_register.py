"""S1 — registration is admin-only and can never mint admin accounts."""


class TestRegister:
    def test_anonymous_register_rejected(self, seeded):
        client = seeded["client"]
        r = client.post("/api/auth/register", json={
            "email": "x@y.in", "full_name": "x", "password": "p", "role": "admin",
        })
        assert r.status_code == 401

    def test_officer_cannot_register(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        r = client.post("/api/auth/register", json={
            "email": "officer-made@y.in", "full_name": "Officer Made",
            "password": "Password@123", "role": "officer",
        }, headers=headers)
        assert r.status_code == 403

    def test_admin_cannot_create_admin_via_register(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.post("/api/auth/register", json={
            "email": "newadmin@y.in", "full_name": "New Admin",
            "password": "Password@123", "role": "admin",
        }, headers=headers)
        assert r.status_code == 403
        assert "officer role" in r.json()["detail"].lower()

    def test_admin_can_create_officer(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.post("/api/auth/register", json={
            "email": "new-officer@y.in", "full_name": "New Officer",
            "password": "Password@123", "role": "officer",
        }, headers=headers)
        assert r.status_code == 201
        assert r.json()["role"] == "officer"

    def test_admin_can_create_officer_without_role_field(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.post("/api/auth/register", json={
            "email": "default-role@y.in", "full_name": "Default Role",
            "password": "Password@123",
        }, headers=headers)
        assert r.status_code == 201
        assert r.json()["role"] == "officer"

    def test_newly_created_officer_has_officer_role(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.post("/api/auth/register", json={
            "email": "check-role@y.in", "full_name": "Check Role",
            "password": "Password@123", "role": "officer",
        }, headers=headers)
        assert r.status_code == 201
        login = client.post("/api/auth/login", json={
            "email": "check-role@y.in", "password": "Password@123",
        })
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "officer"


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]