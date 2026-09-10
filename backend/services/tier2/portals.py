"""
Tier 2 Deep-Link Generators
────────────────────────────
These generate the URL the Procurement Officer clicks to open the
official government verification portal, with the lookup value
pre-filled where the portal URL structure allows it.
The officer completes verification manually and records the result
back into the system.
"""


def udyam_verify_url(udyam_number: str) -> dict:
    """
    Udyam Registration verification — CAPTCHA on every lookup.
    No automation possible. Deep-link to verify page.
    """
    return {
        "portal": "udyamregistration.gov.in",
        "url": "https://udyamregistration.gov.in/Government-India/Ministry-MSME-verification.htm",
        "direct_url": "https://udyamregistration.gov.in/Government-India/Ministry-MSME-verification.htm",
        "lookup_value": udyam_number,
        "portal_name": "Udyam Registration Portal — Ministry of MSME",
        "steps": [
            "Click 'Verify Udyam Registration Certificate' on the portal",
            f"Enter Udyam Number: {udyam_number}",
            "Complete the CAPTCHA and submit",
            "Record the verified registration status below",
        ],
        "instruction": (
            f"Open the Udyam portal, click 'Verify Udyam Registration Certificate', "
            f"and enter: {udyam_number}. Complete CAPTCHA and record the result."
        ),
    }


def bis_verify_url(license_number: str) -> dict:
    """
    BIS ISI / CRS license verification via Manak Online.
    Search by license number on the portal.
    """
    return {
        "portal": "manakonline.in",
        "url": "https://www.manakonline.in/MANA/searchLicense.do",
        "direct_url": "https://www.manakonline.in/MANA/searchLicense.do",
        "lookup_value": license_number,
        "portal_name": "Manak Online — Bureau of Indian Standards",
        "steps": [
            "Open the BIS Manak Online portal",
            "Select 'Search a License' from the menu",
            f"Enter License Number: {license_number or 'as submitted by bidder'}",
            "Verify the license is Active and not expired",
            "Record the result below",
        ],
        "instruction": (
            f"Open Manak Online, use 'Search a License', "
            f"and enter: {license_number or 'the bidder license number'}. Record the result."
        ),
    }


def startup_india_verify_url(dpiit_number: str) -> dict:
    """
    DPIIT / Startup India recognition certificate verification.
    """
    return {
        "portal": "startupindia.gov.in",
        "url": "https://www.startupindia.gov.in/content/sih/en/certificate-verification.html",
        "direct_url": "https://www.startupindia.gov.in/content/sih/en/certificate-verification.html",
        "lookup_value": dpiit_number,
        "portal_name": "Startup India — DPIIT Certificate Verification",
        "steps": [
            "Open the Startup India verification portal",
            f"Enter DPIIT/Certificate Number: {dpiit_number or 'as provided by bidder'}",
            "Check that the startup status is Active and not expired",
            "Record the result below",
        ],
        "instruction": (
            f"Open Startup India portal and verify certificate number: "
            f"{dpiit_number or 'as provided'}. Record the result."
        ),
    }


# ── Additional useful reference portals ───────────────────────────────────────
REFERENCE_PORTALS = {
    "gst": {
        "name": "GST Taxpayer Search",
        "url": "https://www.gst.gov.in/taxpayersearch",
        "description": "Search any GSTIN to verify registration status (Tier 1 — auto-checked)",
    },
    "pan": {
        "name": "Income Tax PAN Verification",
        "url": "https://www.incometax.gov.in/iec/foportal/",
        "description": "Verify PAN validity on Income Tax portal (Tier 1 — auto-checked)",
    },
    "epfo": {
        "name": "EPFO Establishment Search",
        "url": "https://unifiedportal-emp.epfindia.gov.in/epfo/",
        "description": "Search EPFO establishment registration (Tier 1 — auto-checked)",
    },
    "mca": {
        "name": "MCA21 Company Search",
        "url": "https://www.mca.gov.in/content/mca/global/en/mca/company-search.html",
        "description": "Check company status in MCA21 registry (Tier 1 — auto-checked)",
    },
    "gem_debarred": {
        "name": "GeM Debarred Vendors List",
        "url": "https://gem.gov.in/resources/pdf/debarred_vendor.pdf",
        "description": "Official GeM debarred vendor list (Tier 3 — auto-checked)",
    },
    "cvc_blacklist": {
        "name": "CVC Debarred Firms List",
        "url": "https://cvc.gov.in/sites/default/files/debarred_firms.pdf",
        "description": "CVC list of debarred firms (Tier 3 — auto-checked)",
    },
}
