"""Append-only audit log for every analysis run.

Each line is a JSON record. Written to $TRUST_SWARM_AUDIT_LOG (default: audit.log
in the current working directory). Set TRUST_SWARM_AUDIT_LOG='' to disable.
"""

import json
import os
import sys
import time
from pathlib import Path


def _log_path() -> Path | None:
    env = os.getenv("TRUST_SWARM_AUDIT_LOG", "audit.log")
    if not env:
        return None
    return Path(env)


def _write(record: dict) -> None:
    path = _log_path()
    if path is None:
        return
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        print(f"[Trust Swarm] Audit log write failed: {exc}", file=sys.stderr)


def log_analysis_start(repo: str) -> float:
    ts = time.time()
    _write({"event": "analysis_start", "repo": repo, "ts": ts})
    return ts


def log_phase_complete(phase: int, duration_s: float, meta: dict | None = None) -> None:
    record: dict = {"event": f"phase_{phase}_complete", "duration_s": round(duration_s, 2), "ts": time.time()}
    if meta:
        record.update(meta)
    _write(record)


def log_analysis_complete(repo: str, verdict: str, start_ts: float) -> None:
    _write({
        "event": "analysis_complete",
        "repo": repo,
        "verdict": verdict,
        "total_duration_s": round(time.time() - start_ts, 2),
        "ts": time.time(),
    })


def log_error(repo: str, phase: int, error: str) -> None:
    _write({"event": "analysis_error", "repo": repo, "phase": phase, "error": error, "ts": time.time()})
