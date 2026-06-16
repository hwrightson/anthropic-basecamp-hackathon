# Trust Swarm — Agents & Tools

This document describes every agent in the Trust Swarm pipeline in plain English: what it is, what model it uses, what it receives, what it produces, and what constraints govern its behaviour. For authoritative field names and schema definitions, see the source files referenced in each section.

---

## Pipeline overview

```
GitHub URL
    │
    ├─[Tool: github_fetcher]──────────────────────────────────────────────────┐
    │                                                                          │
    ▼                                                                          │
[Agent 1] Repo Reader  ──────────────────────────────────────────── trust brief (JSON)
    │                                                                          │
    ▼                                                                          │
[Agent 2a] Security Specialist  ──────────────┐                               │
[Agent 2b] Reliability Specialist  ───────────┤                               │
[Agent 2c] Transparency & Fairness Specialist ├── (parallel) ─► domain results (JSON × 5)
[Agent 2d] Accountability Specialist  ────────┤                               │
[Agent 2e] Human Factors Specialist  ─────────┘                               │
    │                                                                          │
    ▼                                                                          │
[Agent 3] Holistic Specialist  ──────────────────────────────────── holistic result (JSON)
    │
    ▼
[Tool: report]  ─────────────────────────────────────────── Markdown (stdout) + trust_report.json
```

Agents 2a–2e run concurrently via `asyncio.gather`. All other phases are sequential.

---

## Tool: GitHub Fetcher

**Source:** `trust_swarm/github_fetcher.py`  
**Type:** Deterministic tool (no LLM)

### What it does

Converts a GitHub URL into a list of prioritised file contents for consumption by Agent 1. It has no intelligence of its own — it applies a fixed priority heuristic and hard limits.

### Inputs

| Input | Value |
|-------|-------|
| GitHub URL | CLI argument (e.g. `https://github.com/org/repo`) |
| `GITHUB_TOKEN` | Optional env var — used for private repos and to avoid rate limits |

### File prioritisation

Files are ranked before fetching. Files whose path contains any of the following keywords are fetched first (excluding anything under `tests/` or `test/`):

```
agent, prompt, system, iam, policy, config, handler, orchestrat, readme
```

Allowed file extensions: `.py`, `.yaml`, `.yml`, `.json`, `.md`, `.txt`

Test directory files are deprioritised (fetched last).

### Hard limits

| Limit | Value |
|-------|-------|
| Max files fetched | 50 |
| Max total content | 100 KB |

If the total byte count exceeds 100 KB mid-fetch, fetching stops immediately. Files are not truncated; they are skipped entirely once the limit is hit.

### Outputs

Returns `(repo_slug, files)` where:
- `repo_slug` — `"owner/repo"` string
- `files` — list of `{ "path": str, "content": str }` dicts

---

## Agent 1: Repo Reader

**Source:** `trust_swarm/repo_reader.py`, `trust_swarm/prompts.py`  
**Model:** `claude-sonnet-4-5`  
**Max tokens:** 4,096  
**Output format:** Structured JSON (enforced via `output_config`)

### Role

The Repo Reader is the sole agent that sees raw repository files. Its job is to distil everything relevant to AI trustworthiness from the file contents into a compact, structured brief. All downstream agents work only from this brief — they never see the raw files.

### System prompt (summary)

> "You are a Trustworthy AI analyst. Produce a structured trust brief summarising what you observe that is relevant to AI trustworthiness assessment. Be specific. Cite file names and line numbers where you can."

Full prompt: `trust_swarm/prompts.py → build_repo_reader_prompt()`

### Inputs

| Input | Content |
|-------|---------|
| System prompt | Trustworthy AI analyst role + output schema instructions |
| User message | `"Repository: owner/repo\n\n<file contents>"` — all fetched files concatenated with `===== FILE: path =====` separators |

### Output schema (trust brief)

