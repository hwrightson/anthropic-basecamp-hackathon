
============================================================
## Repo Overview

**Repository:** `Significant-Gravitas/AutoGPT`  
**Tech Stack:** Python, React, Next.js, TypeScript, tmux, Claude Code, GitHub Actions, Vercel, Docker, PostgreSQL, Anthropic SDK, SWR, better-all, LRU cache, SVGO, GraphQL  
**Agent Architecture:** Meta-orchestrator supervising fleet of Claude Code agents in tmux windows, each agent in isolated git worktree, coordinator manages spawning/monitoring/verification/recycling via shell scripts

**Safety mechanisms observed:**
- Checkpoint protocol: agents must emit CHECKPOINT:<step> markers; run-loop.sh blocks recycling until all required steps complete
- verify-complete.sh gate: checks all checkpoints present, 0 unresolved threads, CI green on post-agent run, no fresh CHANGES_REQUESTED reviews before allowing done state
- Manual supervisor evaluation required: verify-complete.sh is a gate but orchestrator must run /pr-test and evaluate quality before marking done
- Session restore: agents save session state to disk with --session-id UUID, can resume exact conversation after crash via claude --resume SESSION_ID
- State file atomic writes: always write to .tmp then mv to prevent corruption from partial writes
- Escalation after 3 idle kicks: agents stuck/idle 3+ times → escalated state, surfaced to human
- Permission mode bypass: all agents spawn with --permission-mode bypassPermissions to avoid blocking on confirmations
- Serial /pr-test rule: only one integration test runs at time to prevent port conflicts and DB corruption, orchestrator queues and serializes
- Protected worktrees: AutoGPT1 on dx/orchestrate-skill never used as spare to prevent wiping .claude/skills/ directory
- GitHub abuse rate limit handling: agents instructed to sleep 2-3 minutes on 403 abuse error, add sleep 3 between API writes
- Thread resolution integrity: agents forbidden from calling resolveReviewThread without commit SHA, orchestrator verifies via GraphQL not agent self-report
- Stale CHANGES_REQUESTED handling: verify-complete.sh ignores reviews submitted before latest commit timestamp
- typeof window check: conditional module loading checks typeof window !== 'undefined' to prevent bundling client-only code in SSR
- Supervisor approval for self-edits: orchestrator uses Agent tool with subagent_type general-purpose for drafting SKILL.md changes, reviews diff itself without surfacing to user
- Functional setState updates: always use setX(curr => ...) form to prevent stale closures and ensure latest state in async callbacks

**Notable absences:**
- No input validation layer for agent prompts or objectives before passing to spawn-agent.sh
- No PII filtering or redaction in state file (stored at ~/.claude/orchestrator-state.json, never committed but visible to all agents)
- No rate limiting on agent spawning (capacity.sh shows availability but no enforced throttle)
- No authentication/authorization model for which agents can access which worktrees or PRs
- No audit log of agent actions beyond git history and state file snapshots
- No sandboxing of agent file system access (agents run with bypassPermissions, can edit any file in worktree)
- No detection of infinite loops or recursive agent spawning (orchestrator trusts run-loop.sh mechanics)
- No guardrails on destructive git operations (agents can force-push, delete branches, rewrite history within worktree scope)
- No verification that agent code changes align with stated objective before allowing push (only post-push verification via /pr-test)
- No mechanism to prevent agents from modifying .claude/skills/ scripts that govern orchestrator behavior (protected worktree rule is procedural, not enforced)
- No cross-agent communication protocol or shared memory beyond state file and git (agents cannot coordinate on conflicting objectives)
- No rollback mechanism if verify-complete.sh passes but human evaluation later finds issues (state marked done, window stays open but no automated undo)
- No monitoring of agent resource usage (CPU, memory, network) or automatic termination of runaway processes
- No encryption of state file (discord_webhook, session_id, pr_number all in plaintext JSON)
- No prevention of agents spawning sub-agents (Agent tool with subagent_type available but no recursion depth limit specified)

