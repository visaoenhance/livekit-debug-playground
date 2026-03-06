---
name: livekit-debug-playground
description: evidence-based debugging skill for livekit voice apps. use when validating token flow, worker readiness, ui state, transcript updates, or end-to-end voice session behavior in livekit-based projects.
---

> **This skill is safe for use in any project.**
> It never runs destructive operations. It validates, diagnoses, and proves.
> The enforcement loop is: **Fail → Diagnose → Fix → Re-run → Prove**

---

## Scope

This skill is for coding agents working inside LiveKit-based repositories. It is optimized for:
- local development and token endpoint debugging
- worker and session startup validation
- Agents UI app validation
- transcript and voice-state proof
- end-to-end voice session evidence

This is not a general LiveKit tutorial.

---

## Normative Principle

**No Evidence. Not done.**

A LiveKit action is not complete when code is written or the dev server starts.
It is complete when observable runtime evidence confirms the behavior.

A page loading is not proof.
A rendered control bar is not proof.
A visible transcript box is not proof.
A working voice session with observable evidence is proof.

---

## Global Clause — Non-Interactive Mode

If this skill is running autonomously (CI, agent mode, no chat reply possible):
1. Run all non-destructive validation scripts automatically
2. Output raw results — do not summarize before showing them
3. If a validation fails and a fix is applied, re-run the check before reporting done
4. If a required check cannot be run, state this explicitly and provide the exact command for manual execution

---

## Global Clause — Never Disclose Secrets

**Never print, log, paste, or include in a diff:**
- `LIVEKIT_API_SECRET` or any value beginning with the secret prefix
- `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- Any JWT token value (begins with `eyJ`)
- Any value from `.env`, `.env.local`, or equivalent files

**Confirming presence is permitted:** State "I can see a value is set for `LIVEKIT_API_SECRET`." Do not print the value.
**`LIVEKIT_URL` is safe to show** — the `wss://` URL contains no secret material.

---

## Activation Rule — When This Skill Applies

This skill activates when any of the following is true:
- The project uses `livekit-agents`, `@livekit/components-react`, `livekit-server-sdk`, or `livekit-client`
- The task involves a token endpoint, voice session, agent worker, or room connection
- The task involves `LIVEKIT_URL`, `LIVEKIT_API_KEY`, or `LIVEKIT_API_SECRET`
- The user reports that a voice agent "seems to work" or "looks ready"

When active:
- Add a validation step to the task plan before execution
- Execute validation as part of the task — not as an afterthought
- Do not ask whether to validate — validate automatically
- Do not report done until the validation for the relevant layer passes

---

## Enforcement Loop

```
Fail → Diagnose → Fix → Re-run → Prove
```

**Never skip to "Prove" without running through the loop.**
If a fix is applied without first diagnosing the failure, the loop is broken.
If a validation passes without raw output to show, the proof is invalid.

**Required plan shape when LiveKit is detected:**
1. Reproduce (run current state — confirm failure if fixing, baseline if building)
2. Diagnose (use the layer-appropriate diagnostic below)
3. Apply minimal fix
4. Prove (binary pass/fail — raw output required, not a summary)
5. Report completion

---

## Layer 1 — Environment & Config

