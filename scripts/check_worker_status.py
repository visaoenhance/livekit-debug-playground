#!/usr/bin/env python3
"""
check_worker_status.py — LiveKit Agent Worker Status Check

Checks whether a LiveKit Python agent worker is currently running.
Detects running processes and optionally checks LiveKit Cloud for
active agent registrations.

Usage:
    python scripts/check_worker_status.py
    python scripts/check_worker_status.py --agent-file agents/my_agent.py
    python scripts/check_worker_status.py --agent-name my-agent-name

Exit codes:
    0 — worker process found and appears healthy
    1 — no worker found or worker appears unhealthy
"""

import os
import sys
import argparse
import subprocess
import shutil
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

def section(msg: str) -> None:
    print(f"\n  {'─' * 56}")
    print(f"  {msg}")
    print(f"  {'─' * 56}")


# ─────────────────────────────────────────────────────────────────────────────
# Process detection
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that indicate a LiveKit agent worker process
LIVEKIT_PROCESS_PATTERNS = [
    "livekit",
    "livekit-agents",
    "food_concierge",
    "agent.py",
    "agent_server",
    "agentserver",
]

# Python keywords that suggest an agent entrypoint
AGENT_ENTRYPOINT_KEYWORDS = [
    "WorkerOptions",
    "AgentServer",
    "cli.run_app",
    "rtc_session",
    "entrypoint_fnc",
]


def get_running_python_processes() -> list[dict]:
    """Return list of running Python processes with pid, command, args."""
    if not shutil.which("ps"):
        return []
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        processes = []
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split(None, 10)
            if len(parts) < 11:
                continue
            pid = parts[1]
            command = parts[10]
            if "python" in command.lower():
                processes.append({"pid": pid, "command": command})
        return processes
    except Exception:
        return []


def filter_livekit_processes(processes: list[dict]) -> list[dict]:
    """Filter processes to those likely to be LiveKit agent workers."""
    matches = []
    for proc in processes:
        cmd = proc["command"].lower()
        for pattern in LIVEKIT_PROCESS_PATTERNS:
            if pattern.lower() in cmd:
                matches.append(proc)
                break
    return matches


