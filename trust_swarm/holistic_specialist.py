import json
import sys

import anthropic

from trust_swarm.prompts import build_holistic_prompt

HOLISTIC_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "compound_risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "risk_combination": {"type": "array", "items": {"type": "string"}},
                        "emergent_concern": {"type": "string"},
                        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    },
                    "required": ["risk_combination", "emergent_concern", "severity"],
                    "additionalProperties": False,
                },
            },
            "overall_verdict": {"type": "string", "enum": ["GREEN", "AMBER", "RED"]},
            "top_3_recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            },
        },
        "required": ["compound_risks", "overall_verdict", "top_3_recommendations"],
        "additionalProperties": False,
    },
}


def run_holistic_specialist(domain_results: list[dict]) -> dict:
    """Phase 3: review all domain results for compound/emergent risks."""
    print("[Phase 3] Running holistic specialist...", file=sys.stderr)

    client = anthropic.Anthropic()
    user_content = (
        "Here are the domain specialist assessments:\n\n"
        + json.dumps(domain_results, indent=2)
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=build_holistic_prompt(),
        messages=[{"role": "user", "content": user_content}],
        output_config={"format": HOLISTIC_SCHEMA},
    )

    text_blocks = [b for b in response.content if b.type == "text" and b.text.strip()]
    return json.loads(text_blocks[-1].text)
