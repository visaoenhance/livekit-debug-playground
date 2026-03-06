# Security Policy

Thank you for helping keep **livekit-debug-playground** secure.

This repository demonstrates validation patterns and debugging discipline for LiveKit voice app environments. While it is a skill/tooling repo, we take security reports seriously.

---

## Supported Versions

This repository is maintained on the `main` branch only.

Security and dependency updates may be applied via:
- Dependabot
- CodeQL scanning
- GitHub Secret Scanning

---

## Reporting a Vulnerability

If you discover a security vulnerability:

**Please do NOT open a public GitHub issue.**

Instead, report it via one of the following:
- **GitHub Private Vulnerability Reporting** (preferred)
- **Email:** info@visaoenhance.com

When reporting, please include:
- Description of the vulnerability
- Steps to reproduce (proof-of-concept if available)
- Impact assessment
- Suggested remediation (if known)

**Response expectations**
- Acknowledgement within **48 hours**
- A status update within **7 days** (or sooner if critical)

---

## Scope

This repository:
- Does **not** store production credentials.
- Does **not** ship production infrastructure.
- Is intended for **local LiveKit development** and validation tooling.

The scripts perform read-only operations — they scan environment files, make HTTP requests to local dev servers, and check running processes. They do not write to databases, modify configuration, or deploy anything.

If a vulnerability impacts the **LiveKit platform itself**, please report it directly to LiveKit via their responsible disclosure process.

---

## Sensitive Information

**This repository must never contain:**
- `LIVEKIT_API_SECRET` or any LiveKit API credentials
- `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, or `ANTHROPIC_API_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- Any JWT tokens (any value beginning with `eyJ`)
- Any value from a `.env` or `.env.local` file

The scripts in `scripts/` confirm presence of secrets without printing their values. If a script inadvertently prints a secret, treat it as a bug and report it.

---

## Security Philosophy

This project promotes a validation-first approach:

> **No Evidence. Not done.**

Coding agents should:
- Prove token endpoint responses (valid JWT, correct shape)
- Confirm worker process is running before declaring runtime ready
- Validate voice session behavior with observable evidence
- Never assume success without proof

Security is not a feature. It is a discipline.

Thank you for contributing responsibly.

