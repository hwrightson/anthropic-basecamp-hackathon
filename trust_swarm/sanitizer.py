"""Sanitise raw repository files before passing them to LLMs.

Two passes:
1. Secret/credential redaction — replaces likely secrets with placeholder tokens.
2. Prompt injection detection — flags files containing adversarial instruction patterns.
"""

import re
import sys

# (pattern, replacement) pairs — matched in order, case-insensitive
_SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"sk-ant-api\d{2}-[A-Za-z0-9_\-]{20,}"), "[REDACTED:ANTHROPIC_KEY]"),
    (re.compile(r"sk-[A-Za-z0-9]{48}"), "[REDACTED:OPENAI_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}"), "[REDACTED:GITHUB_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED:AWS_ACCESS_KEY]"),
    # Generic: key/secret/token/password assignment with a non-trivial value
    (
        re.compile(
            r'(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[=:]\s*["\']?([A-Za-z0-9_/+.!@#$%^&*]{12,})["\']?'
        ),
        r"[REDACTED:CREDENTIAL]",
    ),
]

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions?"),
    re.compile(r"(?i)disregard\s+(?:all\s+)?(?:previous|prior|your)\s+instructions?"),
    re.compile(r"(?i)you\s+are\s+now\s+(?:a|an)\s+\w+"),
    re.compile(r"(?i)override\s+(?:your\s+)?(?:system\s+)?instructions?"),
    re.compile(r"(?i)(?:new\s+)?(?:role|persona|character|mode)\s*:\s*[A-Za-z]"),
    re.compile(r"(?i)\bact\s+as\s+(?:if\s+you\s+(?:are|were)|a\s+)"),
    re.compile(r"(?i)system\s*prompt\s*(?::|=)"),
    re.compile(r"(?i)forget\s+(?:all\s+)?(?:previous|prior|your)\s+(?:context|instructions?)"),
]


def _redact_secrets(text: str) -> tuple[str, int]:
    total = 0
    for pattern, replacement in _SECRET_PATTERNS:
        text, n = pattern.subn(replacement, text)
        total += n
    return text, total


def _detect_injections(text: str) -> list[str]:
    return [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]


def sanitise(files: list[dict]) -> list[dict]:
    """Return sanitised copies of *files*; logs warnings to stderr."""
    cleaned: list[dict] = []
    total_redacted = 0
    flagged_files: list[str] = []

    for f in files:
        content, n = _redact_secrets(f["content"])
        total_redacted += n
        flags = _detect_injections(content)
        if flags:
            flagged_files.append(f["path"])
        cleaned.append({"path": f["path"], "content": content})

    if total_redacted:
        print(
            f"[Trust Swarm] Sanitiser: redacted {total_redacted} potential secret(s)",
            file=sys.stderr,
        )
    if flagged_files:
        print(
            f"[Trust Swarm] Sanitiser: prompt-injection patterns detected in "
            f"{len(flagged_files)} file(s): {', '.join(flagged_files)}",
            file=sys.stderr,
        )

    return cleaned
