import asyncio
import json
import sys

import anthropic

from trust_swarm.prompts import build_specialist_prompt
from trust_swarm.risks import RISKS, DOMAIN_GROUPS, DOMAIN_DISPLAY_NAMES

DOMAIN_RESULT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "domain": {"type": "string"},
            "risks_assessed": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "risk": {"type": "string"},
                        "principle": {"type": "string"},
                        "verdict": {"type": "string", "enum": ["PASS", "CONCERN", "FAIL"]},
                        "evidence": {"type": "string"},
                        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["risk", "principle", "verdict", "evidence", "severity", "confidence"],
                    "additionalProperties": False,
                },
            },
            "domain_summary": {"type": "string"},
            "overall_domain_score": {"type": "string", "enum": ["GREEN", "AMBER", "RED"]},
        },
        "required": ["domain", "risks_assessed", "domain_summary", "overall_domain_score"],
        "additionalProperties": False,
    },
}


async def _run_specialist(
    client: anthropic.AsyncAnthropic,
    domain: str,
    domain_risks: list[dict],
    trust_brief: dict,
) -> dict:
    display_name = DOMAIN_DISPLAY_NAMES[domain]
    system_prompt = build_specialist_prompt(domain, domain_risks)
    user_content = f"Here is the trust brief for the repository:\n\n{json.dumps(trust_brief, indent=2)}"

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
        output_config={"format": DOMAIN_RESULT_SCHEMA},
    )

    text_blocks = [b for b in response.content if b.type == "text" and b.text.strip()]
    result = json.loads(text_blocks[-1].text)
    print(f"[Phase 2] {display_name} specialist complete — {result['overall_domain_score']}", file=sys.stderr)
    return result


async def _run_all_specialists(trust_brief: dict) -> list[dict]:
    client = anthropic.AsyncAnthropic(max_retries=3)
    tasks = [
        _run_specialist(
            client,
            domain,
            [r for r in RISKS if r["id"] in risk_ids],
            trust_brief,
        )
        for domain, risk_ids in DOMAIN_GROUPS.items()
    ]
    return await asyncio.gather(*tasks)


def run_domain_specialists(trust_brief: dict) -> list[dict]:
    """Phase 2: run all 5 domain specialists in parallel. Returns list of domain results."""
    print("[Phase 2] Running 5 domain specialists in parallel...", file=sys.stderr)
    return asyncio.run(_run_all_specialists(trust_brief))
