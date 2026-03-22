# LiveKit Failure Patterns

> Reference for coding agents. Not for end users.
> Use alongside `SKILL.md` to diagnose and fix failures at each validation layer.

---

## Pattern 1 — Missing or Invalid LiveKit Credentials

**Symptoms:**
- Token endpoint returns HTTP 500
- Token endpoint returns `{ error: "Server configuration error" }`
- Worker fails to start with `AuthenticationError` or similar
- All four layers fail immediately

**Root cause:**
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, or `LIVEKIT_API_SECRET` not set
- Keys are set but transposed (key in secret field, secret in key field)
- `.env.local` exists but dev server not restarted after adding vars
- `.env` file present but ignored (project uses `.env.local` or vice versa)

**Diagnosis:**
```bash
python scripts/check_env.py
```

**What to look for:**
- Any `✘ MISSING` line indicates the root cause
- If all vars show as present but token endpoint still fails → check if the server was restarted

**Fix:**
1. Add missing vars to the correct env file
2. Restart the dev server (Next.js caches env vars on startup)
3. Re-run `check_env.py` to confirm
4. Re-run `check_token_endpoint.py` to verify the endpoint now returns a valid token

**Do not proceed to Layer 3 or 4 until this passes.**

---

## Pattern 2 — Broken Token Endpoint

**Symptoms:**
- `curl` or `check_token_endpoint.py` returns non-200 status
- Response body is missing `token` or `url` fields
- Token value present but does not begin with `eyJ`
- Frontend shows "Failed to get token" or similar connection error

**Root cause:**
- API route file is missing or has a syntax error
- Route uses wrong HTTP method (GET vs POST) for the endpoint shape expected by frontend
- `AccessToken` constructed incorrectly (identity missing, grant missing)
- `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are swapped
- Room service or agent dispatch call throws and the handler returns early without a token

**Diagnosis:**
```bash
python scripts/check_token_endpoint.py --url http://localhost:3000/api/livekit/token
```

Also check:
```bash
curl -X POST http://localhost:3000/api/livekit/token \
  -H "Content-Type: application/json" \
  -d '{"participantName": "debug-user"}'
```

**What to look for:**
- HTTP status code (500 = server error, 404 = route missing, 400 = bad request shape)
- Presence of `token`, `url` fields in response
- Whether token begins with `eyJ`

**Fix:**
1. If 404: check that the route file exists at the correct path
2. If 500: check server logs for the exact error thrown inside the handler
3. If token missing: inspect `AccessToken` construction — `toJwt()` must be called and returned
4. If token present but malformed: the API key/secret may be transposed or empty

---

## Pattern 3 — Worker Not Running

**Symptoms:**
- Token endpoint succeeds and returns a valid token
- Frontend connects to the room but agent never joins
- `useVoiceAssistant()` state stays at `idle` or `connecting`
- No `🚀 Agent starting for room:` log line appears anywhere
- Room participant count stays at 1 (only the user)

**Root cause:**
- Python worker was never started
- Worker crashed on startup (check terminal output)
- Worker started but registered under a different `agent_name` than what the token endpoint dispatches
- Worker is running but consuming a different `LIVEKIT_URL` (e.g., `.env` vs `.env.local` mismatch)
- Multiple worker instances running — dispatch fires the wrong one

**Diagnosis:**
```bash
python scripts/check_worker_status.py
```

Also check directly:
```bash
ps aux | grep -E "python|livekit" | grep -v grep
```

Expected terminal output from a healthy worker:
```
✅ Agent server ready
   Connected to: wss://your-project.livekit.cloud
   Agent name: your-agent-name
   Waiting for dispatch...
