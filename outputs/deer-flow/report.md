
============================================================
## Repo Overview

**Repository:** `bytedance/deer-flow`  
**Tech Stack:** Python, FastAPI, TypeScript, Next.js, pnpm, uv, Nginx, Docker, LangGraph, Anthropic SDK, OpenAI SDK, Playwright, pytest, ruff, ESLint, Prettier, Better Auth, GitHub Actions, pre-commit  
**Agent Architecture:** Gateway-based multi-agent system with LangGraph runtime, skill-based architecture, MCP support, and embedded/containerized sandbox execution modes.

**Safety mechanisms observed:**
- Blocking I/O guard skill enforces runtime detection of blocking calls in async paths via tests/blocking_io/, using Blockbuster detector with teeth verification (red→green test pattern)
- Skill-based architecture with explicit skill SOPs and references for maintainer orchestration, smoke testing, and blocking-IO detection
- Pre-commit hooks run ruff lint/format for backend Python and ESLint/Prettier for frontend TypeScript/JavaScript
- Harness/app boundary enforcement: backend/packages/harness/deerflow/ must not import app.*, keeping harness publishable and app-agnostic
- Sandbox permissions and security-sensitive operations (bash/file-write tools, skill installation, remote execution) called out as security-sensitive in maintainer skill
- GitHub issue template config redirects security vulnerabilities to private security policy, not public issues
- Deployment mode selection prefers local mode to avoid Docker network issues, with automatic fallback
- Service health checks verify frontend, API Gateway, LangGraph-compatible API, and frontend routes before declaring success
- Frontend route smoke checks validate key routes under /workspace explicitly
- Make targets for lint, test, test-blocking-io, and check enforce quality gates before deployment

**Notable absences:**
- No system prompts found in the provided files; agent system prompts likely reside in backend/ code not included in this sample
- No IAM policies or role definitions found in the sample; authentication/authorization config may be in .env, config.yaml, or backend code
- No explicit rate limiting configuration found in the provided files
- No PII filtering layer or data sanitization logic visible in the skill documentation or config samples
- No explicit input validation rules found in the skill markdown; validation may be in backend handler code
- No mention of audit logging, observability, or monitoring beyond basic health checks
- No explicit user consent or data retention policies found in the provided files
- No sandboxing escape detection or runtime integrity monitoring mentioned beyond blocking-IO guards
- No mention of model output filtering, content moderation, or prompt injection defenses in the provided files
- No explicit API key rotation, secret management, or credential lifecycle policy found

## Domain Scorecards

| Domain | Score | Summary |
|--------|-------|---------|
| Security | 🔴 RED | Security domain shows significant gaps with no visible input validation, PII filtering, IAM policies, or prompt injection defenses in provided files. Critical security-sensitive operations identified but controls not documented in sampled artifacts. |
| Reliability | 🟡 AMBER | The repository demonstrates moderate reliability practices through skill-based architecture, health checks, and quality gates, but lacks critical mechanisms for detecting silent failures, validating reasoning-action alignment, and monitoring cascading errors in its multi-agent system. The absence of output validation, observability, and explicit error handling patterns raises concerns for production reliability. |
| Transparency & Fairness | 🟡 AMBER | The Transparency & Fairness domain shows moderate risk with structured architecture providing some goal clarity but lacking critical bias mitigation, audit trails, and context freshness validation mechanisms. Skill-based design offers partial transparency through SOPs, but black-box foundation models and absent observability create accountability gaps. |
| Accountability | 🟡 AMBER | The repository demonstrates foundational code quality controls and security awareness (blocking-IO guards, pre-commit hooks, security issue routing) but lacks explicit accountability infrastructure for model governance, decision auditing, and memory integrity across its multi-agent system. |
| Human Factors | 🟡 AMBER | Human Factors domain shows moderate trust concerns primarily from absence of user-facing safeguards and value measurement. While skill-based architecture preserves human oversight, the system lacks confidence indicators, input policy enforcement visibility, and value metrics. |

## Risk Detail

### Security

