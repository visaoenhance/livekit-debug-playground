#!/usr/bin/env python3
"""
check_env.py — LiveKit Environment Validation

Validates that required environment variables are set for a LiveKit project.
Auto-detects project type based on env file contents.

Usage:
    python scripts/check_env.py
    python scripts/check_env.py --env .env.local
    python scripts/check_env.py --project-type A

Exit codes:
    0 — all required vars present
    1 — one or more required vars missing
"""

import os
import sys
import argparse
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

def header(msg: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {msg}")
    print(f"{'─' * 60}")


# ─────────────────────────────────────────────────────────────────────────────
# Env file loader
# ─────────────────────────────────────────────────────────────────────────────

def load_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file and return key=value pairs (no export, no quotes)."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        return env_vars
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip().removeprefix("export").strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    return env_vars


def find_env_file(start: Path) -> Path | None:
    """Search for .env.local, .env in the current and parent directories."""
    for candidate in [".env.local", ".env"]:
        for search_dir in [start, start.parent, start.parent.parent]:
            p = search_dir / candidate
            if p.exists():
                return p
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Var definitions
# ─────────────────────────────────────────────────────────────────────────────

CORE_VARS = [
    ("LIVEKIT_URL", "LiveKit server URL (wss:// for cloud, http:// for local OSS)"),
    ("LIVEKIT_API_KEY", "LiveKit API key"),
    ("LIVEKIT_API_SECRET", "LiveKit API secret"),
]

MODEL_VARS = [
    # (var_name, description, trigger_var_or_None_if_always_check)
    ("OPENAI_API_KEY", "OpenAI API key (STT/LLM/TTS)", None),
    ("DEEPGRAM_API_KEY", "Deepgram API key (STT)", None),
    ("ANTHROPIC_API_KEY", "Anthropic API key (Claude LLM)", None),
]

SUPABASE_VARS = [
    ("SUPABASE_URL", "Supabase project URL"),
    ("SUPABASE_SERVICE_ROLE_KEY", "Supabase service role key (write access)"),
]

AVATAR_VARS = [
    ("LEMONSLICE_API_KEY", "LemonSlice avatar API key"),
    ("LEMONSLICE_AGENT_ID", "LemonSlice pre-built agent ID (optional if IMAGE_URL set)"),
    ("LEMONSLICE_IMAGE_URL", "LemonSlice custom avatar image URL (optional if AGENT_ID set)"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Checks
# ─────────────────────────────────────────────────────────────────────────────

def check_var(name: str, description: str, env: dict[str, str]) -> bool:
    """Return True if var is present and non-empty. Print result."""
    value = env.get(name) or os.environ.get(name, "")
    if value:
        # Show partial value for non-secret vars; just confirm presence for secrets
        secret_keywords = ["SECRET", "KEY", "TOKEN", "PASSWORD"]
        is_secret = any(kw in name.upper() for kw in secret_keywords)
        if is_secret:
            display = f"[set, {len(value)} chars]"
        else:
            display = value[:60] + ("..." if len(value) > 60 else "")
        ok(f"{name:40s} {display}")
        return True
    else:
        fail(f"{name:40s} MISSING — {description}")
        return False


def check_livekit_url_format(env: dict[str, str]) -> None:
    """Warn if LIVEKIT_URL format looks wrong."""
    url = env.get("LIVEKIT_URL") or os.environ.get("LIVEKIT_URL", "")
    if not url:
        return  # already caught above
    if not (url.startswith("wss://") or url.startswith("ws://") or url.startswith("http")):
        fail(f"LIVEKIT_URL format suspicious: {url!r}")
        info("Expected: wss://your-project.livekit.cloud (cloud) or http://localhost:7880 (OSS)")


# ─────────────────────────────────────────────────────────────────────────────
# Detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def detect_supabase(env: dict[str, str]) -> bool:
    return bool(env.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", ""))


def detect_avatar(env: dict[str, str]) -> bool:
    for var in ["LEMONSLICE_API_KEY", "LEMONSLICE_AGENT_ID", "LEMONSLICE_IMAGE_URL"]:
        if env.get(var) or os.environ.get(var, ""):
            return True
    return False


def detect_model_providers(env: dict[str, str]) -> list[str]:
    """Return list of model provider vars that are set."""
    found = []
    for var, _, _ in MODEL_VARS:
        if env.get(var) or os.environ.get(var, ""):
            found.append(var)
    return found


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate LiveKit environment variables."
    )
    parser.add_argument(
        "--env",
        type=Path,
        default=None,
        help="Path to .env file (default: auto-detect .env.local or .env)",
    )
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║      LiveKit Debug Playground — check_env.py             ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Load env file
    script_dir = Path(__file__).parent
    env_path = args.env or find_env_file(script_dir)

    if env_path:
        info(f"Loading env from: {env_path}")
        env = load_env_file(env_path)
    else:
        info("No .env file found — checking os.environ only")
        env = {}

    failures = 0

    # ── Layer 1: Core LiveKit vars ──────────────────────────────────────────
    header("Layer 1 — Core LiveKit Variables (required)")
    for var, desc in CORE_VARS:
        if not check_var(var, desc, env):
            failures += 1
    check_livekit_url_format({**env, **os.environ})

    # ── Model provider keys ─────────────────────────────────────────────────
    header("Model Provider Keys (check what your agent uses)")
    provider_vars_set = detect_model_providers(env)
    if provider_vars_set:
        for var in provider_vars_set:
            check_var(var, "Model provider key", env)
    else:
        info("No model provider keys detected. If your agent uses OpenAI/Deepgram/Anthropic,")
        info("add the relevant key to your env file.")
        # Still check them but don't count as failures
        for var, desc, _ in MODEL_VARS:
            value = env.get(var) or os.environ.get(var, "")
            if not value:
                print(f"  ⚠   {var:40s} not set (add if used by your agent)")

    # ── Supabase vars (if detected) ─────────────────────────────────────────
    if detect_supabase(env):
        header("Supabase Variables (detected)")
        for var, desc in SUPABASE_VARS:
            if not check_var(var, desc, env):
                failures += 1
    else:
        header("Supabase Variables")
        info("SUPABASE_URL not detected — skipping Supabase checks.")
        info("If your project uses Supabase, add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")

    # ── Avatar vars (if detected) ───────────────────────────────────────────
    if detect_avatar(env):
        header("Avatar Variables (detected)")
        lemon_key = env.get("LEMONSLICE_API_KEY") or os.environ.get("LEMONSLICE_API_KEY", "")
        if not lemon_key:
            fail(f"{'LEMONSLICE_API_KEY':40s} MISSING — required for avatar")
            failures += 1
        else:
            ok(f"{'LEMONSLICE_API_KEY':40s} [set, {len(lemon_key)} chars]")

        agent_id = env.get("LEMONSLICE_AGENT_ID") or os.environ.get("LEMONSLICE_AGENT_ID", "")
        image_url = env.get("LEMONSLICE_IMAGE_URL") or os.environ.get("LEMONSLICE_IMAGE_URL", "")

        if agent_id:
            ok(f"{'LEMONSLICE_AGENT_ID':40s} {agent_id[:40]}")
        elif image_url:
            ok(f"{'LEMONSLICE_IMAGE_URL':40s} {image_url[:40]}...")
        else:
            fail(f"{'LEMONSLICE_AGENT_ID or LEMONSLICE_IMAGE_URL':40s} MISSING — need one of these for avatar")
            failures += 1

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    if failures == 0:
        print("  ✔  check_env.py: PASS — all required variables present")
        print(f"{'═' * 60}\n")
        return 0
    else:
        print(f"  ✘  check_env.py: FAIL — {failures} required variable(s) missing")
        print()
        print("  Next steps:")
        print("  1. Add missing variables to your .env.local file")
        print("  2. Restart your dev server (Next.js caches env on startup)")
        print("  3. Re-run this script to confirm all vars are present")
        print(f"{'═' * 60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
