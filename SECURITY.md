# Security Policy

## Scope

This repository contains:
- Agent skill instructions (`SKILL.md`)
- Python validation scripts (`scripts/`)
- Reference documentation (`references/`)

The scripts perform read-only operations: they scan environment files, make HTTP requests to local dev servers, and check running processes. They do not write to databases, modify configuration, or deploy anything.

---

## Sensitive Information

**This repository must never contain:**
- LiveKit API keys or secrets
- OpenAI, Deepgram, or Anthropic API keys
- Supabase service role keys
- Any JWT tokens
- Any value from a `.env` or `.env.local` file

The scripts in `scripts/` are designed to **confirm presence** of secrets without printing their values. If a script inadvertently prints a secret, treat it as a bug and report it.

---

## Reporting a Vulnerability

If you discover a security issue in this repository — including a script that could expose secrets, a logic flaw that could be exploited, or a documentation error that could lead to credential exposure — please report it responsibly:

1. **Do not open a public GitHub issue** for security vulnerabilities.
2. Contact the maintainer directly via the repository's contact information.
3. Include a description of the issue, steps to reproduce, and potential impact.

---

## What This Skill Does NOT Do

- It does not run `supabase db reset` or any destructive database command.
- It does not write to LiveKit rooms or publish data.
- It does not store, transmit, or log any credentials.
- It does not make requests to external services (only to `localhost` by default).

---

## Environment File Safety

The `check_env.py` script reads `.env` and `.env.local` files to confirm variable presence. It displays confirmation messages like:

```
✔  LIVEKIT_API_SECRET    [set, 64 chars]
```

It never prints the actual value of any secret variable.

---

## Dependencies

The validation scripts use only Python standard library modules (`os`, `sys`, `pathlib`, `subprocess`, `urllib`). No third-party packages are required to run the scripts, which eliminates supply chain risk for this tooling.