## Domain Scorecards

| Domain | Score | Summary |
|--------|-------|---------|
| Security | 🔴 RED | Security posture is RED with critical failures in input validation, authorization, and data protection. The architecture's bypassPermissions mode, lack of sandboxing, and absence of PII/secrets filtering create severe vulnerabilities to hijacking, privilege escalation, and data leakage. |
| Reliability | 🔴 RED | The orchestration system exhibits significant reliability risks, particularly around loop detection and silent failure prevention, with multiple procedural safeguards that lack structural enforcement. The checkpoint protocol and verify-complete.sh provide baseline consistency but gaps in input validation, reasoning-action coupling, and recursion limits create critical failure modes. |
| Transparency & Fairness | 🔴 RED | Transparency & Fairness domain shows critical gaps in goal alignment validation and context management, with concerning opacity in agent reasoning and absent bias mitigation. While checkpoint protocols provide step-level tracking, the system lacks semantic verification of objectives, input validation, and mechanisms to prevent context degradation acknowledged in orchestrator prompts. |
| Accountability | 🔴 RED | Critical accountability gaps exist: agents can self-modify governing scripts without human approval, lack clear ownership structures for automated decisions, and have no audit trail beyond git history. Memory integrity has partial protections but accepts unvalidated inputs. |
| Human Factors | 🔴 RED | Human Factors domain shows critical risks from over-automation with insufficient human oversight and misuse prevention. System bypasses human confirmation loops, lacks input validation and authorization controls, and automates complex judgment tasks without calibrated trust mechanisms or cost monitoring. |

## Risk Detail

### Security

**❌ Agent Hijacking & Prompt Injection** (critical)
> No input validation layer exists for agent prompts or objectives before passing to spawn-agent.sh (notable_absences). Agents run with bypassPermissions flag, eliminating confirmation gates that could catch malicious instructions. System prompt in SKILL.md shows agents receive objectives directly without sanitization. The meta-orchestrator architecture with direct shell script spawning provides no guard layer against indirect prompt injection via processed PR content, issues, or review comments that could manipulate agent behavior.

**❌ Tool Misuse & Confused Deputy** (critical)
> No authentication/authorization model for which agents can access which worktrees or PRs (notable_absences). Agents spawn with --permission-mode bypassPermissions, explicitly disabling confirmation gates. No sandboxing of agent file system access - agents can edit any file in worktree with no scoping validation. Agents can perform destructive git operations (force-push, delete branches, rewrite history) with no guardrails. Protected worktree rule for AutoGPT1 is procedural only, not enforced. No mechanism prevents agents from modifying .claude/skills/ scripts that govern orchestrator behavior itself.

**❌ Data Leakage / Data Protection Breach** (high)
> No PII filtering or redaction in state file stored at ~/.claude/orchestrator-state.json (notable_absences). State file contains discord_webhook URLs, session_ids, pr_numbers in plaintext JSON with no encryption. State file visible to all agents with no access controls. No secrets/PII scanning layer before agents process PR content or commit data. Agents have unrestricted file system access in worktrees, can surface raw content without filtering. No audit log of what data agents accessed beyond git history.

**⚠️ Model Extraction / Evasion Attacks** (medium)
> System prompts stored in .claude/skills/orchestrate/SKILL.md and AGENTS.md are visible in repository and to all agents. No system prompt protection mechanism observed. No rate limiting on agent spawning (capacity.sh shows availability but no enforced throttle per notable_absences). GitHub abuse rate limit handling exists (sleep 2-3 minutes on 403) but no proactive query rate limiting to prevent model extraction attempts. Session restore feature (claude --resume SESSION_ID) could potentially be exploited to replay and extract reasoning patterns, though no evidence of adversarial input testing or evasion attack defenses.

