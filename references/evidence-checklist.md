# Evidence Checklist

> Use this checklist before declaring a LiveKit voice app working.
> A box checked in your head is not evidence. Raw output is evidence.

---

## How to use this checklist

For each item, you must have **raw output** — not a description of what you expect to see.
Mark an item only after you have obtained and shown the output.

Acceptable evidence format:
```
Check: Token endpoint returns valid JWT
Evidence: POST /api/livekit/token → HTTP 200
{ token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", url: "wss://..." }
✔ PASS
```

Not acceptable:
```
✔ Token endpoint is working (I tried it)
```

---

## Layer 1 — Environment & Config

- [ ] `LIVEKIT_URL` is set
  - Evidence: `check_env.py` output showing `✔ LIVEKIT_URL`
  - Value begins with `wss://` (cloud) or `http://localhost` (OSS local)

- [ ] `LIVEKIT_API_KEY` is set and non-empty
  - Evidence: `check_env.py` output showing `✔ LIVEKIT_API_KEY`

- [ ] `LIVEKIT_API_SECRET` is set and non-empty
  - Evidence: `check_env.py` output showing `✔ LIVEKIT_API_SECRET`

- [ ] Token endpoint URL is configured in the frontend or env file
  - Evidence: grep of config file showing the endpoint path

- [ ] Model provider keys are set (if agent uses STT/LLM/TTS)
  - Evidence: `check_env.py` output showing provider keys present

- [ ] _(If project uses Supabase)_ `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
  - Evidence: `check_env.py` output showing Supabase vars present

- [ ] _(If project uses avatar)_ Avatar provider key(s) are set
  - Evidence: `check_env.py` output showing avatar vars present

**Layer 1 gate:** Do not proceed to Layer 2 until all applicable Layer 1 boxes are checked with evidence.

---

## Layer 2 — Runtime Readiness

- [ ] Dev server is running and responding
  - Evidence: `curl http://localhost:3000` → HTTP 200 or non-error response

- [ ] Token endpoint returns HTTP 200
  - Evidence: `check_token_endpoint.py` output showing `✔ HTTP 200`

- [ ] Token response contains `token` field
  - Evidence: raw JSON response showing `"token": "eyJ..."`

- [ ] Token value begins with `eyJ` (valid JWT)
  - Evidence: first 20 characters of token shown in `check_token_endpoint.py` output

- [ ] Token response contains `url` field with LiveKit server URL
  - Evidence: raw JSON showing `"url": "wss://..."` or `"wsUrl": "wss://..."`

- [ ] _(If Python agent)_ Worker process is running
  - Evidence: `check_worker_status.py` showing running process OR terminal showing worker output

- [ ] _(If Python agent)_ Worker connected to LiveKit server on startup
  - Evidence: worker terminal showing "Connected to `wss://...`" or "Agent server ready"

**Layer 2 gate:** Do not proceed to Layer 3 until token endpoint returns valid JWT and (if applicable) worker is confirmed running.

---

## Layer 3 — UI Readiness

- [ ] `LiveKitRoom` component renders without immediate crash
  - Evidence: no error boundary triggered, no red crash screen

- [ ] Connection state reaches `Connected` (not just `Connecting`)
  - Evidence: browser console log showing `ConnectionState.Connected` OR component reflecting connected state

- [ ] Microphone permission was requested and granted
  - Evidence: browser showed permission dialog, user allowed, no mic-blocked error in console

- [ ] Agent participant joins the room
  - Evidence: console log showing participant connected with agent identity OR room participant count = 2

- [ ] Control bar renders and mic button is visible
  - Evidence: screenshot or console confirmation — component visible in DOM

- [ ] Audio visualizer renders
  - Evidence: `BarVisualizer` or equivalent is mounted — not just present in code but visible in UI

- [ ] Voice assistant state is observable
  - Evidence: `useVoiceAssistant().state` logged or displayed — value is not `undefined`

**Layer 3 gate:** Do not proceed to Layer 4 until agent has joined, connection is confirmed, and UI components are verified present.

---

## Layer 4 — End-to-End Proof

- [ ] User spoke and STT captured the utterance
  - Evidence: worker terminal shows `USER SAID: '...'` with actual transcript text

- [ ] Agent processed the utterance (LLM called)
  - Evidence: worker terminal shows no STT error, session progresses past `listening` state

- [ ] Agent responded with voice
  - Evidence: worker terminal shows `AGENT SAYING: '...'` with actual response text
  - AND: audio heard in browser OR `BarVisualizer` animated during agent speech

- [ ] Transcript UI shows both user and agent turns
  - Evidence: screenshot or console log showing both sides present in transcript component

- [ ] Voice assistant state cycled through expected states
  - Evidence: `useVoiceAssistant().state` observed to cycle: `listening` → `thinking` → `speaking` → `listening`

- [ ] _(If tool-dependent)_ Tool call appeared in worker logs
  - Evidence: worker log showing `TOOL CALLED: tool_name(...)` with actual arguments

- [ ] _(If tool-dependent)_ Tool result was returned and non-empty
  - Evidence: worker log showing `TOOL RESULT: ...` with actual result data

- [ ] _(If structured output expected)_ Confirmation or result card rendered in UI
  - Evidence: screenshot or DOM inspection showing the card rendered with actual data

- [ ] _(If Supabase persistence expected)_ Backend row was written
  - Evidence: raw query result from Supabase showing the saved row with its `id`

**Layer 4 gate:** Do not declare the voice app working until at minimum user transcript + agent response + no crash is confirmed.

---

## Summary Checklist (Quick Reference)

| # | Check | Evidence required |
|---|---|---|
| 1.1 | `LIVEKIT_URL` set | `check_env.py` output |
| 1.2 | `LIVEKIT_API_KEY` set | `check_env.py` output |
| 1.3 | `LIVEKIT_API_SECRET` set | `check_env.py` output |
| 1.4 | Model provider keys set | `check_env.py` output |
| 2.1 | Token endpoint HTTP 200 | `check_token_endpoint.py` output |
| 2.2 | Token is valid JWT | Token begins with `eyJ` |
| 2.3 | Worker running | Process list or terminal output |
| 3.1 | Connection state `Connected` | Console log |
| 3.2 | Agent joined room | Participant log |
| 4.1 | User transcript captured | Worker `USER SAID:` log |
| 4.2 | Agent responded | Worker `AGENT SAYING:` log + audio |
| 4.3 | State cycled | `useVoiceAssistant().state` observation |

---

## Final Gate

**Before saying "this voice app is working":**

> I have raw evidence for at least items 1.1–1.3, 2.1–2.2, 3.1–3.2, and 4.1–4.2.
> This evidence is raw output, not a description of expected behavior.
> The session completed at least one full exchange: user spoke → agent responded.

If you cannot make this statement, the app is not proven working.
