# Adaptive Interruption Handling

> Reference for implementing natural conversation flow in LiveKit voice agents.
> Requires livekit-agents >= 1.5.0 (Python) or >= 1.2.0 (Node.js).

---

## What is Adaptive Interruption?

Adaptive interruption is a LiveKit Agents feature that distinguishes between two types of user speech during agent turns:
- **Backchanneling**: "uh-huh", "okay", "mm-hmm", "I see" → agent CONTINUES speaking
- **True interruption**: "wait", "hold on", "can you clarify?" → agent STOPS and yields turn

Without adaptive interruption, the default VAD-only mode stops the agent on ANY speech detection. This creates awkward pauses when users naturally acknowledge what they're hearing.

---

## When Adaptive Interruption Matters Most

Use adaptive interruption when your agent:
1. **Delivers coaching or feedback** — user says "uh-huh" during score explanations
2. **Explains educational content** — learners naturally say "okay", "got it" while listening
3. **Reads policies or instructions** — customers show engagement with acknowledgments
4. **Conducts interviews** — candidates acknowledge questions/feedback with brief responses

**Do NOT use adaptive interruption if:**
- Conversations are very short (single Q&A exchanges)
- You want the agent to stop on any sound (hyper-responsive mode)
- SDK version is below 1.5.0 (Python) or 1.2.0 (Node.js)

---

## Correct Implementation (Python)

### ✅ Simple Dict Configuration

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

**That's it. No special imports. Just a plain dict.**

---

## Common Pitfalls — What NOT to Do

### ❌ WRONG: Importing Non-Existent Modules

```python
# FAILS: turn_detector does not exist in livekit.agents
from livekit import turn_detector  # ImportError!
```

### ❌ WRONG: Using TurnHandlingOptions as a Class

```python
# FAILS: TurnHandlingOptions is just a type alias for dict
from livekit.agents import TurnHandlingOptions
session = AgentSession(
    turn_handling=TurnHandlingOptions(
        turn_detection=turn_detector.MultilingualModel(),  # Not needed!
        interruption={"mode": "adaptive"},
    ),
)
```

### ❌ WRONG: Overcomplicating the Config

```python
# FAILS: No need for nested turn_detection — adaptive mode handles this
turn_handling={
    "turn_detection": MultilingualModel(),  # Unnecessary!
    "interruption": {"mode": "adaptive"},
}
```

### ✅ CORRECT: Simple Dict

```python
# Just use a plain dict - no special imports needed
turn_handling={"interruption": {"mode": "adaptive"}}
```

---

## Requirements Checklist

Before enabling adaptive interruption, verify:

- [ ] **SDK version >= 1.5.0 (Python) or >= 1.2.0 (Node.js)**
  - Check: `pip show livekit-agents | grep Version`
  - Expected: `Version: 1.5.0` or higher

- [ ] **VAD is enabled**
  - Example: `vad=silero.VAD.load()`
  - Adaptive interruption requires VAD to detect speech boundaries

- [ ] **STT with aligned transcripts**
  - Supported: OpenAI Whisper, Deepgram, AssemblyAI
  - Not supported: STT without word-level timing

- [ ] **Non-realtime LLM**
  - Supported: OpenAI, Anthropic, Google Gemini
  - Not an issue for most common LLM providers

---

## Verification Steps

### Step 1: Verify SDK Version

```bash
pip show livekit-agents | grep Version
```

**Expected output:**
```
Version: 1.5.0  # or higher
```

If version is below 1.5.0, upgrade:
```bash
pip install --upgrade livekit-agents
```

### Step 2: Test Backchanneling

**What to do:**
1. Start a voice session
2. Let the agent begin speaking (ask for a long explanation)
3. While agent is speaking, say "uh-huh" or "okay"

**Expected behavior:**
- ✅ Agent continues speaking without interruption
- ✅ Backchanneling appears in transcript but doesn't break agent turn

**If agent stops on "uh-huh":**
- Adaptive interruption is NOT active → check config

### Step 3: Test True Interruption

**What to do:**
1. While agent is speaking, say clearly: "Wait, can you clarify that?"
2. Use assertive interruption phrases: "Hold on", "Stop", "I have a question"

**Expected behavior:**
- ✅ Agent stops speaking mid-sentence
- ✅ Agent yields turn to user
- ✅ User can ask their clarifying question

**If agent ignores interruption:**
- Check VAD sensitivity (may be too high)
- Check microphone levels
- Try more assertive interruptions with higher volume

---

## Debugging Adaptive Interruption

### Problem: Agent still stops on "uh-huh"