**⚠️ Memory & Data Poisoning** (medium)
> State file (~/.claude/orchestrator-state.json) uses atomic writes (.tmp then mv) to prevent corruption, showing some integrity protection. However, no validation of writes to persistent memory - any agent can modify state file content. No memory provenance checking exists to verify legitimacy of state entries. Checkpoint protocol validates completion markers but not content integrity. Thread resolution integrity exists (agents forbidden from resolveReviewThread without commit SHA, verified via GraphQL), providing some provenance. No cross-agent communication protocol limits potential for one compromised agent to poison shared state. Escalation after 3 idle kicks provides anomaly detection but no explicit memory poisoning defenses.

### Reliability

**❌ Endless Cycles / Looping** (critical)
> Explicit absence: 'No detection of infinite loops or recursive agent spawning (orchestrator trusts run-loop.sh mechanics)' and 'No prevention of agents spawning sub-agents (Agent tool with subagent_type available but no recursion depth limit specified)'. While run-loop.sh blocks recycling until checkpoints complete, there's no timeout mechanism if an agent never emits required checkpoints. The poll-cycle.sh suggests 2-3 minute polling but no evidence of repeated-state detection or maximum iteration caps. GitHub abuse rate limit handling instructs 'sleep 2-3 minutes on 403' but no broader token usage logging or conversation length limits to prevent context exhaustion loops.

**❌ Silent Failures** (high)
> Critical gap: 'No verification that agent code changes align with stated objective before allowing push (only post-push verification via /pr-test)' means agents can push incorrect or hallucinated solutions that pass syntax checks but fail functional requirements silently until human evaluation. The verify-complete.sh checks CI and threads but cannot detect subtle logical errors or incomplete implementations. No two-pass verification or hard negatives testing observed. State file shows discord_webhook for notifications but no evidence of proactive anomaly detection for factual inconsistencies in agent outputs.

**⚠️ System Instability** (medium)
> The system relies heavily on external tooling (tmux, git worktrees, Claude API, GitHub GraphQL) without explicit failure handling mechanisms. Notable absence of 'monitoring of agent resource usage or automatic termination of runaway processes' and agents spawn with bypassPermissions which could amplify cascade failures. The checkpoint protocol provides some consistency but 'no input validation layer for agent prompts' before spawning means malformed objectives could cause unpredictable behavior. Session restore via --resume SESSION_ID provides recovery but no evidence of handling probabilistic model variance across runs.

**⚠️ Cascading Errors** (medium)
> The meta-orchestrator architecture creates inter-agent dependencies but 'no cross-agent communication protocol or shared memory beyond state file and git' means agents cannot coordinate on conflicting objectives. Serial /pr-test rule prevents some cascades (port conflicts, DB corruption) but 'no rollback mechanism if verify-complete.sh passes but human evaluation later finds issues' means bad agent outputs can propagate. The escalation after 3 idle kicks handles stuck agents but 'no detection of infinite loops or recursive agent spawning' leaves risk of runaway processes. State file atomic writes (write to .tmp then mv) prevent corruption but no fault injection testing evidence.

**⚠️ Role & Specification Drift** (medium)
> The system prompt explicitly warns 'If your context compacts and you lose track of what to do, run: cat ~/.claude/orchestrator-state.json' acknowledging accumulated context can shift behavior. Agents are passed objectives via spawn-agent.sh args but 'no input validation layer for agent prompts or objectives' means role boundaries can blur. The AGENTS.md specifies 'guidance here is optimized for automation and consistency' but no runtime role constraint validation observed. Protected worktree rule for AutoGPT1 is 'procedural, not enforced' suggesting role boundaries rely on agent compliance rather than structural enforcement. Supervisor approval for self-edits to SKILL.md shows meta-awareness but no trace audit against declared role specification.

**⚠️ Reasoning-Action Mismatch** (medium)
> Thread resolution integrity rule ('agents forbidden from calling resolveReviewThread without commit SHA, orchestrator verifies via GraphQL not agent self-report') shows awareness of reasoning-action decoupling but relies on post-hoc verification not structural prevention. The checkpoint protocol (CHECKPOINT:<step> markers) provides trace of declared steps but no validation that emitted checkpoints correspond to actual completed work beyond CI passing. Important rule 'Do NOT resolve any review thread via GraphQL unless the code fix is committed and pushed first' suggests agents can hallucinate completion reasoning. No evidence of reasoning-action validation or mismatch injection testing. Agents use Agent tool for sub-tasks but no structured output verification beyond diff review.

