import pytest


@pytest.fixture
def sample_trust_brief():
    return {
        "repo": "org/repo",
        "tech_stack": ["Python", "Claude API"],
        "agent_architecture": "coordinator + 2 specialists",
        "key_files_found": ["agents/orchestrator.py", "config.yaml"],
        "system_prompt_excerpts": {"coordinator": "You are a coordinator..."},
        "safety_mechanisms_observed": ["input validation in handler.py"],
        "notable_absences": ["no rate limiting found"],
    }


@pytest.fixture
def sample_domain_result():
    return {
        "domain": "Security",
        "risks_assessed": [
            {
                "risk": "Agent Hijacking & Prompt Injection",
                "principle": "Security / Invulnerable",
                "verdict": "CONCERN",
                "evidence": "No input sanitisation found in orchestrator.py.",
                "severity": "high",
            }
        ],
        "domain_summary": "One high-severity gap found.",
        "overall_domain_score": "AMBER",
    }


@pytest.fixture
def sample_holistic_result():
    return {
        "compound_risks": [
            {
                "risk_combination": ["Prompt Injection", "Blurred Accountability"],
                "emergent_concern": "Injected instructions could act without audit trail.",
                "severity": "critical",
            }
        ],
        "overall_verdict": "AMBER",
        "top_3_recommendations": ["Add input sanitisation", "Enable audit logging", "Add rate limiting"],
    }
