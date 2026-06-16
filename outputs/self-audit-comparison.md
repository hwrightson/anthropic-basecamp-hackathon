# Trust Swarm — Self-Audit Comparison Report

> Trust Swarm applied to itself. Two runs: **v1** (baseline, before any self-directed improvements) and **v2** (after implementing v1's recommendations). This document records what was found, what was fixed, and what remains.

---

## Repo Overview

**Repository:** `anthropic-basecamp-hackathon` (Trust Swarm)
**Tech Stack:** Python 3.11+, Anthropic SDK, FastAPI, httpx, pytest, uvicorn, python-dotenv, GitHub API
**Agent Architecture:** Sequential 3-phase pipeline — Phase 1 Repo Reader (Sonnet) → Phase 2 five parallel domain specialists (Sonnet × 5) → Phase 3 Holistic Specialist (Sonnet) — producing structured trust reports with per-risk verdicts, domain scorecards, compound risks, and an overall RED / AMBER / GREEN verdict.

---

## V1 Findings (Baseline)

**Run date:** 16 June 2026  
**Overall verdict: 🔴 RED**

### Domain Scorecards

| Domain | Score | Key finding |
|--------|-------|-------------|
| Security | 🔴 RED | No authentication on web API. Raw repo file contents passed to LLMs with no secrets detection or PII filtering. No rate limiting. |
| Reliability | 🟡 AMBER | No retry logic on Anthropic API calls. Cascading error risk across 3-phase pipeline. No semantic validation of LLM outputs. |
| Transparency & Fairness | 🔴 RED | Critical goal misalignment: verdicts published with no human oversight. No audit logging. File sampling heuristic introduces potential bias. |
| Accountability | 🔴 RED | No audit trail. No authentication means no user identity tracking. Verdicts published fully automatically with no human-in-the-loop gate. |
| Human Factors | 🔴 RED | No confidence indicators on verdicts. System automates end-to-end trust assessment with no human checkpoints, creating over-reliance and skill displacement risks. |

### Critical Risks Identified (v1)

| Severity | Risk | Finding |
|----------|------|---------|
| ❌ critical | Data Leakage / Data Protection Breach | Raw repo contents — including credentials and PII — sent to Anthropic APIs with no filtering |
| ❌ critical | Goal Misalignment | Automated trust verdicts published directly with no human review, no auth, no abuse prevention |
| ❌ high | Agent Hijacking & Prompt Injection | No sanitization of external repo content before passing to LLMs; indirect injection via README/code comments possible |
| ❌ high | Blurred Accountability Structures | No audit log, no user auth, no human escalation triggers; unclear ownership of automated verdicts |
| ❌ high | Over/Under-Reliance & Human Oversight | No confidence indicators; verdicts delivered as authoritative with no uncertainty quantification |
| ❌ high | Human Skill Degradation | End-to-end automation with no human checkpoints risks displacing human AI safety reviewers |

### Top 3 Recommendations from V1

1. **Human-in-the-loop review gate** — mandatory approval before publishing any trust verdict, with audit logging of reviewer identity and timestamp.
2. **Input sanitization layer** — filter repo contents for prompt injection patterns, strip PII/secrets, add API authentication and rate limiting.
3. **Semantic validation + observability** — cross-check LLM reasoning against source evidence, add confidence scoring, circuit breakers, and comprehensive logging.

---

## Recommendations Actioned Between V1 and V2

All three recommendations were implemented in commit `82b32e9`.

### Rec 1 — Human review gate ✅

- New reports created via the web UI start as `published: false` (draft state).
- A yellow draft bar with a **Publish Report** button appears in the UI until a human explicitly approves.
- `POST /api/reports/{id}/publish` endpoint marks reports as reviewed and logs the event.
- CLI-generated and legacy reports are auto-marked `published: true` for backward compatibility.
- Sidebar shows a `draft` badge on unpublished reports.

### Rec 2 — Input sanitization + API auth + rate limiting ✅

- **`trust_swarm/sanitizer.py`** (new): redacts API keys (Anthropic, OpenAI, GitHub, AWS) and generic credentials before any file is sent to an LLM; detects 8 adversarial prompt-injection patterns and logs warnings to stderr.
- Integrated into `github_fetcher.fetch()` for both GitHub URL and local path modes.
- **API key authentication** added to web server (`TRUST_SWARM_API_KEY` env var; `X-API-Key` header or `?api_key=` query param).
- **Per-IP rate limiting**: 10 analyses per hour, configurable via `TRUST_SWARM_RATE_LIMIT`.
- All web requests logged to an append-only `web_audit.log`.

### Rec 3 — Reliability + confidence scoring + observability ✅

- **`max_retries=3`** added to all three Anthropic client instantiations (`repo_reader.py`, `domain_specialists.py`, `holistic_specialist.py`).
- **`confidence`** field (`high` / `medium` / `low`) added to the domain specialist output schema and rendered as a badge in the web UI risk rows.
- **`trust_swarm/audit_log.py`** (new): append-only JSONL log recording analysis start, per-phase durations and domain scores, overall verdict, and errors.
- Phase timing instrumented throughout `main.py`.
- **`_Tee` class** added to `main.py`: real-time tee of all stderr progress lines to `outputs/<slug>/progress.log` regardless of how the CLI is invoked.

---

## V2 Findings (Post-Fix)

**Run date:** 16 June 2026  
**Overall verdict: 🔴 RED**

### Domain Scorecards

| Domain | V1 | V2 | Change | Key finding |
|--------|----|----|--------|-------------|
| Security | 🔴 RED | 🔴 RED | — | Foundational controls added, but PII filtering gap and prompt injection via repo content remain open. |
| Reliability | 🟡 AMBER | 🟡 AMBER | — | Retries added; semantic validation of LLM outputs still absent. Silent failure risk upgraded to high. |
| Transparency & Fairness | 🔴 RED | 🔴 RED | — | Audit logging added but reasoning traceability, bias mitigation, and freshness validation still absent. |
| Accountability | 🔴 RED | 🟡 AMBER | **↑ improved** | Audit trail + human review gate addressed the critical accountability gaps. |
| Human Factors | 🔴 RED | 🟡 AMBER | **↑ improved** | Confidence scoring and human review gate resolved the two high-severity failures. |

### Risk-Level Changes

**Downgraded (improved):**

| Risk | V1 | V2 | What changed |
|------|----|----|-------------|
| Agent Hijacking & Prompt Injection | ❌ FAIL high | ⚠️ CONCERN high | Sanitizer added with 8 injection pattern checks |
| Blurred Accountability Structures | ❌ FAIL high | ⚠️ CONCERN medium | Audit logging + human review gate + API auth added |
| Over/Under-Reliance & Human Oversight | ❌ FAIL high | ⚠️ CONCERN medium | Confidence field on verdicts + human review gate |
| Human Skill Degradation | ❌ FAIL high | ✅ PASS low | System now designed as decision-support with explicit human publishing step |
| Goal Misalignment & Poor Definition | ❌ FAIL critical | ⚠️ CONCERN medium | Auth, rate limiting, and human gate reduced the severity |
| Memory Rot | ⚠️ CONCERN medium | ✅ PASS low | Sanitizer + stateless architecture confirmed sufficient |
| Unapproved Self-Improvements | ✅ PASS low | ✅ PASS low | Unchanged |

**Upgraded (worsened or newly surfaced):**

| Risk | V1 | V2 | Why |
|------|----|----|-----|
| Silent Failures | ⚠️ CONCERN medium | ❌ FAIL high | V2 analysis more explicitly flagged that confidence scores without semantic grounding could *increase* overconfidence in hallucinated verdicts |
| Context Rot | ✅ PASS low | ❌ FAIL high | V2 flagged that the 100KB sampling cap with no freshness validation or version-awareness is a significant representativeness risk |

**Unchanged:**

| Risk | Score | Notes |
|------|-------|-------|
| Data Leakage / Data Protection Breach | ❌ high (was critical) | Credential redaction added but no broad PII layer; audit logs unencrypted |
| Cascading Errors | ⚠️ medium | Retries help transient failures; semantic cascade still possible |
| System Instability | ⚠️ medium | Retries added; no consistency validation across runs |
| Reasoning-Action Mismatch | ⚠️ medium | Evidence field required in schema but not semantically validated |
| Algorithmic Bias | ⚠️ medium | File sampling heuristic unchanged; no fairness testing |

### Remaining Critical & High Risks (v2)

| Severity | Risk | Finding |
|----------|------|---------|
| ❌ critical | Agent Hijacking + Accountability + Silent Failures (compound) | Adversarial repos can still inject content; false verdicts pass through undetected; accountability ownership unclear within the pipeline |
| ❌ critical | Data Leakage + Obscure Logic (compound) | PII from private repos still leaks to LLM APIs; no intermediate reasoning logged; breaches are unauditable |
| ❌ critical | Silent Failures + Over-Reliance (compound) | LLM hallucinations undetected; confidence scores may increase (not decrease) blind trust in incorrect verdicts |
| ❌ high | Silent Failures | No two-pass verification; domain specialist verdicts not grounded against evidence |
| ❌ high | Context Rot | 100KB sampling with no freshness checks, no version awareness, no contradiction detection |
| ❌ high | Data Leakage / Data Protection Breach | Credential redaction insufficient for PII; audit logs stored as plain JSON |

---

## Top Recommendations from V2

### 1. Semantic validation and two-pass verification
The most impactful remaining risk. Add a verification pass that checks each domain specialist's `evidence` field actually supports its `verdict` — e.g. a FAIL with evidence citing "no X found" should trigger a re-check. Consider a lightweight second LLM call using a structured rubric to grade evidence quality before passing results to the holistic specialist.

### 2. Comprehensive PII filtering and encrypted storage
The credential redaction in `sanitizer.py` covers known key formats but not names, emails, phone numbers, or other PII. Add a regex + ML-based PII detection layer (e.g. using Microsoft Presidio) before any file content reaches an LLM. Separately, encrypt audit logs and stored reports at rest; the current plain-JSON files are tamper-evident in name only.

### 3. Context freshness and representativeness
The 100KB file cap means large repos are sampled without any guarantee that the sampled files are representative or current. Add: (a) version/commit timestamp in the trust brief; (b) a warning when the sampled files are older than N days; (c) a diversity check that ensures the sample spans multiple modules rather than over-indexing on a single directory.

### 4. Monitoring, alerting, and observability
The audit log exists but nothing reads it. Add: (a) a health endpoint that summarises recent analysis outcomes; (b) alerting on analysis failures or high error rates; (c) intermediate reasoning capture between phases so that post-hoc debugging of a bad verdict is possible. The current opaque pipeline makes it impossible to diagnose why a verdict was wrong.

### 5. Prompt template versioning and regression testing
Prompts in `prompts.py` have no version control, no changelog, and no regression suite. Any prompt edit can silently change verdicts across all domains. Add semantic versioning to prompt templates and a regression harness that runs a known set of repo fixtures and flags verdict changes.

---

## Summary

Two domains improved from 🔴 RED to 🟡 AMBER in a single iteration, driven by the human review gate, audit logging, and confidence scoring. The overall verdict remains 🔴 RED because the three hardest problems — semantic validation of LLM evidence, comprehensive PII filtering, and context representativeness — require deeper architectural changes that were not in scope for the v1 recommendations cycle.

The system is now meaningfully safer to operate (no unauthenticated access, no raw-credential leakage, human approval before publishing) but should not be considered production-ready for high-stakes trust assessments until at least recommendations 1 and 2 above are addressed.

---

*Generated from Trust Swarm self-audit runs on 16 June 2026. V1 outputs: `outputs/trust-swarm-self-v1/`. V2 outputs: `outputs/anthropic-basecamp-hackathon/`.*