```

**Fix:**
1. If no worker process: start it — `python your_agent.py dev`
2. If crashed: read the exception — usually missing env vars or import errors
3. If running but not joining: compare `agent_name` in worker to the agent name dispatched in token endpoint
4. If wrong URL: confirm the worker reads from the same env file as the token endpoint

---

## Pattern 4 — Session Not Initializing

**Symptoms:**
- Agent joins the room (participant appears)
- No voice activity — silence from agent
- Worker shows no `🎤 USER SAID:` log lines even after speaking
- `useVoiceAssistant()` state stays at `connecting` after agent joins

**Root cause:**
- Microphone not published by frontend (`canPublish: false` in token grant, or mic blocked)
- `AgentSession` not started (`await session.start(...)` missing or erroring)
- STT provider key missing — session starts but STT provider throws on first audio frame
- `vad` not loaded — voice is never detected as speech

**Diagnosis:**
- Check browser DevTools console for WebRTC errors
- Check worker log for exception after `🚀 Agent starting for room:`
- Confirm `canPublish: true` in the token grant
- Confirm STT provider key is set

**Fix:**
1. If mic permission blocked: prompt user to allow — this is a browser setting, not a code fix
2. If `canPublish` false: fix the token endpoint grant
3. If STT key missing: add the correct key and restart worker
4. If `session.start()` throws: read the exception in worker logs — often a model config issue

---

## Pattern 5 — Transcript Not Updating

**Symptoms:**
- Agent speaks (audio heard) but transcript box shows nothing
- Worker logs show `AGENT SAYING:` but frontend transcript stays empty
- User speech detected in worker logs but not reflected in UI

**Root cause:**
- UI is not subscribing to `dataReceived` events from the room
- Agent is not publishing transcripts as data messages (no `room.local_participant.publish_data(...)`)
- Transcript state is being set but the component is not mounted inside `LiveKitRoom`
- Transcript update logic depends on state (`data.type`) check that doesn't match what the worker sends

**Diagnosis:**
- In browser DevTools: add a breakpoint or log in the `dataReceived` handler
- Check worker code for `publish_data` calls on `user_speech_committed` and `agent_speech_committed`
- Confirm the component rendering the transcript is a child of `LiveKitRoom`

**Fix:**
1. If worker not publishing: add `publish_data` calls in the session event handlers
2. If frontend not subscribing: ensure `room.on('dataReceived', handler)` is wired up inside `LiveKitRoom`
3. If `data.type` mismatch: log raw payload and align frontend string to what worker sends

---

## Pattern 6 — UI Renders, No Real Connection

**Symptoms:**
- Page loads fully with control bar, visualizer, transcript box
- Clicking "Start Voice" shows a spinner and resolves to connected state
- No audio from agent — silence
- Worker logs show no activity for this session
- Visualizer shows static animation, never changes on voice input

**Root cause:**
- Demo illusion: the UI is fully rendered but the session never completed properly
- Token endpoint returned a token but `LiveKitRoom` silently failed to connect
- Worker dispatched to wrong room name (name mismatch between frontend request and actual room)
- Agent joined but `session.start()` was never called — agent is in the room but not processing

**This is the most dangerous failure pattern.** The app appears complete. The user may report it as working. It is not.

**Diagnosis:**
- Check `useConnectionState()` — must reach `Connected`, not just `Connecting`
- Check room participant count — must show at least 2 (user + agent)
- Check worker terminal — must show `USER SAID:` after speaking
- Check browser console for `[LIVEKIT]` errors

**Fix:**
1. Confirm `connectionState === ConnectionState.Connected` in component
2. Confirm agent participant identity appears in `useRemoteParticipants()`
3. Confirm worker logs show activity specific to this room name
4. If worker shows no activity: re-check dispatch — agent may have been dispatched to a different room

---

## Pattern 7 — Visualizer State Never Changes

**Symptoms:**
- `BarVisualizer` renders
- Speaking into mic produces no animation change
- Agent speaking produces no bar movement

**Root cause:**
- `audioTrack` prop passed to `BarVisualizer` is `undefined`
- Microphone not published or not subscribed
- Wrong track source passed — `Source.Microphone` vs `Source.Camera`
- `useVoiceAssistant()` returns no audio track because agent has not joined

**Diagnosis:**
- Log `audioTrack` from `useVoiceAssistant()` — if undefined, audio is not flowing
- Check `useTracks()` — confirm tracks are present for both local and remote participants

**Fix:**
1. Ensure agent has joined before expecting `audioTrack` to be non-null
2. Confirm `audio={true}` on `LiveKitRoom`
3. Pass the correct `audioTrack` from `useVoiceAssistant()` to `BarVisualizer`

---

## Pattern 8 — Multiple Agents Joining Same Room

**Symptoms:**
- Session starts normally for the first user
- Second user connecting produces two agent responses
- Worker logs show the same agent joining the same room twice
- Conversation is echoed or duplicated

**Root cause:**
- Multiple worker processes running simultaneously
- `agent_name` not set, causing any available worker to respond to any dispatch
- Token endpoint dispatching by class name instead of a unique `agent_name`

**Diagnosis:**
```bash
ps aux | grep python | grep -v grep
```
Should show only one agent process.

**Fix:**
1. Kill duplicate workers: `pkill -f your_agent.py`
2. Set a unique `agent_name` in `@server.rtc_session(agent_name="your-unique-name")`
3. Confirm the token endpoint dispatches using the exact same name

---

## Pattern 9 — Supabase Dependency Failure

**Symptoms (in projects that use Supabase):**
- Voice session starts but structured results (order confirmation, saved records) never appear
- Tool calls execute but return empty results
- Worker logs show `supabase` client errors or missing `SUPABASE_URL`

**Root cause:**
- `SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` not set in Python worker's env
- Worker reading from a different `.env` file than the Next.js frontend
- Supabase local instance not running when `SUPABASE_URL` is `http://localhost:54321`

