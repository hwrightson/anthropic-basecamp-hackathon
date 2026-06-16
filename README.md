<p align="center">
  <img src="assets/trust-swarm-logo.png" alt="Trust Swarm" width="600"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/powered%20by-Claude%20Opus%20%2B%20Sonnet-blueviolet" alt="Powered by Claude"/>
  <img src="https://img.shields.io/badge/risks%20assessed-22-orange" alt="22 risks"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/tests-21%20passing-brightgreen" alt="21 tests"/>
</p>

# Trust Swarm

A subagent swarm that assesses the trustworthiness of any AI/agentic GitHub repository against a 22-risk evaluation framework. Point it at a repo and get back a structured report: per-risk verdicts with evidence, domain scorecards, compound risk analysis, and an overall **GREEN / AMBER / RED** verdict.

---

## Table of Contents

- [Why Trust Swarm?](#why-trust-swarm)
- [How it works](#how-it-works)
- [The 22 risks assessed](#the-22-risks-assessed)
- [Setup](#setup)
- [Usage](#usage)
- [Output](#output)
- [Repo structure](#repo-structure)
- [Running tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

---

## Why Trust Swarm?

Agentic AI systems — repos that use LLMs to take real-world actions — are proliferating faster than the tooling to evaluate them safely. A star count or a slick README tells you nothing about whether an agent leaks data, loops infinitely, ignores human oversight, or pursues goals its authors didn't intend.

Trust Swarm applies a structured, evidence-based risk framework — automatically, in under a minute — so you can make an informed decision before adopting, deploying, or building on top of any agentic repo.

---

## How it works

Three sequential phases. Phase 2 runs in parallel.

```
GitHub URL
    │
    ▼
[Phase 1] Repo Reader          (claude-sonnet-4-6)
    │  Fetches repo via GitHub API → structured trust brief
    │
    ▼
[Phase 2] 5 Domain Specialists (claude-sonnet-4-6 × 5, parallel)
    ├── Security
    ├── Reliability
    ├── Transparency & Fairness
    ├── Accountability
    └── Human Factors
    │
    ▼
[Phase 3] Holistic Specialist  (claude-opus-4-7)
    │  Reviews all 5 domain reports → compound/emergent risk analysis
    │
    ▼
Markdown report (stdout) + trust_report.json
```

The Repo Reader fetches up to 50 files (100 KB cap), prioritising `agent`, `prompt`, `system`, `iam`, `policy`, `config`, `handler`, `orchestrat`, and `README` paths. Domain specialist prompts are generated programmatically from the risk definitions — no manual per-risk prompt writing.

---

## The 22 risks assessed

Each risk is assessed with a `PASS / CONCERN / FAIL` verdict, a severity (`critical / high / medium / low`), and cited evidence (specific file, line reference, or observable absence).

### Security

| Risk | Root Causes | Evaluation Options |
|------|------------|-------------------|
| **Agent Hijacking & Prompt Injection** | Unsanitised external input; indirect injection via processed data; insufficient input validation | Input sanitisation; restricted agent tool access; human gating for sensitive decisions |
| **Tool Misuse & Confused Deputy** | Overly permissive IAM roles; failure to apply least privilege; insufficient tool call scope validation | IAM permissions audit; principle of least privilege; tool call scope validation |
| **Data Leakage / Data Protection Breach** | Overly permissive data access; missing PII detection; agent surfacing raw content without filtering | IAM permissions; principle of least privilege; secrets/PII scanning |
| **Model Extraction / Evasion Attacks** | Insufficient system prompt protection; absence of rate limiting; adversarial inputs crafted to elicit model internals | System prompt protection; rate limiting; adversarial input testing |
| **Memory & Data Poisoning** | Unvalidated writes to persistent memory; insufficient provenance checking; adversarial write access to memory store | Information injection testing; memory validation gates; provenance logging |

### Reliability

| Risk | Root Causes | Evaluation Options |
|------|------------|-------------------|
| **System Instability** | Probabilistic model variance; unexpected inputs; external tool failures | Output comparison; consistency checks across N runs |
| **Silent Failures** | Hallucinations; factual inconsistencies; incomplete data | Two-pass verification; human red teaming; hard negatives testing |
| **Cascading Errors** | Inter-agent dependencies; lack of error handling; faulty logic in one agent | Output validation; fault injection testing; end-to-end trace comparison |
| **Endless Cycles / Looping** | Recursive logic; lack of termination condition; converging tool outputs | Timeouts; repeated-state detection; token usage logging |
| **Role & Specification Drift** | Role ambiguity in system prompts; accumulated context shifting behaviour; unclear task decomposition boundaries | Role constraint validation; trace audit against declared role specification |
| **Reasoning-Action Mismatch** | LLM hallucination of reasoning traces; structural decoupling of reasoning from execution steps | Reasoning-action validation; mismatch injection testing; structured output verification |

### Transparency & Fairness

| Risk | Root Causes | Evaluation Options |
|------|------------|-------------------|
| **Algorithmic Bias** | Biased training data in foundation models; skewed input samples; feedback loops amplifying initial bias | Fairness metrics across demographic groups; edge-case testing; explainability review |
| **Obscure Logic (Black Box)** | Third-party model opacity; insufficient logging of intermediate reasoning; missing chain-of-thought capture | Subagent logging; observability/CloudWatch logs; chain-of-thought capture |
| **Context Rot** | Outdated information; ambiguous/missing contextual details; conflicting data sources; context stuffing | Contradiction testing; recency bias testing; information freshness checks |
| **Goal Misalignment & Poor Definition** | Ambiguous or incomplete goal specification; absent organisational value constraints; misalignment between task objective and stakeholder intent | Policy adherence testing; value constraint validation |

### Accountability

| Risk | Root Causes | Evaluation Options |
|------|------------|-------------------|
| **Unapproved Self-Improvements** | Model updates; data drift; concept drift | Gold standard response dataset comparison; LLM-as-a-judge deviation scoring |
| **Blurred Accountability Structures** | Insufficient human escalation triggers; unclear ownership of automated decisions; missing audit trail | Human gating checks; audit trail verification; escalation trigger testing |
| **Memory Rot** | Unfiltered user input; data pipeline errors; improper memory decay/pruning; malicious data injection | Long horizon recall tests; false memory injection and detection |

### Human Factors

| Risk | Root Causes | Evaluation Options |
|------|------------|-------------------|
| **Over/Under-Reliance & Human Oversight** | Insufficient confidence indicators; missing uncertainty flags; lack of user education; poorly calibrated human-AI trust | Confidence indicator review; uncertainty flag presence; user education assessment |
| **Human Misuse** | Insufficient input policy enforcement; overly permissive guard node configuration; users circumventing use restrictions | Guard node policy review; input restriction testing |
| **Human Skill Degradation** | Automation displacing human judgment; skills atrophy from over-reliance; inadequate change management | Human-in-the-loop mechanism review; oversight adequacy assessment |
| **Undefined or Negative Value** | Misaligned success metrics; excessive API calls from inefficient orchestration; poorly scoped use case; high latency vs manual baseline | Cost per workflow run tracking; time-to-insight vs manual baseline; user utility ratings |

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY (required)
# Add GITHUB_TOKEN for private repos (optional)
```

---

## Usage

```bash
python -m trust_swarm https://github.com/org/repo
```

Progress is printed to stderr as each phase runs. The final Markdown report goes to stdout; `trust_report.json` is written to the current directory.

```bash
# Save the report
python -m trust_swarm https://github.com/org/repo > report.md
```

---

## Output

**Markdown report sections:**
1. Repo Overview — tech stack, agent architecture, key files, safety mechanisms, notable absences
2. Domain Scorecards — GREEN / AMBER / RED per domain with top findings
3. Risk Detail — per-risk verdict, evidence, severity for all 22 risks
4. Compound Risks — cross-domain interactions identified by the holistic specialist
5. Top Recommendations — three prioritised actions
6. Overall Verdict — GREEN / AMBER / RED

**`trust_report.json`** — full structured output including the repo brief, all domain results, and holistic analysis.

---

## Repo structure

```
trust-swarm/
├── trust_swarm/                  # Main package
│   ├── __init__.py
│   ├── __main__.py               # CLI entry point (python -m trust_swarm)
│   ├── main.py                   # Orchestration pipeline (Phases 1-3)
│   ├── github_fetcher.py         # GitHub API integration & file prioritisation
│   ├── repo_reader.py            # Phase 1: structured trust brief generation
│   ├── domain_specialists.py     # Phase 2: parallel domain specialist agents
│   ├── holistic_specialist.py    # Phase 3: compound risk synthesis (Opus)
│   ├── risks.py                  # 22-risk taxonomy — root causes, evaluation options
│   ├── prompts.py                # Programmatic prompt generation from risk definitions
│   └── report.py                 # Markdown + JSON report assembly
├── tests/                        # pytest suite (21 tests)
│   ├── conftest.py
│   ├── test_github_fetcher.py    # GitHub API fetch (mocked)
│   ├── test_prompts.py           # Prompt generation coverage
│   ├── test_report.py            # Report formatting
│   └── test_risks.py             # Risk definition integrity
├── outputs/                      # Example run outputs
│   ├── autogen/
│   │   ├── report.md
│   │   └── progress.log
│   └── autogpt/
│       ├── report.md
│       └── progress.log
├── assets/
│   └── trust-swarm-logo.png
├── docs/                         # Design specs and implementation plans
├── .env.example                  # Environment variable template
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Running tests

```bash
pytest
```

21 tests covering risk definitions, GitHub fetching (mocked), prompt generation, and report formatting.

---

## Contributing

Contributions are welcome. The highest-value areas are:

- **Risk definitions** (`trust_swarm/risks.py`) — new risks, refined root causes, or better evaluation options
- **Prompt quality** (`trust_swarm/prompts.py`) — improved specialist instructions
- **Fetcher heuristics** (`trust_swarm/github_fetcher.py`) — smarter file prioritisation for dense repos
- **Test coverage** (`tests/`) — edge cases, additional repo fixtures

Please open an issue before submitting a large PR so we can discuss scope first.

---

## License

MIT — see [LICENSE](LICENSE) for details.
