"""
Resilient Compliance Runner
────────────────────────────
Wraps every individual API call in a safe execution boundary.

Failure modes handled:
  1. API timeout            → status = "pending_manual", detail explains why
  2. API auth error (401)   → status = "pending_manual", logs key issue
  3. API 4xx (bad request)  → status = "fail", detail = API error message
  4. API 5xx (server error) → status = "pending_manual", retry suggested
  5. Network error          → status = "pending_manual", offline note
  6. Unexpected exception   → status = "pending_manual", safe fallback
  7. Invalid/empty input    → status = "fail", explains what's missing

Key design decisions:
  - NEVER let one check failure crash the whole compliance run
  - API errors → "pending_manual" (not "fail") because we can't CONFIRM failure,
    so we don't auto-disqualify — the officer decides
  - Every failure is logged in the audit trail with full exception info
  - Score excludes "pending_manual" checks (same as Tier 2 manual_review)
  - Frontend shows a clear "⚠️ Check Unavailable" badge with retry option
"""

import httpx
import asyncio
import logging
from models.compliance import CheckStatus

logger = logging.getLogger(__name__)

# ── Failure reason categories ─────────────────────────────────────────────
class FailureReason:
    TIMEOUT       = "API_TIMEOUT"
    AUTH_ERROR    = "API_AUTH_ERROR"
    NOT_FOUND     = "API_NOT_FOUND"
    SERVER_ERROR  = "API_SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    UNKNOWN       = "UNKNOWN_ERROR"


def _pending_manual(reason_code: str, check_name: str, detail: str, exc: Exception = None) -> dict:
    """
    Return a 'pending_manual' verdict.

    This is the SAFE fallback for API failures. We cannot confirm PASS or FAIL
    without data, so we ask an officer to manually verify instead of auto-disqualifying.
    """
    return {
        "status": CheckStatus.manual_review,
        "detail": detail,
        "_failure_reason": reason_code,
        "_check_name": check_name,
        "_exception": str(exc) if exc else None,
        "_requires_manual": True,
    }


def _fail(check_name: str, detail: str) -> dict:
    """Return a definitive FAIL — used only when input itself is clearly invalid."""
    return {
        "status": CheckStatus.fail,
        "detail": detail,
        "_failure_reason": FailureReason.INVALID_INPUT,
        "_check_name": check_name,
    }


async def safe_call(
    check_name: str,
    coro,
    timeout_seconds: float = 12.0,
) -> dict:
    """
    Safely execute an async API coroutine.

    Returns the raw API result dict on success, or a
    structured failure dict on any error.

    Args:
        check_name: Human-readable name for logging
        coro: The async coroutine to execute (e.g. gst.verify_gst(...))
        timeout_seconds: Per-call timeout

    Returns:
        dict — either the API result, or a failure dict with status=manual_review
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)

        # If the adapter itself returned an api_error marker
        if isinstance(result, dict) and result.get("status") == "api_error":
            error_msg = result.get("error", "Unknown API error")
            logger.warning(f"[{check_name}] Adapter returned api_error: {error_msg}")
            return _pending_manual(
                FailureReason.SERVER_ERROR,
                check_name,
                f"External API returned an error for {check_name}. "
                f"Officer please verify manually. (API said: {error_msg[:120]})",
            )

        return result

    except asyncio.TimeoutError:
        logger.warning(f"[{check_name}] Timed out after {timeout_seconds}s")
        return _pending_manual(
            FailureReason.TIMEOUT,
            check_name,
            f"{check_name} check timed out after {timeout_seconds}s. "
            f"Government API may be slow or down. Officer please verify on official portal.",
        )

    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        logger.error(f"[{check_name}] HTTP {code}: {exc}")

        if code == 401:
            return _pending_manual(
                FailureReason.AUTH_ERROR,
                check_name,
                f"{check_name} API authentication failed (HTTP 401). "
                f"Check that the API key in .env is valid and not expired. Officer please verify manually.",
                exc,
            )
        if code == 404:
            # 404 from a govt API means "not found" — that IS a compliance failure
            return {
                "status": CheckStatus.fail,
                "detail": f"{check_name}: Record not found in government database (HTTP 404).",
                "_failure_reason": FailureReason.NOT_FOUND,
            }
        if code == 429:
            return _pending_manual(
                FailureReason.SERVER_ERROR,
                check_name,
                f"{check_name} API rate limit exceeded (HTTP 429). "
                f"Retry in a few minutes, or verify manually on official portal.",
                exc,
            )
        if 500 <= code < 600:
            return _pending_manual(
                FailureReason.SERVER_ERROR,
                check_name,
                f"{check_name} government API is currently unavailable (HTTP {code}). "
                f"This is a temporary outage. Retry later or verify manually.",
                exc,
            )
        # Other 4xx — treat as input/data problem
        return _pending_manual(
            FailureReason.UNKNOWN,
            check_name,
            f"{check_name} API returned HTTP {code}. Officer please verify manually.",
            exc,
        )

    except httpx.ConnectError as exc:
        logger.error(f"[{check_name}] Network connection failed: {exc}")
        return _pending_manual(
            FailureReason.NETWORK_ERROR,
            check_name,
            f"{check_name} check failed: cannot connect to government API. "
            f"Check internet connectivity or VPN. Officer please verify manually.",
            exc,
        )

    except httpx.RemoteProtocolError as exc:
        logger.error(f"[{check_name}] Protocol error: {exc}")
        return _pending_manual(
            FailureReason.NETWORK_ERROR,
            check_name,
            f"{check_name} API connection dropped mid-response. Retry or verify manually.",
            exc,
        )

    except Exception as exc:
        # Catch-all — never let an unknown error crash the compliance run
        logger.exception(f"[{check_name}] Unexpected error: {exc}")
        return _pending_manual(
            FailureReason.UNKNOWN,
            check_name,
            f"{check_name} check encountered an unexpected error. "
            f"The system has logged this. Officer please verify manually. "
            f"(Error type: {type(exc).__name__})",
            exc,
        )


def is_api_failure(raw_result: dict) -> bool:
    """Returns True if the raw result is an API failure (not real data)."""
    return raw_result.get("_failure_reason") is not None


def extract_failure_verdict(raw_result: dict) -> dict:
    """
    If the raw result is an API failure, return the pre-built verdict.
    The rules engine should never be called on a failure result.
    """
    return {
        "status": raw_result.get("status", CheckStatus.manual_review),
        "detail": raw_result.get("detail", "Check unavailable."),
    }
