# livekit-debug-playground

Evidence-based debugging skill for LiveKit voice apps.

### The Problem

LiveKit voice applications often appear to work even when no real voice session has occurred.

Developers and coding agents frequently report success based on UI appearance rather than actual runtime behavior.

### The Solution

This repo provides:

• An Agent Skill for coding assistants (Cursor, Copilot, Claude Code)  
• Deterministic validation scripts for environment, token endpoints, and workers  
• A structured debugging discipline for proving real voice sessions occurred

The rule enforced by this repo:

> **If there is no observable runtime evidence, the voice app is not working.**

---

## When You Should Use This

Use this repo if:

• Your LiveKit UI loads but voice interaction never starts  
• The transcript UI renders but no messages appear  
• The agent joins the room but never responds  
• The visualizer never changes state  
• Coding agents claim the system works but you have no proof  
• You want deterministic validation of a LiveKit voice pipeline

This tool forces the system to prove that a real voice interaction occurred.

---

## What This Is

A portable Agent Skill plus validation scripts for debugging LiveKit-based voice applications. It is used by coding agents such as Cursor, GitHub Copilot, and Claude Code working inside LiveKit repositories to enforce evidence-based validation before reporting anything as complete.

This is not a general LiveKit tutorial. It is a debugging discipline.

---

## Why This Exists

LiveKit voice app failures are often silent. A page can load completely — control bar rendered, visualizer visible, transcript box present — while no real voice session has ever occurred. Coding agents and developers declare success based on visual appearance rather than observable runtime behavior.

This skill enforces one rule:

> **A working voice session with observable evidence is proof. Everything else is demo illusion.**

The enforcement loop:

```
Fail → Diagnose → Fix → Re-run → Prove
```

---

## Core Philosophy

**No Evidence. Not done.**

- A page loading is not proof
- A rendered control bar is not proof
- A visible transcript box is not proof
- A working voice session with observable evidence is proof

Done means the pass condition was confirmed — not that the code was written.

---

## What It Validates

| Layer | What it checks |
|---|---|
| 1 — Env/Config | Required env vars exist, `LIVEKIT_URL` format is valid, model provider keys are present |
| 2 — Runtime | Token endpoint returns a valid JWT, worker process is running and connected |
| 3 — UI | Session reaches `Connected`, agent joins the room, transcript updates, visualizer state changes |
| 4 — End-to-End | User turn captured, agent responds, voice state cycles, expected workflow output appears |

---

## Common Failure Patterns

1. Missing or invalid credentials
2. Broken token endpoint (returns error or invalid JWT)
3. Worker not running or crashed on startup
4. Session not initializing (stuck at `Connecting`)
5. Transcript not updating (UI rendering without subscribing to events)
6. UI renders but no real connection — demo illusion
7. Visualizer state never changes (audio track not received)
8. Multiple agents joining the same room
9. Supabase dependency failure blocking worker startup
10. Avatar layer fails silently after main session appears working
11. Agent stops on backchanneling ("uh-huh", "okay") — unnatural conversation flow

See [references/livekit-failure-patterns.md](references/livekit-failure-patterns.md) for diagnosis and fix instructions for each.

---

## Install the Skill

### With Agent Skills

```bash
npx skills add visaoenhance/livekit-debug-playground
```

This installs the skill instructions.

Then load `SKILL.md` into your coding agent's project context file:

| Agent | Context file |
|---|---|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |

### With scripts (deterministic local checks)

Clone this repo or copy the `scripts/` directory into your project:

```bash
git clone https://github.com/visaoenhance/livekit-debug-playground.git
```

---

## Scripts

All scripts use Python standard library only — no third-party dependencies. Exit code `0` = PASS, `1` = FAIL.

### Check environment variables

```bash
python scripts/check_env.py
```

