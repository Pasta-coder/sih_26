"""M3 (documents) + M4 (MSME exemption) API tests."""


class TestDocumentUpload:
    def test_upload_creates_document_and_consistency_report(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id

        r = client.post(
            f"/api/documents/upload/{bidder_id}",
            data={"doc_type": "pan_card"},
            files={"file": ("pan.txt", b"AAACR5055K ACME SUPPLIERS PVT LTD", "text/plain")},
            headers=headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["doc_type"] == "pan_card"

        # Uploaded doc appears in the consistency report (advisory).
        r = client.get(f"/api/documents/consistency/{bidder_id}", headers=headers)
        assert r.status_code == 200
        report = r.json()
        assert report["company_name"] == "ACME SUPPLIERS PVT LTD"
        assert len(report["documents"]) == 1
        assert report["documents"][0]["doc_type"] == "pan_card"

    def test_invalid_doc_type_rejected(self, seeded):
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        r = client.post(
            f"/api/documents/upload/{bidder_id}",
            data={"doc_type": "hacking_script"},
            files={"file": ("x.txt", b"data", "text/plain")},
            headers=headers,
        )
        assert r.status_code == 400

    def test_oversized_upload_rejected(self, seeded, monkeypatch):
        from config import get_settings
        monkeypatch.setattr(get_settings(), "max_upload_size_mb", 1)
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id
        big = b"x" * (2 * 1024 * 1024)  # 2 MB > 1 MB limit
        r = client.post(
            f"/api/documents/upload/{bidder_id}",
            data={"doc_type": "pan_card"},
            files={"file": ("big.txt", big, "text/plain")},
            headers=headers,
        )
        assert r.status_code == 413

    def test_consistency_flags_mismatch(self, seeded):
        """Extract path can't run without OCR libs here, so simulate a stored doc."""
        from database import SessionLocal
        from models.bidder import BidderDocument
        client, headers = _client_and_headers(seeded, "officer")
        bidder_id = seeded["bidder"].id

        session = SessionLocal()
        doc = BidderDocument(
            bidder_id=bidder_id,
            doc_type="pan_card",
            filename="pan_card_mismatch.txt",
            filepath="/tmp/none",
            extracted_fields={"raw_ids_found": {"pan": "ZZZZZ0000Z"}, "name": "SOME OTHER COMPANY"},
        )
        session.add(doc)
        session.commit()
        session.close()

        r = client.get(f"/api/documents/consistency/{bidder_id}", headers=headers)
        statuses = {c["field"]: c["status"] for c in r.json()["documents"][0]["checks"]}
        assert statuses["pan"] == "mismatch"
        assert statuses["name"] == "mismatch"


class TestAdminToggles:
    """Regression: rule-toggle PATCH must actually persist (in-place dict mutation
    was invisible to SQLAlchemy change tracking)."""
    def test_toggle_persists_after_patch(self, seeded):
        client, headers = _client_and_headers(seeded, "admin")
        r = client.patch(
            f"/api/admin/mock-toggle/{seeded['tender'].id}",
            json={"msme_exemption": True},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["rule_toggles"]["msme_exemption"] is True
        # A fresh read (new session) must also see the persisted toggle.
        t = client.get(f"/api/tenders/{seeded['tender'].id}", headers=headers).json()
        assert t["rule_toggles"]["msme_exemption"] is True


class TestMsmeExemption:
    def test_epfo_waived_when_msme_exemption_on_and_udyam_present(self, seeded):
        from database import SessionLocal
        from models.bidder import Bidder
        session = SessionLocal()
        bidder = Bidder(
            tender_id=seeded["tender"].id,
            company_name="MSME MICRO UNIT PVT LTD",
            gstin="27AAACR5055K1ZK",
            pan="AAACR5055K",
            cin="L17110MH1973PLC019786",
            udyam_number="UDYAM-MH-27-0003333",
            epfo_code=None,
        )
        session.add(bidder)
        session.commit()
        session.refresh(bidder)
        bidder_id = bidder.id
        session.close()

        # Turn the MSME exemption toggle on for this tender.
        client, headers = _client_and_headers(seeded, "admin")
        r = client.patch(
            f"/api/admin/mock-toggle/{seeded['tender'].id}",
            json={"msme_exemption": True},
            headers=headers,
        )
        assert r.status_code == 200

        r = client.post(f"/api/compliance/run/{bidder_id}", headers=_client_and_headers(seeded, "officer")[1])
        assert r.status_code == 200
        checks = client.get(f"/api/compliance/{bidder_id}", headers=headers).json()["checks"]
        epfo = next(c for c in checks if c["check_name"] == "epfo_registration")
        assert epfo["status"] == "not_applicable"

    def test_epfo_required_when_no_udyam_registration(self, seeded):
        from database import SessionLocal
        from models.bidder import Bidder
        session = SessionLocal()
        bidder = Bidder(
            tender_id=seeded["tender"].id,
            company_name="NO UDYAM FIRM",
            gstin="27AAACR5055K1ZK",
            pan="AAACR5055K",
            cin="L17110MH1973PLC019786",
            udyam_number=None,
            epfo_code=None,
        )
        session.add(bidder)
        session.commit()
        session.refresh(bidder)
        bidder_id = bidder.id
        session.close()

        client, admin_headers = _client_and_headers(seeded, "admin")
        client.patch(f"/api/admin/mock-toggle/{seeded['tender'].id}", json={"msme_exemption": True}, headers=admin_headers)
        r = client.post(f"/api/compliance/run/{bidder_id}", headers=_client_and_headers(seeded, "officer")[1])
        assert r.status_code == 200
        checks = client.get(f"/api/compliance/{bidder_id}", headers=admin_headers).json()["checks"]
        epfo = next(c for c in checks if c["check_name"] == "epfo_registration")
        assert epfo["status"] == "fail"  # required but not provided


def _client_and_headers(seeded, role):
    return seeded["client"], seeded[f"{role}_headers"]