from trust_swarm.prompts import build_repo_reader_prompt, build_specialist_prompt, build_holistic_prompt
from trust_swarm.risks import RISKS, DOMAIN_GROUPS


def test_repo_reader_prompt_contains_output_schema():
    prompt = build_repo_reader_prompt()
    assert "tech_stack" in prompt
    assert "notable_absences" in prompt
    assert "safety_mechanisms_observed" in prompt


def test_specialist_prompt_contains_all_domain_risk_names():
    domain_risks = [r for r in RISKS if r["domain"] == "security"]
    prompt = build_specialist_prompt("security", domain_risks)
    for risk in domain_risks:
        assert risk["name"] in prompt


def test_specialist_prompt_contains_verdict_values():
    domain_risks = [r for r in RISKS if r["domain"] == "security"]
    prompt = build_specialist_prompt("security", domain_risks)
    assert "PASS" in prompt
    assert "CONCERN" in prompt
    assert "FAIL" in prompt


def test_holistic_prompt_mentions_compound_risks():
    prompt = build_holistic_prompt()
    assert "compound" in prompt.lower()
    assert "overall_verdict" in prompt