Validates `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and model provider keys. Never prints secret values — shows `[set, N chars]`.

### Check the token endpoint

```bash
python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit/token
```

Auto-detects the endpoint if `--url` is omitted. Validates HTTP 200, `token` field present, JWT prefix (`eyJ`), and `url`/`wsUrl` field present.

### Check the worker process

```bash
python scripts/check_worker_status.py
```

Scans running processes for a Python LiveKit worker. Warns if multiple workers are found. Optional flags:

```bash
python scripts/check_worker_status.py --agent-file agents/my_agent.py
python scripts/check_worker_status.py --check-deps
```

---

## Evidence Expectations

| Layer | Minimum accepted evidence |
|---|---|
| 1 — Env/Config | `check_env.py` output showing all required vars present |
| 2 — Runtime | Token endpoint returns `{ token: "eyJ...", url: "wss://..." }` + worker running |
| 3 — UI | Connection state `Connected`, agent participant in room |
| 4 — End-to-end | User transcript captured + agent responded + voice state cycled |

Raw output must be shown before any summary. A summary without preceding raw output is not valid evidence.

---

## Supported Project Types

| Type | Pattern | Required additions |
|---|---|---|
| A | Python `AgentServer` + Next.js | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, model keys |
| B | Python `WorkerOptions` + Next.js | Same as Type A; worker startup pattern differs |
| C | Agents UI / React (cloud-hosted agent) | No local Python worker; token endpoint and UI layers only |
| D | Any type + Supabase persistence | Adds `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`; Layer 4 requires DB write proof |
| E | Any type + Avatar layer | Adds avatar provider keys; avatar layer validated after Layer 4 passes |

See [references/project-types.md](references/project-types.md) for required env vars and layer details per type.

---

## File Structure

```
livekit-debug-playground/
├── SKILL.md                           ← installable Agent Skill (primary artifact)
├── agents/
│   └── openai.yaml                    ← OpenAI Agents SDK skill manifest
├── references/
│   ├── livekit-failure-patterns.md    ← 11 failure modes with diagnosis and fix
│   ├── evidence-checklist.md          ← layer-by-layer validation checklist
│   ├── project-types.md              ← required vars and layer specifics by project type
│   └── adaptive-interruption-handling.md  ← natural conversation flow implementation guide
├── scripts/
│   ├── check_env.py                   ← validates required environment variables
│   ├── check_token_endpoint.py        ← tests token endpoint, validates JWT response
│   └── check_worker_status.py         ← checks if Python agent worker is running
├── README.md
├── LICENSE
└── SECURITY.md
```

---

## Related

- [supabase-debug-playground](https://github.com/visaoenhance/supabase-debug-playground) — the Supabase equivalent of this skill
- [food-court-voice-concierge](https://github.com/visaoenhance/food-court-voice-concierge) — reference project (Type A + D)
- [realtime-voice-avatar-agent](https://github.com/visaoenhance/realtime-voice-avatar-agent) — reference project (Type A + E)

---

## Mentioned in the LiveKit Community

This debugging playground was referenced in a LiveKit community discussion about Agent SDK state transitions (agent vs user speaking/listening).

**Discussion:** [Agent SDK states](https://community.livekit.io/t/agent-sdk-states/563)

The tool helps developers observe and validate runtime state transitions including:

- `agent_state_changed`
- `user_state_changed`
- transcript updates
- connection lifecycle
- end-to-end voice interaction flow

This provides real-world validation that the evidence-based debugging approach solves developer questions in the LiveKit ecosystem.

---

## ⚠ Disclaimer — No Warranty

This repository and its associated skill (`SKILL.md`) are provided as-is, without warranty of any kind. Scripts read environment files and make HTTP requests to local dev servers. You are responsible for understanding the environment before running any command. The authors are not responsible for misconfiguration or unexpected behavior resulting from use of this repository.

Run in a local or isolated environment. Do not run against production systems.

---

## License

MIT — Copyright (c) 2026 Emilio Taylor, Visao LLC. See [LICENSE](LICENSE).