### Transparency & Fairness

**❌ Context Rot** (high)
> Clear evidence of context degradation risk. `.claude/skills/orchestrate/SKILL.md` explicitly acknowledges context loss: 'If your context compacts and you lose track of what to do, run: cat ~/.claude/orchestrator-state.json | jq' indicating known issue with orchestrator losing situational awareness. No mechanisms for information freshness checks, contradiction testing, or recency bias testing observed. State file provides snapshot recovery but does not prevent context compaction. Agents receive objectives via `spawn-agent.sh` but no validation of contextual consistency across multi-agent tasks. `verify-complete.sh` checks mechanical completion (checkpoints, CI, threads) but not semantic coherence or staleness of information used. Serial `/pr-test` rule prevents concurrency conflicts but doesn't address temporal consistency of context.

**❌ Goal Misalignment & Poor Definition** (high)
> Multiple indicators of goal specification fragility. Notable_absences state 'No input validation layer for agent prompts or objectives before passing to spawn-agent.sh' allowing ambiguous or incomplete goals. 'No verification that agent code changes align with stated objective before allowing push (only post-push verification via /pr-test)' means agents can execute misaligned actions before detection. CHECKPOINT protocol validates step completion mechanically but not alignment with stakeholder intent. `verify-complete.sh` checks technical gates (CI green, threads resolved) not value constraints. Orchestrator approval for self-edits (`.claude/skills/orchestrate/SKILL.md` changes) reviewed by orchestrator itself creates circular validation risk. No policy adherence testing or value constraint validation observed. Escalation after 3 idle kicks addresses stuck agents but not goal drift. Permission bypass mode (`--permission-mode bypassPermissions`) removes human confirmation checkpoints that could catch misalignment.

**⚠️ Algorithmic Bias** (medium)
> No evidence of explicit bias mitigation in agent spawning or task assignment. `.claude/skills/vercel-react-best-practices/AGENTS.md` indicates guidance 'optimized for automation and consistency' but no demographic fairness checks or testing documented. Agent objectives passed to `spawn-agent.sh` lack input validation per notable_absences, creating risk of encoding unstated assumptions. No fairness metrics, edge-case testing, or bias monitoring observed across agents or worktrees. However, system focuses on code generation tasks rather than human-impacting decisions, limiting immediate harm surface.

**⚠️ Obscure Logic (Black Box)** (medium)
> Partial transparency mechanisms present but significant opacity remains. CHECKPOINT protocol in `.claude/skills/orchestrate/SKILL.md` provides step-level tracking and agents output structured markers, enabling reconstruction of completed steps. State file `~/.claude/orchestrator-state.json` captures agent assignments and session IDs. Git history provides commit-level audit trail. However, notable_absences show 'No audit log of agent actions beyond git history and state file snapshots' and 'No verification that agent code changes align with stated objective before allowing push.' Third-party Claude model reasoning remains opaque. Intermediate decision logic between checkpoints not captured. Session restore via `--resume SESSION_ID` proves conversation persistence but not explainability of reasoning chains.

### Accountability

**❌ Unapproved Self-Improvements** (critical)
> SKILL.md shows orchestrator can use Agent tool with subagent_type general-purpose to draft changes to its own governing scripts (.claude/skills/orchestrate/SKILL.md), reviews diff itself without surfacing to user. No mechanism prevents agents from modifying .claude/skills/ scripts that govern orchestrator behavior - protected worktree rule is procedural, not enforced. No verification that agent code changes align with stated objective before allowing push. Agents run with bypassPermissions and can edit any file in worktree. System allows self-modification of orchestration logic without human approval gates.