**Diagnosis:**
```bash
python scripts/check_env.py  # check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
curl http://localhost:54321   # if using local Supabase
```

**Fix:**
1. Add Supabase vars to the env file the Python worker loads (often `../.env.local` relative to the agents folder)
2. If using local Supabase: start it with `supabase start`
3. Re-run the full validation loop after fixing

---

## Pattern 10 — Avatar Layer Fails Silently

**Symptoms (in projects with avatar integration):**
- Voice agent works without avatar — audio and transcript functional
- Avatar video panel renders but shows nothing
- Worker logs show no avatar-related entries after session starts

**Root cause:**
- Avatar provider key (`LEMONSLICE_API_KEY` or equivalent) not set
- Avatar session started before `session.start()` completes — race condition
- Avatar SDK not installed: `pip install "livekit-agents[lemonslice]~=1.3"`

**Diagnosis:**
- Check worker logs for `avatar` keyword — should show init attempt and result
- Check `check_env.py` output for avatar provider keys

**Fix:**
1. Set the required avatar provider keys in env
2. Ensure `avatar_session.start(session, room)` is called after `session.start()`
3. Install the avatar SDK plugin
4. Re-run validation without avatar first — confirm base session works before adding avatar

---

## Pattern 11 — Agent Stops on Backchanneling ("uh-huh", "okay")

**Symptoms:**
- Voice session works — agent speaks and responds to user
- Agent stops speaking awkwardly when user says "uh-huh", "okay", "mm-hmm"
- Conversation flow feels unnatural — agent interrupts itself frequently
- User cannot acknowledge long explanations without breaking agent flow
- `useVoiceAssistant()` state switches from `speaking` to `listening` on brief user acknowledgments

**Root cause:**
- Default VAD-only interruption treats ALL speech as interruption
- Agent cannot distinguish backchanneling from true interruptions
- Adaptive interruption not enabled (Python SDK < 1.5.0 or config missing)

**Diagnosis:**
```bash
# Check SDK version
pip show livekit-agents | grep Version
# Must be >= 1.5.0 for adaptive interruption support
```

Check `AgentSession` config in worker code:
```python
# Look for this line:
turn_handling={"interruption": {"mode": "adaptive"}}
```

**What to look for:**
- SDK version below 1.5.0 → upgrade required
- No `turn_handling` parameter in `AgentSession` → defaults to VAD-only
- `turn_handling` present but mode is `"vad"` → adaptive not enabled
- Worker logs on startup should show: `Interruption mode: adaptive`

**Fix:**

1. **Upgrade SDK if needed:**
```bash
pip install --upgrade livekit-agents
```

2. **Add adaptive interruption config to AgentSession:**
```python
from livekit.agents import AgentSession
from livekit.plugins import openai, silero

session = AgentSession[UserState](
    userdata=userdata,
    stt=openai.STT(model="whisper-1"),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(voice="alloy"),
    vad=silero.VAD.load(),
    turn_handling={
        "interruption": {"mode": "adaptive"},
    },
)
```

3. **Restart worker process**

4. **Test backchanneling:**
   - Start session and let agent speak
   - Say "uh-huh" during agent speech
   - Expected: agent continues speaking
   - If agent stops: config not applied or SDK version too old

**Common mistakes:**
- ❌ Importing non-existent modules: `from livekit import turn_detector` (ImportError)
- ❌ Using `TurnHandlingOptions` as a class instea of dict
- ❌ Overcomplicating config with nested `turn_detection` settings
- ✅ Just use a simple dict: `turn_handling={"interruption": {"mode": "adaptive"}}`

**See also:**
- [adaptive-interruption-handling.md](adaptive-interruption-handling.md) for complete implementation guide

---

## Failure Triage Order

If everything appears broken, diagnose in this order:

1. **Layer 1 first** — run `check_env.py`. Do not skip.
2. **Layer 2 second** — run `check_token_endpoint.py`. Do not proceed if token is invalid.
3. **Worker third** — run `check_worker_status.py` and check terminal output.
4. **Browser last** — only open browser debug after Layers 1-3 pass.

Skipping this order wastes time. A broken token endpoint will make every browser symptom misleading.