**⚠️ Agent Hijacking & Prompt Injection** (high)
> No system prompts found in provided files - backend code not sampled. No explicit input validation rules found in skill markdown (.agent/skills/*/SKILL.md). No mention of prompt injection defenses, input sanitization, or guard nodes in safety_mechanisms_observed. The skill-based architecture exists but without visible input validation at skill boundaries, indirect prompt injection via processed data remains possible.

**⚠️ Tool Misuse & Confused Deputy** (high)
> Maintainer skill (.agent/skills/deerflow-maintainer-orchestrator/SKILL.md) explicitly calls out 'bash/file-write tools, skill installation, remote execution' as security-sensitive but no IAM policies or role definitions found. No principle of least privilege enforcement visible. Sandbox permissions mentioned but implementation details absent. Tool call scope validation not documented in provided files.

**❌ Data Leakage / Data Protection Breach** (high)
> No PII filtering layer or data sanitization logic visible in skill documentation. No IAM policies found to restrict data access. GitHub issue template (.github/ISSUE_TEMPLATE/config.yml) redirects security vulnerabilities to private policy but no PII detection, secrets scanning, or data redaction mechanisms documented. Agent could surface raw content without filtering.

**⚠️ Model Extraction / Evasion Attacks** (medium)
> No system prompt protection mechanisms found - system prompts not in provided files. No rate limiting configuration found despite use of Anthropic SDK and OpenAI SDK. No adversarial input testing documented. Blocking-IO guard exists for runtime safety but no defenses against adversarial queries crafted to elicit model internals or bypass reasoning constraints.

**⚠️ Memory & Data Poisoning** (medium)
> LangGraph runtime with MCP support mentioned but no memory validation gates, provenance logging, or write validation visible. Skill installation is security-sensitive per maintainer skill but no validation of skill integrity or memory store write controls documented. No information injection testing or memory provenance checking mechanisms found in provided files.

### Reliability

**⚠️ System Instability** (medium)
> Gateway-based multi-agent system with LangGraph runtime and MCP support introduces complexity. Deployment mode selection 'prefers local mode to avoid Docker network issues, with automatic fallback' suggests known instability issues. Service health checks verify multiple components (frontend, API Gateway, LangGraph-compatible API, frontend routes), indicating multi-component dependency fragility. No evidence found of output comparison or consistency checks across N runs for probabilistic model outputs. Skill-based architecture with external tool calls (bash/file-write, skill installation, remote execution noted as security-sensitive) creates external dependency points, but no fault tolerance mechanisms documented.

**⚠️ Silent Failures** (medium)
> No explicit mention of model output filtering, content moderation, or hallucination detection. System uses Anthropic SDK and OpenAI SDK for LLM calls but no two-pass verification, hard negatives testing, or factual consistency checks documented. Skill documentation (.agent/skills/) provides SOPs and troubleshooting guides but no validation of LLM-generated outputs against ground truth. Health checks verify service availability but not output correctness. No audit logging or observability mentioned beyond basic health checks, making silent failures difficult to detect post-deployment.

**⚠️ Cascading Errors** (medium)
> Multi-agent system with skill-based architecture (.agent/skills/deerflow-maintainer-orchestrator/, smoke-test/, blocking-io-guard/) creates inter-agent dependencies. Maintainer orchestrator skill coordinates multiple skills, creating cascading risk. No explicit error handling patterns documented in skill SOPs. Service health checks provide end-to-end validation but no fault injection testing or intermediate validation checkpoints mentioned. Harness/app boundary enforcement prevents import violations but does not address runtime error propagation. No observability or distributed tracing to track error cascades across agents.

**⚠️ Role & Specification Drift** (medium)
> Skill-based architecture with explicit SKILL.md files and SOPs (.agent/skills/blocking-io-guard/SKILL.md, deerflow-maintainer-orchestrator/SKILL.md, smoke-test/SKILL.md) provides role definitions. However, 'No system prompts found in the provided files; agent system prompts likely reside in backend/ code not included' means actual runtime role specifications are not visible. Maintainer orchestrator skill description mentions 'security-sensitive operations' including skill installation and remote execution, suggesting complex, potentially overlapping agent roles. No role constraint validation or trace audit against declared specifications documented. Accumulated context in multi-turn interactions could shift behavior without detection mechanisms.

**⚠️ Reasoning-Action Mismatch** (medium)
> System uses LLM backends (Anthropic SDK, OpenAI SDK) for agent reasoning but no reasoning-action validation documented. Skill SOPs provide procedural guidance (.agent/skills/smoke-test/references/SOP.md, .agent/skills/blocking-io-guard/references/sop-skeleton.md) but no verification that LLM reasoning traces match actual tool invocations. Security-sensitive operations (bash/file-write tools, skill installation, remote execution) noted in maintainer skill but no structured output verification or reasoning trace validation. No mismatch injection testing or reasoning-vs-execution auditing mechanisms found. Blocking-IO guard uses test-based verification (red→green pattern) for code behavior but not for reasoning consistency.

**✅ Endless Cycles / Looping** (low)
> No evidence of recursive agent logic or looping patterns in the skill documentation. Health checks with explicit validation of frontend routes and service endpoints suggest bounded execution. Deployment health checks 'verify frontend, API Gateway, LangGraph-compatible API, and frontend routes before declaring success' implies termination conditions. No mention of repeated-state detection or token usage logging, but the skill-based architecture with explicit SOPs (.agent/skills/*/SKILL.md) suggests bounded, task-oriented execution rather than open-ended loops. LangGraph runtime typically includes cycle detection, though not explicitly documented here.