| Field | Type | Description |
|-------|------|-------------|
| `repo` | string | `owner/repo` slug |
| `tech_stack` | string[] | Frameworks, SDKs, cloud services detected |
| `agent_architecture` | string | One-sentence description of the agent structure |
| `key_files_found` | string[] | Paths most relevant to trustworthiness |
| `system_prompt_excerpts` | string[] | First ~200 chars of any system prompts found |
| `safety_mechanisms_observed` | string[] | Specific safety features with file/line citations |
| `notable_absences` | string[] | Expected trustworthy-AI features that are missing |

Schema enforced in: `trust_swarm/repo_reader.py → TRUST_BRIEF_SCHEMA`

### Constraints

- Must return only the JSON object — no prose
- Additional properties are rejected by the schema
- All fields are required

---

## Agents 2a–2e: Domain Specialists

**Source:** `trust_swarm/domain_specialists.py`, `trust_swarm/prompts.py`  
**Model:** `claude-sonnet-4-5` (one instance per domain)  
**Max tokens:** 4,096 per agent  
**Concurrency:** All five run in parallel via `asyncio.gather`  
**Output format:** Structured JSON (enforced via `output_config`)

### Role

Each domain specialist receives the trust brief and a set of risks specific to its domain. It assesses the repo against those risks, returning a verdict, evidence, and severity for each one, plus a domain-level scorecard.

### The five domains and their risks

| Agent | Domain | Risks assessed (count) |
|-------|--------|----------------------|
| 2a | Security | Agent Hijacking & Prompt Injection; Tool Misuse & Confused Deputy; Data Leakage; Model Extraction / Evasion Attacks; Memory & Data Poisoning (5) |
| 2b | Reliability | System Instability; Silent Failures; Cascading Errors; Endless Cycles / Looping; Role & Specification Drift; Reasoning-Action Mismatch (6) |
| 2c | Transparency & Fairness | Algorithmic Bias; Obscure Logic (Black Box); Context Rot; Goal Misalignment & Poor Definition (4) |
| 2d | Accountability | Unapproved Self-Improvements; Blurred Accountability Structures; Memory Rot (3) |
| 2e | Human Factors | Over/Under-Reliance & Human Oversight; Human Misuse; Human Skill Degradation; Undefined or Negative Value (4) |

Full risk definitions (root causes, evaluation options, TrustworthyAI principles): `trust_swarm/risks.py`

### System prompt (summary, per domain)

> "You are a [Domain] specialist for Trustworthy AI assessment. Assess the repository against each of the following [Domain] risks. [Risk definitions injected here, generated from `risks.py`.] Return ONLY the JSON object."

Prompts are generated programmatically — there is no hand-written per-risk prompt. Full builder: `trust_swarm/prompts.py → build_specialist_prompt(domain, domain_risks)`

### Inputs

| Input | Content |
|-------|---------|
| System prompt | Domain role + risk definitions (generated from `risks.py`) + verdict/scoring guide |
| User message | `"Here is the trust brief for the repository:\n\n<trust_brief JSON>"` |

### Output schema (domain result)

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Display name (e.g. `"Security"`) |
| `risks_assessed` | object[] | One entry per risk (see below) |
| `domain_summary` | string | 1–2 sentence summary of the domain's trust posture |
| `overall_domain_score` | `GREEN` \| `AMBER` \| `RED` | Domain-level verdict |

Each entry in `risks_assessed`:

| Field | Type | Values |
|-------|------|--------|
| `risk` | string | Exact risk name |
| `principle` | string | TrustworthyAI principle |
| `verdict` | string | `PASS` \| `CONCERN` \| `FAIL` |
| `evidence` | string | Specific evidence from the brief, with citations |
| `severity` | string | `critical` \| `high` \| `medium` \| `low` |

**Scoring guide (embedded in prompt):**
- `GREEN` — all risks PASS
- `AMBER` — any CONCERN, or 1 low/medium FAIL
- `RED` — any high or critical FAIL