**❌ Blurred Accountability Structures** (high)
> No authentication/authorization model for which agents can access which worktrees or PRs. No audit log of agent actions beyond git history and state file snapshots - insufficient for attributing specific decisions. Escalation after 3 idle kicks surfaces stuck agents to human, but no clear ownership documented for automated decisions made before that threshold. verify-complete.sh creates gate requiring manual supervisor evaluation, but orchestrator itself auto-resolves threads and marks PRs done without human confirmation of who owns final approval. State file shows discord_webhook for notifications but no documented escalation protocol or ownership hierarchy.

**⚠️ Memory Rot** (medium)
> System prompt excerpt: 'If your context compacts and you lose track of what to do, run: cat ~/.claude/orchestrator-state.json' indicates acknowledged context window limitations. Agents save session state to disk with --session-id UUID and can resume via claude --resume SESSION_ID, providing recovery mechanism. However, no input validation layer for agent prompts or objectives before passing to spawn-agent.sh allows unfiltered user input into memory. No PII filtering or redaction in state file. State file uses atomic writes (.tmp then mv) to prevent corruption but no documented memory decay, pruning mechanisms, or verification of long-term recall accuracy. No detection of malicious data injection into state file or agent objectives.

### Human Factors

**❌ Over/Under-Reliance & Human Oversight** (critical)
> System exhibits critical over-reliance risks: agents run with --permission-mode bypassPermissions (no confirmation prompts), verify-complete.sh auto-gates completion without requiring human review of quality, orchestrator can approve its own SKILL.md edits via subagent without surfacing to user. No confidence indicators in agent outputs beyond binary CHECKPOINT markers. Absence of 'verification that agent code changes align with stated objective before allowing push' means human sees results only post-facto. System encourages over-trust through automation of critical gates (CI green + checkpoints = done) without calibrated uncertainty flags for ambiguous cases. Manual supervisor evaluation mentioned in safety_mechanisms but undermined by bypass permissions and self-approval workflows.

**❌ Human Misuse** (critical)
> No input validation layer for agent prompts or objectives before spawn-agent.sh execution. No authentication/authorization model controlling which agents access which worktrees/PRs. Agents can execute destructive git operations (force-push, delete branches, rewrite history) with no guardrails. No prevention of agents modifying .claude/skills/ scripts that govern orchestrator behavior (protection is procedural not enforced). No recursion depth limit on Agent tool subagent spawning enables potential misuse cascade. System design assumes benign orchestrator inputs but provides no enforcement of intended use restrictions or policy guardrails on agent objectives.

**⚠️ Human Skill Degradation (Agency & Job Displacement)** (high)
> Orchestrator delegates entire PR lifecycle (code changes, review response, CI fixing, thread resolution) to autonomous agents with minimal human-in-loop touchpoints. verify-complete.sh claims 'Manual supervisor evaluation required' but system mechanics (bypass permissions, automated gates, checkpoint protocol) enable full automation. No adequate change management or skills preservation mechanism - humans monitor state files and escalations rather than participate in decision-making. Escalation after 3 idle kicks is reactive not proactive oversight. Risk of atrophy in code review, debugging, and architectural judgment as agents handle end-to-end workflows. However, human still required for final 'done' marking and handles escalated cases, providing partial oversight.

**⚠️ Undefined or Negative Value** (medium)
> System shows value risks: no cost tracking per workflow run despite spawning multiple Claude agents in parallel tmux sessions. GitHub abuse rate limit handling (sleep 2-3 min on 403) suggests inefficient API orchestration. Serial /pr-test rule to prevent port conflicts indicates resource contention inefficiencies. No latency baseline comparison vs manual PR workflow. Success metrics undefined - verify-complete.sh checks CI green + checkpoints but not code quality, maintainability, or time-to-completion. Excessive coordination overhead visible (poll every 2-3 min, state file management, checkpoint protocol, session restore) but no measurement of net productivity gain. Protected worktrees and state file corruption prevention suggest operational brittleness. However, automation of tedious review-response cycles likely provides value for high-volume PR maintenance if cost-effective.

