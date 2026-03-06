# Project Types

> Use this reference to identify which layers and which required vars apply to your specific project.
> Not all LiveKit projects are the same. Validation requirements differ by project type.

---

## Type A — Python Agent + Next.js Frontend (AgentServer Pattern)

**Matches if:**
- Python file uses `AgentServer` with `@server.rtc_session`
- `inference.STT`, `inference.LLM`, `inference.TTS` (unified API)
- Token endpoint uses `AgentDispatchClient.createDispatch()`
- Frontend uses `@livekit/components-react` with `LiveKitRoom`

**Reference projects:**
- `visaoenhance/food-court-voice-concierge`
- `visaoenhance/realtime-voice-avatar-agent`

**Required env vars:**
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIsomething
LIVEKIT_API_SECRET=your_secret_here
OPENAI_API_KEY=sk-...            # if using OpenAI LLM/TTS
DEEPGRAM_API_KEY=...             # if using Deepgram STT
```

**All four layers apply.**
Worker must be running before Layer 3 can pass.

**Common env file location:** `agents/` folder loads `../.env.local` (one level up from agents/)
Confirm with `load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))`.

**Worker start command:**
```bash
python your_agent.py dev
```

**Token endpoint pattern:**
```
POST /api/livekit-agentserver/token
Returns: { token: "eyJ...", url: "wss://...", roomName: "..." }
```

**Layer 3 specific:** confirm `agent_name` in `@server.rtc_session` matches the name used in `AgentDispatchClient.createDispatch()`.

---

## Type B — Python Agent + Next.js Frontend (CLI/WorkerOptions Pattern)

**Matches if:**
- Python file uses `cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))`
- `openai.STT()`, `openai.LLM()`, `openai.TTS()` direct plugins (not `inference.*`)
- Token endpoint does NOT use `AgentDispatchClient` — agent auto-assigns to rooms
- Frontend uses `@livekit/components-react` with `LiveKitRoom`

> ⚠ This pattern has known schema validation issues in livekit-agents >= 1.4.
> Function tool parameters with defaults will cause 400 errors from OpenAI.
> If seeing schema errors, consider migrating to Type A (AgentServer pattern).

**Required env vars:**
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIsomething
LIVEKIT_API_SECRET=your_secret_here
OPENAI_API_KEY=sk-...
```

**Layer 2 difference:** No `AgentDispatchClient` — worker auto-assigns. Confirm worker is running and connected to LiveKit; it will auto-join any new room.

**Token endpoint pattern (simpler):**
```
POST /api/livekit/token
Returns: { token: "eyJ...", wsUrl: "wss://..." }
```

Note: some endpoints return `wsUrl`, others return `url`. Frontend must use the correct field name.

---

## Type C — Agents UI / React Demo (No Python Agent)

**Matches if:**
- Project uses `@livekit/components-react` and `LiveKitRoom`
- No Python worker — LiveKit Cloud or a pre-existing hosted agent handles the backend
- Token endpoint generates a token only (no dispatch)
- `@livekit/agents-ui` or similar demo UI component

**Reference projects:**
- `visaoenhance/livekit-agents-ui-demo`

**Required env vars:**
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIsomething
LIVEKIT_API_SECRET=your_secret_here
```

**Layer 2 difference:** No local worker to check. Skip `check_worker_status.py`. Confirm the token endpoint works and that a hosted agent is registered in LiveKit Cloud.

**Layer 3 difference:** Agent joins from cloud — may have a delay. Do not flag as broken if agent takes 5–10 seconds to join after room creation.

**Layer 4 difference:** Console logs for `USER SAID:` / `AGENT SAYING:` will not appear (no local worker). Instead observe:
- `useVoiceAssistant().state` cycling
- Transcript populated via `useTranscriptions()` or equivalent
- Audio level from `BarVisualizer` changing on voice input

---

## Type D — LiveKit with Supabase Persistence

**Matches if:**
- Project has both `LIVEKIT_*` and `SUPABASE_*` env vars
- Agent uses Supabase (Python `supabase-py` client) to read/write data during sessions
- Tool results are persisted to a Supabase table
- Frontend may show confirmation cards loaded from Supabase

**Additional required env vars (on top of Type A or B):**
```
SUPABASE_URL=http://127.0.0.1:54321         # local
# OR
SUPABASE_URL=https://your-project.supabase.co  # cloud
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

**Layer 1 addition:** `check_env.py` will check for Supabase vars when `SUPABASE_URL` is present in the env.

**Layer 4 addition:** After tool execution, query the target table to confirm the row was written:
```python
result = supabase.table("your_table").select("*").order("created_at", desc=True).limit(1).execute()
print(result.data)
```
A row with an `id` field present is the pass condition. No row = backend effect not proven.

**If using local Supabase:**
```bash
supabase status  # confirm local instance is running
```
Must show `API URL: http://127.0.0.1:54321` and `Status: running`.

---

## Type E — LiveKit with Avatar Layer

**Matches if:**
- Project uses `livekit-agents[lemonslice]` or another avatar SDK
- `LEMONSLICE_API_KEY` (or equivalent) is set or expected
- Avatar video track is published to the room alongside audio
- Frontend renders an avatar video panel

**Additional required env vars:**
```
LEMONSLICE_API_KEY=sk_lemon_...
# EITHER:
LEMONSLICE_AGENT_ID=agent_...    # pre-built agent
# OR:
LEMONSLICE_IMAGE_URL=https://...  # custom image avatar
```

**Layer 1 addition:** `check_env.py` checks for avatar keys when `LEMONSLICE_API_KEY` or `LEMONSLICE_IMAGE_URL` is present.

**Layer 2 addition:** Avatar SDK installation check:
```bash
pip show livekit-agents | grep lemonslice
# or:
python -c "from livekit.plugins import lemonslice; print('ok')"
```

**Layer 4 addition:** Confirm avatar video track render — not just audio.
- Worker log shows: `✅ LemonSlice avatar started successfully`
- Frontend shows avatar video panel with non-blank content
- Avatar lip-sync observed during agent speech

**Important:** Validate without avatar first (base voice session). Only add avatar validation after base voice session passes all four layers.

---

## Minimum Required Vars by Type

| Var | Type A | Type B | Type C | Type D | Type E |
|---|---|---|---|---|---|
| `LIVEKIT_URL` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `LIVEKIT_API_KEY` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `LIVEKIT_API_SECRET` | ✔ | ✔ | ✔ | ✔ | ✔ |
| `OPENAI_API_KEY` | ✔ | ✔ | — | ✔ | ✔ |
| `DEEPGRAM_API_KEY` | optional | — | — | optional | optional |
| `SUPABASE_URL` | — | — | — | ✔ | — |
| `SUPABASE_SERVICE_ROLE_KEY` | — | — | — | ✔ | — |
| `LEMONSLICE_API_KEY` | — | — | — | — | ✔ |

---

## Identifying Project Type

If type is unknown, run in this order:

1. Check for `AgentServer` in Python files → Type A
2. Check for `WorkerOptions` / `cli.run_app` in Python files → Type B
3. No Python agent → Type C
4. Any of the above with `SUPABASE_URL` → also Type D
5. Any of the above with `LEMONSLICE_API_KEY` → also Type E

```bash
grep -r "AgentServer\|WorkerOptions\|cli.run_app" --include="*.py" .
grep -r "SUPABASE_URL\|LEMONSLICE_API_KEY" --include="*.env*" --include="*.py" .
```