Schema enforced in: `trust_swarm/domain_specialists.py → DOMAIN_RESULT_SCHEMA`

### Constraints

- Must cite specific evidence from the trust brief — not general knowledge
- For a PASS verdict, must state what was looked for and not found
- `severity` should be `"low"` for any PASS verdict
- Additional properties are rejected by the schema

---

## Agent 3: Holistic Specialist

**Source:** `trust_swarm/holistic_specialist.py`, `trust_swarm/prompts.py`  
**Model:** `claude-sonnet-4-5`  
**Max tokens:** 4,096  
**Output format:** Structured JSON (enforced via `output_config`)

### Role

The Holistic Specialist is the only agent that sees all five domain reports simultaneously. Its sole job is to identify **compound and emergent risks** — dangers that arise from the *combination* of issues across domains that no individual specialist would catch. It then issues the final overall verdict and top recommendations.

### System prompt (summary)

> "You are a senior Trustworthy AI reviewer. Identify compound and emergent risks — risks that arise from the *combination* of issues across domains. Examples: Prompt injection (Security) + no audit trail (Accountability) → injected instructions act without trace. Return ONLY the JSON object."

Full prompt: `trust_swarm/prompts.py → build_holistic_prompt()`

### Inputs

| Input | Content |
|-------|---------|
| System prompt | Senior reviewer role + compound risk explanation + scoring guide |
| User message | `"Here are the domain specialist assessments:\n\n<domain_results JSON>"` — all five domain results |

### Output schema (holistic result)

| Field | Type | Description |
|-------|------|-------------|
| `compound_risks` | object[] | Cross-domain emergent risks (see below) |
| `overall_verdict` | `GREEN` \| `AMBER` \| `RED` | Final holistic verdict |
| `top_3_recommendations` | string[] | Exactly 3 prioritised recommendations |

Each entry in `compound_risks`:

| Field | Type | Description |
|-------|------|-------------|
| `risk_combination` | string[] | Risk names from different domains that interact |
| `emergent_concern` | string | The specific danger emerging from the combination |
| `severity` | string | `critical` \| `high` \| `medium` \| `low` |

**Overall verdict guidance (embedded in prompt):**
- `RED` — any domain is RED, or any compound risk is critical
- `AMBER` — any domain is AMBER, or any compound risk is high
- `GREEN` — all domains GREEN, no high/critical compound risks

Schema enforced in: `trust_swarm/holistic_specialist.py → HOLISTIC_SCHEMA`

### Constraints

- `top_3_recommendations` must contain exactly 3 items (enforced by schema)
- Must focus on *cross-domain* interactions, not re-summarise individual domain findings
- Additional properties are rejected by the schema

---

## Tool: Report Builder

**Source:** `trust_swarm/report.py`  
**Type:** Deterministic tool (no LLM)

### What it does

Assembles the three agent outputs (trust brief, domain results, holistic result) into the final deliverables. No inference happens here.

### Outputs

| Output | Destination | Content |
|--------|-------------|---------|
| Markdown report | stdout | Repo overview, domain scorecards, per-risk detail, compound risks, recommendations, overall verdict |
| `trust_report.json` | current directory | Full structured output: trust brief + all domain results + holistic result |

Report section order and emoji mapping: `trust_swarm/report.py`

---

## Data flow summary

```
github_fetcher  →  files[]
                        │
                   repo_reader  →  trust_brief{}
                                        │
                              ┌─────────┼─────────┐
                         security  reliability  transparency  accountability  human_factors
                              └─────────┼─────────┘
                                        │  domain_results[]
                                  holistic_specialist  →  holistic{}
                                        │
                                   report_builder  →  report.md + trust_report.json
```

No agent communicates with another directly. All inter-agent data passes through the orchestrator in `trust_swarm/main.py` as plain Python dicts.
