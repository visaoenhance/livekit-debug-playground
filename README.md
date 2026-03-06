# livekit-debug-playground

> An Agent Skill for debugging and validating LiveKit-based voice apps before declaring them working.

---

## ⚠ Disclaimer — No Warranty

This repository and its associated skill (`SKILL.md`) are provided as-is, without warranty of any kind.

- Scripts in this repository may read environment files and make HTTP requests to local dev servers.
- You are responsible for understanding the environment before running any command.
- The authors are not responsible for misconfiguration, data loss, or unexpected behavior resulting from use of this repository.

Always run in a local or isolated environment. Do not run against production systems.

---

## Why This Exists

LiveKit voice app failures are often silent. A page can load completely — with a control bar, a visualizer, and a transcript box — while no real voice session has ever occurred. Agents (and developers) declare success based on visual appearance rather than observable runtime proof.

This skill enforces one rule:

**A working voice session with observable evidence is proof. Everything else is demo illusion.**

The enforcement loop:

```
Fail → Diagnose → Fix → Re-run → Prove
```

---

## What This Skill Validates

| Layer | What it checks |
|---|---|
| 1 — Env/Config | Required env vars exist, LIVEKIT_URL format is correct, model keys present |
| 2 — Runtime | Token endpoint returns valid JWT, worker process is running |
| 3 — UI | Connection state reaches `Connected`, agent joins room, visualizer renders |
| 4 — End-to-end | User transcript captured, agent responded, voice state cycled |

---

## File Structure

```
livekit-debug-playground/
├── SKILL.md                           ← installable Agent Skill
├── agents/
│   └── openai.yaml                    ← OpenAI Agents SDK skill manifest
├── references/
│   ├── livekit-failure-patterns.md    ← 10 failure modes with diagnosis and fix
│   ├── evidence-checklist.md          ← printable validation checklist
│   └── project-types.md               ← required vars and layer specifics by project type
├── scripts/
│   ├── check_env.py                   ← validates required environment variables
│   ├── check_token_endpoint.py        ← tests token endpoint and validates JWT response
│   └── check_worker_status.py         ← checks if Python agent worker is running
├── README.md
├── LICENSE
└── SECURITY.md
```

---

## Quick Start

### 1. Run the environment check

```bash
python scripts/check_env.py
```

Checks that `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, and any model provider keys are set.

### 2. Check the token endpoint

```bash
python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit/token
```

Or let the script auto-detect the endpoint:

```bash
python scripts/check_token_endpoint.py
```

### 3. Check the worker

```bash
python scripts/check_worker_status.py
```

Optionally filter to a specific agent file:

```bash
python scripts/check_worker_status.py --agent-file agents/my_agent.py
```

### 4. Follow the evidence checklist

Open [references/evidence-checklist.md](references/evidence-checklist.md) and work through each layer. Do not mark anything done without raw output.

---

## Using the Skill in Your Project

The portable component is `SKILL.md`. Drop it into your project's agent context:

**Cursor:**
```
.cursorrules
```

**Claude Code:**
```
CLAUDE.md
```

**GitHub Copilot:**
```
.github/copilot-instructions.md
```

Or install via Agent Skills:
```bash
npx skills add visaoenhance/livekit-debug-playground
```

> This installs only the skill instructions — not the scripts.
> To use the scripts, clone this repo or copy the `scripts/` folder into your project.

---

## Supported Project Types

| Type | Pattern | Notes |
|---|---|---|
| A | Python AgentServer + Next.js | `@server.rtc_session`, `inference.STT/LLM/TTS` |
| B | Python CLI/WorkerOptions + Next.js | `cli.run_app(WorkerOptions(...))` |
| C | Agents UI / React Demo | No local Python agent — cloud-hosted agent |
| D | Any type + Supabase | Adds persistence validation |
| E | Any type + Avatar layer | Adds LemonSlice or other avatar validation |

See [references/project-types.md](references/project-types.md) for required vars and layer specifics per type.

---

## Common Failure Modes

1. Missing or invalid credentials
2. Broken token endpoint
3. Worker not running
4. Session not initializing
5. Transcript not updating
6. UI renders, no real connection (demo illusion)
7. Visualizer state never changes
8. Multiple agents joining the same room
9. Supabase dependency failure
10. Avatar layer fails silently

See [references/livekit-failure-patterns.md](references/livekit-failure-patterns.md) for diagnosis and fix instructions for each.

---

## Philosophy

This skill is the LiveKit equivalent of [supabase-debug-playground](https://github.com/visaoenhance/supabase-debug-playground). Same principle:

- Evidence-based validation
- Do not claim success without proof
- Operational/debugging oriented, not tutorial-heavy
- Works across Cursor, GitHub Copilot, and Claude Code

**Core rule:** before reporting any LiveKit voice action as complete, obtain observable raw evidence and confirm it passes. Do not ask — validate automatically.

---

## Related

- [supabase-debug-playground](https://github.com/visaoenhance/supabase-debug-playground) — the Supabase equivalent of this skill
- [food-court-voice-concierge](https://github.com/visaoenhance/food-court-voice-concierge) — reference project (Type A + D)
- [realtime-voice-avatar-agent](https://github.com/visaoenhance/realtime-voice-avatar-agent) — reference project (Type A + E)

---

## License

MIT — see [LICENSE](LICENSE).