**What to check:**
- `LIVEKIT_URL` is set and begins with `wss://` (or `http://` for local OSS)
- `LIVEKIT_API_KEY` is set and non-empty
- `LIVEKIT_API_SECRET` is set and non-empty
- Token endpoint URL is configured in the frontend or `.env`
- Model provider keys exist (`OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, etc.) if the agent uses them
- If the project depends on Supabase: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
- If the project includes an avatar layer: avatar provider keys are set

**Validation command:**
```bash
python scripts/check_env.py
```

**Passes when:** All required vars are set. Output shows `✔` for each required variable.
**Do not report Layer 1 done** unless `check_env.py` outputs all required vars as present.

**Common failures:**
- `LIVEKIT_URL` uses `wss://` but project expects `https://` for REST calls (or vice versa)
- API key and secret are transposed
- `.env.local` exists but the dev server wasn't restarted after adding vars
- Model provider key is missing but the worker starts anyway (fails on first session)

---

## Layer 2 — Runtime Readiness

**What to check:**
- Dev server is running and responding
- Token endpoint returns a valid response with `token` and `url` fields
- Token response does not include an `error` field
- Token value begins with `eyJ` (valid JWT prefix)
- If using a Python agent: worker process is running and connected to LiveKit

**Validation commands:**
```bash
python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit/token
python scripts/check_worker_status.py
```

**Passes when:**
- Token endpoint returns HTTP 200 with `{ token: "eyJ...", url: "wss://..." }`
- Worker log shows connection to LiveKit server (no crash on startup)

**Do not report Layer 2 done** unless token endpoint returns a valid JWT and the worker is confirmed running.

**Common failures:**
- Token endpoint returns 500 because env vars are missing (check Layer 1 first)
- Token endpoint exists but returns `{ error: "..." }` — credentials misconfigured
- Worker starts but crashes immediately — check Python dependencies and env vars
- Multiple worker instances running — agent joins room multiple times
- Worker uses wrong agent name — dispatch fails silently

---

## Layer 3 — UI Readiness

**What to check:**
- `LiveKitRoom` component connects without immediate error
- Microphone permission can be requested in the browser
- Control bar renders and microphone button is interactive
- Audio visualizer renders (even before session starts)
- Voice assistant state is observable: `connecting`, `listening`, `speaking`, `thinking`, `idle`
- Participant list shows the agent after it joins (not just the user)

**Validation method:**
- Open browser DevTools console
- Connect to a session
- Confirm connection state transitions in console or via `useConnectionState()`
- Confirm agent participant appears in the room

**Passes when:** Connection state reaches `Connected`, agent participant joined, no WebRTC errors in console.

**Common failures:**
- `LiveKitRoom` renders but connection state stays at `Connecting` — check token/URL
- Agent never joins — worker not running or dispatch failed
- Microphone permission denied — browser blocked it, not a code issue
- BarVisualizer renders but state never changes — agent is not processing audio
- Control bar appears but clicking produces no observable state change

---

## Layer 4 — End-to-End Proof

**What to check:**
- Session starts and agent joins (Layer 3 prerequisite)
- User speech is transcribed and appears in transcript
- Agent responds with voice (audio track observed)
- Agent transcript appears and reflects a meaningful response
- Voice assistant state cycles: `listening` → `thinking` → `speaking` → `listening`
- If tools are used: tool calls appear in logs, results are returned
- If structured output is expected: confirmation state renders and backend effect is verified
- If Supabase persistence is expected: row written to correct table and query confirms it

**Evidence required:**
- Console log or screenshot showing `USER SAID: '...'` captured by worker
- Console log or screenshot showing `AGENT SAYING: '...'` from worker
- Transcript UI shows both user and agent turns
- If tool-dependent: tool call log + tool result log with non-empty result
- If persistence-dependent: raw query result showing the saved row

**Do not report Layer 4 done** without at least:
- Confirmed user transcript capture
- Confirmed agent response (voice or transcript)
- No session crash after the first exchange

**Common failures:**
- Transcript box renders but never updates — UI is not subscribing to agent data events
- Agent joins but voice state stays `idle` — audio track not received
- Worker logs show session started but no `USER SAID` entries — mic not publishing
- Tool calls logged but result is empty or error — check tool implementation and API keys
- App appears complete but no voice exchange ever occurred — demo illusion

---

## Evidence Standard

**Required before reporting any layer done:**

| Layer | Minimum evidence |
|---|---|
| 1 — Env/Config | `check_env.py` output showing all vars present |
| 2 — Runtime | Token endpoint returns `{ token: "eyJ...", url: "wss://..." }` + worker running |
| 3 — UI | Connection state `Connected`, agent participant in room |
| 4 — End-to-end | User transcript captured + agent responded + state cycled |

**Raw output must be shown before any summary.**
A summary without preceding raw output is not valid evidence.

---

## Banned Phrases

The following phrases are invalid as completion signals unless immediately followed by raw evidence:

- "looks good"
- "should be working"  
- "the app appears ready"
- "it seems to connect"
- "the agent is probably listening"
- "the session started"

**Valid completion signal format:**
```
Token endpoint check:
{ token: "eyJhbGc...", url: "wss://your-project.livekit.cloud" }
✔ HTTP 200
✔ token field present
✔ token begins with eyJ (valid JWT)
✔ url field present
Layer 2 token check: PASS
```

---

## Required Output Format

When this skill is used, the coding agent must report in this structure:

```
### Layer Checked
- Environment / Runtime / UI / End-to-End

### Evidence
- command run
- raw output observed
- pass/fail result

### Diagnosis
- what failed
- why it failed

### Fix Applied
- exact change made

### Re-run Proof
- command re-run
- output after fix

### Final Verdict
- passed / failed / blocked
```

**Raw output must appear before any summary.** A summary without preceding raw output is not valid evidence.

If all four layers pass:

```
## LiveKit Validation — Complete

Layer 1 (Env/Config):      PASS
Layer 2 (Runtime):         PASS
Layer 3 (UI):              PASS
Layer 4 (End-to-end):      PASS

Evidence summary:
- check_env.py: all required vars present
- Token endpoint: HTTP 200, valid JWT returned
- Worker: connected and ready in logs
- Session: user transcript captured, agent responded, state cycled

✔ Voice session validated. This is not demo illusion.
```

---

## Install This Skill

Drop this file into your project's agent context:
- **Cursor**: `.cursorrules`
- **Claude Code**: `CLAUDE.md`
- **Copilot**: `.github/copilot-instructions.md`

Or reference via Agent Skills:
```bash
npx skills add visaoenhance/livekit-debug-playground
```

---

## References

- [livekit-failure-patterns.md](references/livekit-failure-patterns.md) — common failure modes with diagnosis
- [evidence-checklist.md](references/evidence-checklist.md) — printable validation checklist
- [project-types.md](references/project-types.md) — required vars and layer specifics per project type
- [scripts/check_env.py](scripts/check_env.py) — env var validation
- [scripts/check_token_endpoint.py](scripts/check_token_endpoint.py) — token endpoint validation
- [scripts/check_worker_status.py](scripts/check_worker_status.py) — worker process check