**Diagnosis:**
1. Verify `turn_handling` dict is present in `AgentSession` config
2. Check SDK version: `pip show livekit-agents | grep Version`
3. Ensure VAD is loaded: `vad=silero.VAD.load()`
4. Check agent startup logs for turn_handling initialization

**What to look for in logs:**
```
✅ Agent session starting
   Interruption mode: adaptive  # Must show "adaptive"
```

**Fix:**
- If logs show `Interruption mode: vad` → config not applied
- Restart worker after changing config
- Confirm `turn_handling` is correctly indented under `AgentSession(...)`

### Problem: Agent never stops (ignores all interruptions)

**Diagnosis:**
1. Check VAD thresholds — may be set too high
2. Verify microphone input levels in browser DevTools
3. Test with clear, loud interruptions: "STOP!", "WAIT!"

**What to look for:**
- VAD not detecting speech at all → check microphone permissions
- VAD detecting speech but turn not ending → check STT alignment support

**Fix:**
- Lower VAD `min_speech_duration` if available
- Ensure STT provider supports word-level timestamps
- Test with known-working STT (OpenAI Whisper recommended)

### Problem: ImportError for turn_detector or TurnHandlingOptions

**Error message:**
```
ImportError: cannot import name 'turn_detector' from 'livekit'
```

**Root cause:**
- Attempting to import modules that don't exist in the SDK

**Fix:**
```python
# Remove all turn_detector imports
# Remove TurnHandlingOptions imports
# Just use a plain dict:
turn_handling={"interruption": {"mode": "adaptive"}}
```

---

## Cost & Performance

### LiveKit Cloud
- **Cost**: Unlimited (free) — model runs on LiveKit infrastructure
- **Self-hosted**: 40,000 requests/month free tier
- **Latency**: Minimal (~10-20ms added to turn detection)

### Performance Impact
- Model runs on LiveKit Cloud servers (not your infrastructure)
- No additional compute required on worker side
- Negligible bandwidth increase (classification done server-side)

---

## Rollback Plan

If adaptive interruption causes unexpected behavior, easily revert to VAD-only mode:

### Option 1: Remove turn_handling Parameter
```python
session = AgentSession[UserState](
    userdata=userdata,
    stt=openai.STT(model="whisper-1"),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(voice="alloy"),
    vad=silero.VAD.load(),
    # turn_handling removed → defaults to VAD-only
)
```

### Option 2: Explicitly Set VAD Mode
```python
turn_handling={"interruption": {"mode": "vad"}}
```

Both options immediately restore default VAD-only interruption behavior.

---

## Real-World Example

### Use Case: HR Interview Coach

**Problem:**
- Agent delivers feedback scores and explanations
- Candidates naturally say "uh-huh", "okay" while listening
- VAD-only mode caused agent to stop mid-sentence awkwardly

**Solution:**
```python
turn_handling={"interruption": {"mode": "adaptive"}}
```

**Result:**
- Agent continues speaking through acknowledgments
- Conversation flow became natural
- Agent still stops properly when candidate asks "Wait, can you explain that score?"

---

## Documentation References

- **Official Docs**: [LiveKit Adaptive Interruption](https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling/)
- **SDK Requirements**: Python 1.5.0+, Node.js 1.2.0+
- **API Reference**: Pass `turn_handling` as dict to `AgentSession` constructor

---

## Evidence Template

When validating adaptive interruption implementation, use this format:

```
### Adaptive Interruption Test

**Configuration:**
turn_handling={"interruption": {"mode": "adaptive"}}

**SDK Version:**
livekit-agents 1.5.0

**Backchanneling Test:**
- Agent speaking: "Your interview score is 85 out of 100. This reflects strong communication..."
- User: "uh-huh" (during agent speech)
- Agent: [continues speaking without stopping]
- ✅ PASS

**True Interruption Test:**
- Agent speaking: "The next category we evaluated was problem-solving..."
- User: "Wait, can you explain the score again?"
- Agent: [stops immediately and yields turn]
- ✅ PASS

**Verdict:** Adaptive interruption functioning correctly.
```

---

## Validation Checklist

Use this before declaring adaptive interruption working:

- [ ] SDK version verified (>= 1.5.0 for Python, >= 1.2.0 for Node.js)
- [ ] `turn_handling={"interruption": {"mode": "adaptive"}}` set in AgentSession
- [ ] VAD is enabled and loaded
- [ ] STT provider supports word-level alignment (OpenAI Whisper, Deepgram, etc.)
- [ ] Backchanneling test passed (agent continues on "uh-huh")
- [ ] True interruption test passed (agent stops on "wait, hold on")
- [ ] Worker logs show `Interruption mode: adaptive` on startup
- [ ] No ImportError for turn_detector or TurnHandlingOptions

**Only check all boxes after raw output confirms each behavior.**
