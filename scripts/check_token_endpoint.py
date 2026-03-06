#!/usr/bin/env python3
"""
check_token_endpoint.py — LiveKit Token Endpoint Validation

Tests a LiveKit token endpoint and validates the response shape.
Confirms the endpoint returns a valid JWT token and server URL.

Usage:
    python scripts/check_token_endpoint.py
    python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit/token
    python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit-agentserver/token --method POST

Exit codes:
    0 — token endpoint passed all checks
    1 — one or more checks failed
"""

import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Terminal helpers
# ─────────────────────────────────────────────────────────────────────────────

def ok(msg: str) -> None:
    print(f"  ✔  {msg}")

def fail(msg: str) -> None:
    print(f"  ✘  {msg}")

def info(msg: str) -> None:
    print(f"  ℹ  {msg}")

def warn(msg: str) -> None:
    print(f"  ⚠  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Common token endpoint paths to try if no URL given
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_BASE = "http://localhost:3000"
CANDIDATE_PATHS = [
    "/api/livekit/token",
    "/api/livekit-agentserver/token",
    "/api/token",
    "/api/livekit-token",
]


def find_working_endpoint(base: str) -> str | None:
    """Try candidate paths and return the first that responds (any HTTP status)."""
    for path in CANDIDATE_PATHS:
        url = base.rstrip("/") + path
        try:
            req = urllib.request.Request(
                url,
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3):
                return url
        except urllib.error.HTTPError:
            # Any HTTP error means the server responded — path exists
            return url
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Token validation helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_jwt(value: str) -> bool:
    """Minimal check: a JWT has 3 base64url segments separated by dots."""
    if not isinstance(value, str):
        return False
    if not value.startswith("eyJ"):
        return False
    parts = value.split(".")
    return len(parts) == 3


def redact_token(token: str) -> str:
    """Return first 20 chars + redacted suffix for safe display."""
    if len(token) <= 20:
        return token
    return token[:20] + "..." + f"[{len(token)} chars total]"


# ─────────────────────────────────────────────────────────────────────────────
# Main check
# ─────────────────────────────────────────────────────────────────────────────

def check_endpoint(url: str, method: str = "POST") -> int:
    """
    Run all token endpoint checks. Returns 0 on pass, 1 on fail.
    """
    failures = 0

    print(f"\n  Endpoint : {url}")
    print(f"  Method   : {method}")
    print()

    # Build request
    payload = json.dumps({
        "participantName": "debug-check-agent",
        "roomName": f"debug-room-{__import__('time').time_ns()}",
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method=method,
    )

    # ── HTTP status ──────────────────────────────────────────────────────────
    status_code = None
    response_body = b""

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            response_body = resp.read()
    except urllib.error.HTTPError as e:
        status_code = e.code
        try:
            response_body = e.read()
        except Exception:
            response_body = b""
    except urllib.error.URLError as e:
        fail(f"HTTP request failed: {e.reason}")
        info("Is the dev server running? Try: npm run dev")
        return 1
    except TimeoutError:
        fail("Request timed out after 10 seconds")
        info("Is the dev server running and responding?")
        return 1

    if status_code == 200:
        ok(f"HTTP {status_code}")
    else:
        fail(f"HTTP {status_code} (expected 200)")
        failures += 1

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        data = json.loads(response_body)
    except json.JSONDecodeError:
        fail(f"Response is not valid JSON: {response_body[:200]!r}")
        return failures + 1

    # Show raw response (with token redacted)
    safe_data = dict(data)
    if "token" in safe_data and isinstance(safe_data["token"], str):
        safe_data["token"] = redact_token(safe_data["token"])
    print(f"  Raw response: {json.dumps(safe_data, indent=2)[:800]}")
    print()

    # ── Error field ──────────────────────────────────────────────────────────
    if "error" in data:
        fail(f"Response contains error field: {data['error']!r}")
        if "details" in data:
            info(f"Details: {data['details']}")
        failures += 1

    # ── Token field ──────────────────────────────────────────────────────────
    token_value = data.get("token")
    if token_value:
        ok(f"token field present")
    else:
        fail("token field missing from response")
        info("Expected: { token: 'eyJ...', url: 'wss://...' }")
        failures += 1

    # ── JWT format ───────────────────────────────────────────────────────────
    if token_value:
        if is_jwt(token_value):
            ok(f"token begins with eyJ (valid JWT prefix) — {redact_token(token_value)}")
        else:
            fail(f"token does not look like a JWT: {token_value[:30]!r}...")
            info("A valid LiveKit JWT begins with 'eyJ'")
            failures += 1

    # ── URL field (try common field names) ───────────────────────────────────
    url_value = data.get("url") or data.get("wsUrl") or data.get("serverUrl") or data.get("liveKitUrl")
    if url_value:
        ok(f"server URL field present: {url_value}")
        if not (url_value.startswith("wss://") or url_value.startswith("ws://") or url_value.startswith("http")):
            warn(f"URL format may be unexpected: {url_value!r}")
    else:
        fail("Server URL field missing from response")
        info("Expected: { ..., url: 'wss://your-project.livekit.cloud' }")
        info("Some endpoints use 'wsUrl', 'serverUrl', or 'liveKitUrl' — check your token endpoint")
        failures += 1

    # ── Room name (optional but useful) ─────────────────────────────────────
    room_name = data.get("roomName") or data.get("room")
    if room_name:
        ok(f"roomName present: {room_name}")

    # ── Summary ─────────────────────────────────────────────────────────────
    print()
    print(f"  {'─' * 56}")
    if failures == 0:
        ok("check_token_endpoint.py: PASS")
        print()
        print("  Layer 2 token check: PASS")
        print(f"  {'─' * 56}\n")
        return 0
    else:
        fail(f"check_token_endpoint.py: FAIL ({failures} check(s) failed)")
        print()
        print("  Diagnosis:")
        print("  - HTTP 500: check LIVEKIT_API_KEY, LIVEKIT_API_SECRET are set correctly")
        print("  - HTTP 404: verify the route file exists at the given path")
        print("  - error field present: read the error message and fix credentials")
        print("  - token missing: inspect the route handler — ensure toJwt() is called and returned")
        print("  - JWT invalid: API key and secret may be transposed")
        print(f"  {'─' * 56}\n")
        return 1


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a LiveKit token endpoint."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help=f"Token endpoint URL (default: auto-detect from {DEFAULT_BASE})",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="POST",
        choices=["GET", "POST"],
        help="HTTP method (default: POST)",
    )
    parser.add_argument(
        "--base",
        type=str,
        default=DEFAULT_BASE,
        help=f"Base URL for auto-detection (default: {DEFAULT_BASE})",
    )
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  LiveKit Debug Playground — check_token_endpoint.py      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    endpoint_url = args.url
    if not endpoint_url:
        info(f"No --url given. Auto-detecting from {args.base}...")
        endpoint_url = find_working_endpoint(args.base)
        if endpoint_url:
            info(f"Found endpoint: {endpoint_url}")
        else:
            fail("Could not find a responding token endpoint.")
            info("Known paths tried:")
            for p in CANDIDATE_PATHS:
                print(f"    {args.base}{p}")
            info("Start your dev server (npm run dev) or pass --url explicitly.")
            return 1

    return check_endpoint(endpoint_url, args.method)


if __name__ == "__main__":
    sys.exit(main())