### Transparency & Fairness

**⚠️ Algorithmic Bias** (medium)
> No evidence of bias mitigation, fairness testing, or demographic parity checks found in the trust brief. The system integrates Anthropic SDK and OpenAI SDK foundation models whose training data bias characteristics are opaque. No fairness metrics, edge-case testing for protected groups, or bias detection mechanisms observed in .agent/skills/ documentation, pre-commit hooks, or test targets (Make targets include lint, test, test-blocking-io but no fairness validation). While absence of evidence is not evidence of presence, lack of any fairness safeguards in a multi-agent system with external model dependencies presents risk of inherited or amplified bias.

**⚠️ Obscure Logic (Black Box)** (medium)
> Notable absence: 'No mention of audit logging, observability, or monitoring beyond basic health checks' and 'No system prompts found in the provided files; agent system prompts likely reside in backend/ code not included in this sample.' The skill-based architecture with explicit SOPs (.agent/skills/*/SKILL.md, references/SOP.md) provides some structural transparency, but no chain-of-thought logging, subagent reasoning capture, or intermediate decision tracing observed. Health checks validate service availability but not reasoning transparency. LangGraph runtime architecture suggests multi-step reasoning, but without observability logs or structured output capture, agent decision paths remain opaque to auditors.

**⚠️ Context Rot** (medium)
> No mechanisms observed for information freshness validation, recency checks, or contradiction detection. Skill references include static markdown files (.agent/skills/blocking-io-guard/references/good-anchor-rules.md, .agent/skills/smoke-test/references/SOP.md, troubleshooting.md) with no versioning or staleness detection. MCP support and gateway architecture suggest external data retrieval, but no timestamp validation, source conflict resolution, or context stuffing mitigation found. Deployment health checks verify service availability but not data currency. Pre-commit hooks enforce code quality but not contextual information validity.

**✅ Goal Misalignment & Poor Definition** (low)
> Skill-based architecture provides explicit goal specification through structured SKILL.md files for each capability (blocking-io-guard, deerflow-maintainer-orchestrator, smoke-test). Maintainer skill explicitly calls out 'security-sensitive operations (bash/file-write tools, skill installation, remote execution)' as requiring careful handling. Harness/app boundary enforcement ensures separation of concerns. GitHub issue template redirects security vulnerabilities to private channels, demonstrating organizational value alignment. While no explicit policy adherence testing mentioned, the structured skill SOPs with references and troubleshooting guides provide clear task boundaries and stakeholder intent alignment. Red-to-green test pattern in blocking-IO guard shows value constraint validation in practice.

### Accountability

**⚠️ Unapproved Self-Improvements** (medium)
> No evidence of model version control, update approval workflows, or drift detection mechanisms found in provided files. The tech stack includes Anthropic SDK and OpenAI SDK suggesting external model usage, but no versioning/pinning configurations or change management processes are documented. The maintainer orchestrator skill (.agent/skills/deerflow-maintainer-orchestrator/SKILL.md) and skill-based architecture exist, but lack explicit approval gates for model updates or data/concept drift monitoring. No gold standard response datasets or LLM-as-a-judge deviation scoring mechanisms observed in the test infrastructure beyond blocking-IO guards.

**⚠️ Blurred Accountability Structures** (medium)
> Maintainer orchestrator skill references security-sensitive operations (bash/file-write tools, skill installation, remote execution) as documented in .agent/skills/deerflow-maintainer-orchestrator/SKILL.md, but no explicit human escalation triggers, ownership assignments, or decision audit trails are visible. GitHub issue template (.github/ISSUE_TEMPLATE/config.yml) redirects security issues but doesn't establish accountability chains for automated decisions. No audit logging or observability infrastructure mentioned beyond basic health checks. The gateway-based multi-agent system with LangGraph runtime lacks documented human-in-the-loop gating for high-risk operations, though security sensitivity is acknowledged.

**⚠️ Memory Rot** (medium)
> No evidence of memory management, verification, decay, or pruning mechanisms in the provided files. The multi-agent system with MCP support and sandbox execution modes suggests stateful operation, but no filtering of user input into persistent memory, data pipeline validation for memory stores, or false memory detection is documented. No long-horizon recall tests or memory injection testing found in test infrastructure (pytest references exist but test scope focuses on blocking-IO guards per tests/blocking_io/). Input validation rules and PII filtering layers are notably absent. The skill-based architecture lacks explicit safeguards against malicious data injection into agent memory.

### Human Factors

**⚠️ Over/Under-Reliance & Human Oversight** (medium)
> No confidence indicators, uncertainty flags, or user education mechanisms found in the provided files. System prompt excerpts are empty and no documentation addresses system limitations or trust calibration. The smoke-test/references/SOP.md and skill documentation focus on technical validation but lack user-facing guidance on when to trust agent outputs. Health checks verify service availability but not output reliability indicators.

**⚠️ Human Misuse** (medium)
> Sandbox permissions and security-sensitive operations are mentioned in deerflow-maintainer-orchestrator/SKILL.md (bash/file-write tools, skill installation, remote execution) but no explicit input policy enforcement or guard node configuration is visible. No input validation rules found in skill markdown files. The blocking-io-guard focuses on async I/O patterns, not user input restrictions. GitHub security policy redirects vulnerabilities privately but does not indicate runtime misuse prevention mechanisms.

**⚠️ Undefined or Negative Value** (medium)
> No cost tracking, API call efficiency metrics, time-to-insight measurements, or user utility ratings found in provided files. Health checks validate service availability but not value delivery. No misaligned success metrics visible, but also no defined success metrics at all. Deployment mode preference for local over Docker (to avoid network issues) suggests practical optimization, but no quantitative value assessment framework present. Use case scoping not documented in provided files.

**✅ Human Skill Degradation (Agency & Job Displacement)** (low)
> Searched for automation displacement indicators and human-in-the-loop mechanisms. The skill-based architecture with explicit SOPs (smoke-test/references/SOP.md, blocking-io-guard/references/sop-skeleton.md) suggests structured workflows requiring human setup and oversight. Maintainer orchestration skill implies human developers remain in control of skill deployment and system changes. No evidence of autonomous decision-making that bypasses human judgment. The system appears designed as a developer tool augmenting rather than replacing human capabilities.

## Compound Risks

**🔴 Data Leakage / Data Protection Breach + Obscure Logic (Black Box) + Blurred Accountability Structures** (critical)
> PII or sensitive data could be exposed through agent outputs with no audit trail to trace the leak source, no filtering mechanisms to prevent it, and no clear ownership for remediation, creating undetectable and unattributable data breaches

**🔴 Agent Hijacking & Prompt Injection + Memory & Data Poisoning + Over/Under-Reliance & Human Oversight** (critical)
> Injected malicious instructions could poison agent memory stores, causing the system to consistently produce corrupted outputs that humans trust without question due to lack of confidence indicators or uncertainty flags

**🔴 Silent Failures + Obscure Logic (Black Box) + Blurred Accountability Structures** (critical)
> LLM hallucinations or reasoning failures occur without detection mechanisms, produce no audit trail for investigation, and have no clear owner responsible for catching errors, enabling systematic propagation of false information

**🟡 Tool Misuse & Confused Deputy + Unapproved Self-Improvements + Human Misuse** (high)
> Security-sensitive tools (bash/file-write, skill installation, remote execution) could be invoked through confused deputy attacks with no approval workflows to gate changes and no input policy enforcement to prevent misuse escalation

**🟡 Cascading Errors + Memory Rot + Context Rot** (high)
> Errors propagate across multi-agent dependencies while stale or corrupted memory and context accumulate without validation, creating compounding failure modes that become increasingly difficult to diagnose or recover from

**🟡 Reasoning-Action Mismatch + Blurred Accountability Structures + Over/Under-Reliance & Human Oversight** (high)
> Agent reasoning traces may not match executed actions, with no verification mechanisms, no audit trail to detect mismatches, and no user warnings to prevent blind trust in potentially inconsistent behaviors

**🟡 Algorithmic Bias + Context Rot + Undefined or Negative Value** (high)
> Biased foundation models operating on stale context produce systematically unfair outputs with no measurement framework to detect declining value or discriminatory impact over time

**🟠 System Instability + Silent Failures + Human Misuse** (medium)
> Multi-component system fragility causes intermittent failures that go undetected, while users continue to rely on or misuse an unreliable system without awareness of degraded operational state

## Top Recommendations

1. Implement comprehensive audit logging and observability infrastructure across all agents with structured reasoning traces, tool invocation records, data access logs, and human decision points to enable accountability and incident investigation
2. Deploy layered input validation and output filtering at all trust boundaries including prompt injection defenses at skill entry points, PII redaction before external calls, memory write validation gates, and hallucination detection on LLM outputs
3. Establish human-in-the-loop approval workflows for security-sensitive operations (bash/file-write, skill installation, remote execution) with confidence indicators on all agent outputs, uncertainty flags for ambiguous reasoning, and clear escalation paths for high-risk decisions

## Overall Verdict

# 🔴 RED
