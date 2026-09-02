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
    Udyam Registration verification — CAPTCHA confirmed on every lookup.
    No automation. Deep-link to official portal only.
    """
    return {
        "portal": "udyamregistration.gov.in",
        "url": "https://udyamregistration.gov.in/Government-India/Ministry-MSME-registration.htm",
        "lookup_value": udyam_number,
        "instruction": (
            f"Navigate to the Udyam portal above, click 'Verify Udyam Registration', "
            f"and enter the number: {udyam_number}. "
            f"Record the verified status below."
        ),
    }


def bis_verify_url(license_number: str) -> dict:
    """
    BIS ISI/CRS license verification — CAPTCHA status unconfirmed.
    Manual redirect.
    """
    return {
        "portal": "manakonline.in",
        "url": "https://www.manakonline.in/MANA/searchLicense.do",
        "lookup_value": license_number,
        "instruction": (
            f"Navigate to Manak Online above, use 'Search a License', "
            f"and enter: {license_number}. Record the result below."
        ),
    }


def startup_india_verify_url(dpiit_number: str) -> dict:
    """
    DPIIT/Startup India recognition verification — plausible CAPTCHA-free
    but unconfirmed. Manual redirect until spike confirms.
    """
    return {
        "portal": "startupindia.gov.in",
        "url": f"https://www.startupindia.gov.in/content/sih/en/certificate-verification.html",
        "lookup_value": dpiit_number,
        "instruction": (
            f"Navigate to Startup India above and verify certificate number: {dpiit_number}. "
            f"Record the result below."
        ),
    }