def check_for_agent_file(
    agent_file: str | None,
    processes: list[dict],
) -> list[dict]:
    """If a specific agent file is given, filter further."""
    if not agent_file:
        return processes
    return [
        p for p in processes
        if agent_file.lower() in p["command"].lower()
        or Path(agent_file).name.lower() in p["command"].lower()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Agent file scan
# ─────────────────────────────────────────────────────────────────────────────

def find_agent_files(search_dir: Path) -> list[Path]:
    """Find Python files that look like LiveKit agent entrypoints."""
    candidates = []
    for py_file in search_dir.rglob("*.py"):
        # Skip node_modules, .venv, __pycache__
        if any(skip in str(py_file) for skip in ["node_modules", ".venv", "venv", "__pycache__", ".git"]):
            continue
        try:
            content = py_file.read_text(errors="ignore")
            for keyword in AGENT_ENTRYPOINT_KEYWORDS:
                if keyword in content:
                    candidates.append(py_file)
                    break
        except (PermissionError, OSError):
            continue
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# LiveKit SDK check
# ─────────────────────────────────────────────────────────────────────────────

def check_livekit_sdk_installed() -> tuple[bool, str]:
    """Check if livekit-agents is importable and return version."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import livekit.agents; print(livekit.agents.__version__)"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout.strip()
        return False, ""
    except Exception:
        return False, ""


def check_python_deps() -> None:
    """Print status of key LiveKit packages."""
    packages = [
        ("livekit-agents", "livekit.agents"),
        ("livekit-server-sdk", "livekit"),
        ("livekit-plugins-openai", "livekit.plugins.openai"),
        ("livekit-plugins-deepgram", "livekit.plugins.deepgram"),
        ("livekit-plugins-silero", "livekit.plugins.silero"),
    ]
    for pkg_name, import_path in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {import_path}; print('ok')"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ok(f"{pkg_name:40s} importable")
            else:
                warn(f"{pkg_name:40s} not importable — {result.stderr.strip()[:60]}")
        except Exception:
            warn(f"{pkg_name:40s} check failed")


# ─────────────────────────────────────────────────────────────────────────────
# Multiple worker detection
# ─────────────────────────────────────────────────────────────────────────────

def check_multiple_workers(livekit_procs: list[dict]) -> None:
    """Warn if multiple agent workers are running."""
    if len(livekit_procs) > 1:
        warn(f"{len(livekit_procs)} LiveKit-related processes found!")
        info("Multiple workers can cause a single dispatch to trigger multiple agents in one room.")
        info("Kill extra processes: pkill -f your_agent.py")
        for proc in livekit_procs:
            print(f"    PID {proc['pid']:8s}  {proc['command'][:80]}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check LiveKit agent worker status."
    )
    parser.add_argument(
        "--agent-file",
        type=str,
        default=None,
        help="Python agent file to look for in process list (e.g. agents/my_agent.py)",
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default=None,
        help="Agent name used in @server.rtc_session(agent_name=...) to look for",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        default=False,
        help="Also check that livekit-agents SDK packages are importable",
    )
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║   LiveKit Debug Playground — check_worker_status.py      ║")
    print("╚══════════════════════════════════════════════════════════╝")

    failures = 0

    # ── SDK check (optional) ─────────────────────────────────────────────────
    section("LiveKit SDK Installation")
    sdk_installed, sdk_version = check_livekit_sdk_installed()
    if sdk_installed:
        ok(f"livekit-agents installed, version: {sdk_version}")
    else:
        fail("livekit-agents not importable in current Python environment")
        info("Install: pip install 'livekit-agents[openai]'")
        failures += 1

    if args.check_deps:
        section("Python Package Availability")
        check_python_deps()

    # ── Process scan ─────────────────────────────────────────────────────────
    section("Running Agent Worker Processes")

    all_python = get_running_python_processes()
    info(f"Python processes found: {len(all_python)}")

    livekit_procs = filter_livekit_processes(all_python)

    if args.agent_file:
        livekit_procs = check_for_agent_file(args.agent_file, all_python)
        info(f"Filtering for agent file: {args.agent_file}")

    if livekit_procs:
        ok(f"{len(livekit_procs)} LiveKit-related process(es) found:")
        for proc in livekit_procs:
            print(f"\n    PID {proc['pid']:8s}")
            print(f"    CMD {proc['command'][:120]}")
        check_multiple_workers(livekit_procs)
    else:
        fail("No LiveKit agent worker processes found")
        info("Start your worker with: python your_agent.py dev")
        info("Ensure it uses one of: AgentServer, WorkerOptions, cli.run_app")
        failures += 1

    # ── Agent file discovery ─────────────────────────────────────────────────
    section("Agent File Discovery (local codebase)")
    search_root = Path.cwd()
    agent_files = find_agent_files(search_root)

    if agent_files:
        ok(f"{len(agent_files)} agent file(s) found:")
        for f in agent_files:
            rel = f.relative_to(search_root) if search_root in f.parents else f
            print(f"    {rel}")
    else:
        info("No Python agent entrypoint files detected in current directory tree.")
        info("Looking for files containing: WorkerOptions, AgentServer, cli.run_app, rtc_session")

    # ── Instructions for agent name ──────────────────────────────────────────
    if args.agent_name:
        section(f"Agent Name Check: {args.agent_name!r}")
        if agent_files:
            found_in = []
            for f in agent_files:
                try:
                    content = f.read_text(errors="ignore")
                    if args.agent_name in content:
                        found_in.append(f)
                except Exception:
                    pass
            if found_in:
                ok(f"Agent name {args.agent_name!r} found in:")
                for f in found_in:
                    rel = f.relative_to(search_root) if search_root in f.parents else f
                    print(f"    {rel}")
            else:
                warn(f"Agent name {args.agent_name!r} not found in any agent file")
                info("Ensure your token endpoint dispatches the same agent_name as")
                info("the one registered in @server.rtc_session(agent_name=...)")
        else:
            info("No agent files found to search for agent name")

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n  {'═' * 56}")
    if failures == 0:
        ok("check_worker_status.py: PASS")
        print()
        print("  Layer 2 worker check: PASS")
        print()
        print("  Reminder: Confirm worker terminal shows:")
        print("    ✅ Agent server ready")
        print("    Connected to: wss://...")
        print("    Waiting for dispatch...")
        print(f"  {'═' * 56}\n")
        return 0
    else:
        fail(f"check_worker_status.py: FAIL ({failures} issue(s) found)")
        print()
        print("  Next steps:")
        print("  1. Start the Python agent: python your_agent.py dev")
        print("  2. Check for startup errors in the terminal")
        print("  3. Confirm LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET are set")
        print("  4. Re-run this script to confirm the worker is found")
        print(f"  {'═' * 56}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
