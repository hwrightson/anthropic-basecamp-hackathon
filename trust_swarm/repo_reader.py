import json
import sys

import anthropic

from trust_swarm.prompts import build_repo_reader_prompt

TRUST_BRIEF_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "repo": {"type": "string"},
            "tech_stack": {"type": "array", "items": {"type": "string"}},
            "agent_architecture": {"type": "string"},
            "key_files_found": {"type": "array", "items": {"type": "string"}},
            "system_prompt_excerpts": {
                "type": "array",
                "items": {"type": "string"},
            },
            "safety_mechanisms_observed": {"type": "array", "items": {"type": "string"}},
            "notable_absences": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "repo", "tech_stack", "agent_architecture", "key_files_found",
            "system_prompt_excerpts", "safety_mechanisms_observed", "notable_absences",
        ],
        "additionalProperties": False,
    },
}


def _format_files(files: list[dict]) -> str:
    blocks = []
    for f in files:
        blocks.append(f"===== FILE: {f['path']} =====\n{f['content']}")
    return "\n\n".join(blocks)


def read_repo(repo_slug: str, files: list[dict]) -> dict:
    """Phase 1: produce a structured trust brief from fetched repo files."""
    print("[Phase 1] Analysing repo with Claude...", file=sys.stderr)

    client = anthropic.Anthropic(max_retries=3)
    user_content = f"Repository: {repo_slug}\n\n{_format_files(files)}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=build_repo_reader_prompt(),
        messages=[{"role": "user", "content": user_content}],
        output_config={"format": TRUST_BRIEF_SCHEMA},
    )

    text_blocks = [b for b in response.content if b.type == "text" and b.text.strip()]
    return json.loads(text_blocks[-1].text)
