# Trust Swarm — Design Spec

**Date:** 2026-06-16
**Status:** Approved

---

## Problem

AI/agentic GitHub repositories carry specific trustworthiness risks that general code review misses. A 22-risk evaluation framework exists but applying it manually is slow and inconsistent. This system automates that assessment using a subagent swarm, producing a structured trustworthiness report for any AI/agentic repo.

---

## Scope

- **In scope:** Static assessment of AI/agentic repositories against the 22-risk framework. Reads code, config, IAM policies, system prompts, and documentation.
- **Out of scope:** Programmatic test execution, implementing fixes, raising PRs.
- **Target repos:** AI/agentic projects using LLMs, multi-agent workflows, or Claude/OpenAI SDKs.

---

## Architecture

Three sequential phases; Phase 2 is internally parallel.

```
GitHub URL
    │
    ▼
[Phase 1] Repo Reader (single Claude call)
    │  Fetches repo via GitHub API, produces structured trust brief
    │
    ▼
[Phase 2] 5 Domain Specialists (parallel via asyncio)
    ├── Security
    ├── Reliability
    ├── Transparency & Fairness
    ├── Accountability
    └── Human Factors
    │
    ▼
[Phase 3] Holistic Specialist (single Claude call)
    │  Reviews all 5 domain reports for compound/emergent risks
    │
    ▼
Final Report (Markdown + JSON)
```

**Platform:** Plain Anthropic Python SDK (`anthropic` package), `asyncio` for parallelism. Same pattern as Basecamp exercises. No Managed Agents beta required.

**Models:**
- Repo Reader: `claude-sonnet-4-6`
- Domain Specialists: `claude-sonnet-4-6` (5 parallel calls)
- Holistic Specialist: `claude-opus-4-7` (cross-domain reasoning benefits from stronger model)

---

## Risk Groupings

The 22 risks from the framework are grouped into 5 domains:

| Domain | Risks |
|--------|-------|
| **Security** | Agent Hijacking & Prompt Injection, Tool Misuse & Confused Deputy, Data Leakage / Data Protection Breach, Model Extraction / Evasion Attacks, Memory & Data Poisoning |
| **Reliability** | System Instability, Silent Failures, Cascading Errors, Endless Cycles / Looping, Role & Specification Drift, Reasoning-Action Mismatch |
| **Transparency & Fairness** | Algorithmic Bias, Obscure Logic (Black Box), Context Rot, Goal Misalignment & Poor Definition |
| **Accountability** | Unapproved Self-Improvements, Blurred Accountability Structures, Memory Rot |
| **Human Factors** | Over/Under-Reliance & Human Oversight, Human Misuse, Human Skill Degradation, Undefined or Negative Value |

---

## Data Model

### Repo Brief (Phase 1 output)

```json
{
  "repo": "org/repo-name",
  "tech_stack": ["Python", "Claude API", "AWS Lambda"],
  "agent_architecture": "coordinator + 3 specialists, Anthropic SDK",
  "key_files_found": ["agents/orchestrator.py", "config.yaml", "iam/policy.json"],
  "system_prompt_excerpts": {
    "coordinator": "...",
    "specialists": ["..."]
  },
  "safety_mechanisms_observed": ["input validation in handler.py"],
  "notable_absences": ["no rate limiting", "no PII filtering layer found"]
}
```

### Domain Specialist Output (Phase 2, one per domain)

```json
{
  "domain": "Security",
  "risks_assessed": [
    {
      "risk": "Agent Hijacking & Prompt Injection",
      "principle": "Security / Invulnerable",
      "verdict": "CONCERN",
      "evidence": "No input sanitisation found in orchestrator.py lines 34-67.",
      "severity": "high"
    }
  ],
  "domain_summary": "Two high-severity security gaps found...",
  "overall_domain_score": "RED"
}
```

`verdict` values: `PASS | CONCERN | FAIL`
`severity` values: `critical | high | medium | low`
`overall_domain_score` values: `GREEN | AMBER | RED`

### Holistic Specialist Output (Phase 3)

```json
{
  "compound_risks": [
    {
      "risk_combination": ["Prompt Injection", "Blurred Accountability"],
      "emergent_concern": "Injected instructions could cause autonomous action with no audit trail",
      "severity": "critical"
    }
  ],
  "overall_verdict": "AMBER",
  "top_3_recommendations": ["...", "...", "..."]
}
```

`overall_verdict` values: `GREEN | AMBER | RED`

---

## File Structure

```
anthropic-basecamp-hackathon/
├── trust_swarm/
│   ├── __init__.py
│   ├── main.py                  # entry point: python -m trust_swarm <github_url>
│   ├── github_fetcher.py        # GitHub API → raw repo content
│   ├── repo_reader.py           # Claude call → structured trust brief
│   ├── domain_specialists.py    # 5 parallel specialist calls via asyncio
│   ├── holistic_specialist.py   # cross-domain compound risk call
│   ├── risks.py                 # 22 risks as structured Python dicts
│   ├── prompts.py               # system prompt builders (generated from risks.py)
│   └── report.py                # assembles final Markdown + JSON output
├── .env.example
└── requirements.txt             # anthropic, httpx, python-dotenv
```

### Entry Point

```
python -m trust_swarm https://github.com/org/repo
```

Prints progress to stderr as it runs (`[Phase 1] Reading repo...`, `[Phase 2] Running 5 domain specialists in parallel...`, etc.) so the swarm activity is visible. Final Markdown report goes to stdout; `trust_report.json` is written to the current directory.

---

## Prompt Generation

Domain specialist system prompts are **generated programmatically** from `risks.py` — no manual prompt writing per risk. Each prompt receives:
1. The specialist's domain name and responsibility
2. The structured risk criteria for its assigned risks (TrustworthyAI principle, sub-dimension, root causes, evaluation options from the framework)
3. The repo brief as user content
4. Output schema (JSON matching the domain specialist data model above)

---

## GitHub Fetcher Behaviour

The fetcher calls GitHub REST API (no auth required for public repos, `GITHUB_TOKEN` env var for private) and pulls:
- Repository file tree (top 2 levels)
- Content of files matching extensions: `*.py`, `*.yaml`, `*.yml`, `*.json`, `*.md`, `*.txt`
- Priority filter: files whose path contains any of `agent`, `prompt`, `system`, `iam`, `policy`, `config`, `handler`, `orchestrat`, `README` are fetched first
- Hard cap: 50 files max, 100KB total content. If cap is reached, lower-priority files (deep nested, test files) are dropped first.

---

## Output

Final Markdown report sections:
1. **Repo Overview** (from brief)
2. **Domain Scorecards** (GREEN/AMBER/RED per domain with top findings)
3. **Risk Detail** (per-risk verdict, evidence, severity)
4. **Compound Risks** (from holistic specialist)
5. **Top Recommendations**
6. **Overall Verdict**

---

## Success Criteria

- Given a valid GitHub URL for an AI/agentic repo, produces a complete trustworthiness report in under 60 seconds
- All 22 risks from the framework are assessed
- Each finding cites specific evidence (file, line reference, or observable absence)
- Compound risks section surfaces at least one cross-domain interaction when present