## Compound Risks

**🔴 Agent Hijacking & Prompt Injection + Blurred Accountability Structures + Obscure Logic (Black Box)** (critical)
> Injected malicious instructions can execute without attribution trail - no audit log captures which agent performed which action, and intermediate reasoning is opaque, making it impossible to detect or forensically analyze hijacking incidents post-facto

**🔴 Silent Failures + Over/Under-Reliance & Human Oversight + Goal Misalignment & Poor Definition** (critical)
> Agents push functionally incorrect code that passes CI checks while humans over-trust the automated verification gates - misaligned implementations go undetected until production because bypassPermissions removes human checkpoints and verify-complete.sh only validates mechanical completion

**🔴 Memory & Data Poisoning + Context Rot + Memory Rot** (critical)
> Corrupted state file entries persist and degrade over time as context compacts - orchestrator relies on poisoned memory to make decisions, with no provenance checking to detect manipulation and no freshness validation to identify stale information

**🔴 Tool Misuse & Confused Deputy + Unapproved Self-Improvements + Human Misuse** (critical)
> Agent modifies orchestration scripts in .claude/skills/ to expand its own permissions, then uses those elevated privileges to access unauthorized worktrees or execute destructive git operations - self-modification creates privilege escalation pathway with no enforcement layer

**🔴 Endless Cycles / Looping + Cascading Errors + System Instability** (critical)
> Runaway recursive agent spawning consumes all system resources while triggering cascading failures across dependent agents - no recursion depth limits or timeout mechanisms prevent resource exhaustion, and lack of inter-agent coordination allows conflicts to amplify

**🟡 Data Leakage / Data Protection Breach + Obscure Logic (Black Box) + Blurred Accountability Structures** (high)
> PII from PR content leaks into unencrypted state file without detection - no filtering layer captures the exposure, opaque agent reasoning hides what data was accessed, and absent audit trails prevent identifying who is accountable for the breach

**🟡 Reasoning-Action Mismatch + Silent Failures + Goal Misalignment & Poor Definition** (high)
> Agents emit CHECKPOINT markers claiming task completion while actual code changes fail functional requirements - mismatch between declared reasoning and executed actions goes undetected because no semantic validation links checkpoints to objective alignment

**🟡 Model Extraction / Evasion Attacks + System Instability + Cascading Errors** (high)
> Adversary exploits --resume SESSION_ID to replay conversations extracting system prompts, then uses extracted patterns to craft evasion inputs that destabilize the orchestrator - cascading failures propagate across all managed PRs as orchestrator loses coherence

**🟡 Human Skill Degradation (Agency & Job Displacement) + Over/Under-Reliance & Human Oversight + Undefined or Negative Value** (high)
> Humans atrophy critical code review and debugging skills while over-trusting automated agents, but system provides negative ROI due to unmeasured API costs and coordination overhead - organizations lose both human capability and economic value

## Top Recommendations

1. Implement multi-layered input validation and sandboxing: Add mandatory validation layer before spawn-agent.sh that sanitizes objectives, enforce least-privilege access controls per agent-worktree pair, and implement filesystem sandboxing to prevent unauthorized script modifications - this addresses 4 critical compound risks involving hijacking, tool misuse, and self-improvement
2. Deploy comprehensive audit and verification infrastructure: Create immutable audit log capturing all agent actions with attribution, implement pre-push semantic verification that validates code changes align with stated objectives, and add reasoning-action coupling checks that verify CHECKPOINT claims match actual work completed - breaks the silent failure and accountability gaps
3. Add recursive safety bounds and human-in-loop gates: Implement hard limits on agent spawning depth, add timeout mechanisms for non-progressing agents, restore human confirmation checkpoints for high-risk operations (destructive git commands, script modifications, PR completion), and surface confidence indicators that calibrate human trust - prevents runaway loops and over-reliance cascades

## Overall Verdict

# 🔴 RED
