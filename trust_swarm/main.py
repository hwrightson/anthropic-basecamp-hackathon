import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from trust_swarm.github_fetcher import fetch
from trust_swarm.repo_reader import read_repo
from trust_swarm.domain_specialists import run_domain_specialists
from trust_swarm.holistic_specialist import run_holistic_specialist
from trust_swarm.report import build_markdown_report, build_json_report
from trust_swarm import audit_log

_PROJECT_ROOT = Path(__file__).parent.parent


class _Tee:
    """Write to both a real stream and a file simultaneously."""

    def __init__(self, real_stream, file_path: Path) -> None:
        self._real = real_stream
        self._fh = file_path.open("w", buffering=1, encoding="utf-8")

    def write(self, s: str) -> int:
        self._real.write(s)
        return self._fh.write(s)

    def flush(self) -> None:
        self._real.flush()
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __getattr__(self, name):
        return getattr(self._real, name)


def _out_dir(repo_slug: str) -> Path:
    safe = repo_slug.replace("/", "-").replace("\\", "-")
    d = _PROJECT_ROOT / "outputs" / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def main() -> None:
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python -m trust_swarm <github_url_or_local_path>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    print(f"[Trust Swarm] Fetching repo: {target}", file=sys.stderr)
    repo_slug, files = fetch(target)
    print(f"[Trust Swarm] Fetched {len(files)} files", file=sys.stderr)

    out_dir = _out_dir(repo_slug)

    # Tee all stderr progress lines to progress.log in the output directory
    tee = _Tee(sys.stderr, out_dir / "progress.log")
    sys.stderr = tee

    try:
        start_ts = audit_log.log_analysis_start(repo_slug)

        t0 = time.time()
        trust_brief = read_repo(repo_slug, files)
        audit_log.log_phase_complete(1, time.time() - t0)

        t0 = time.time()
        domain_results = run_domain_specialists(trust_brief)
        audit_log.log_phase_complete(2, time.time() - t0, {
            "domain_scores": {r["domain"]: r["overall_domain_score"] for r in domain_results}
        })

        t0 = time.time()
        holistic = run_holistic_specialist(domain_results)
        audit_log.log_phase_complete(3, time.time() - t0, {"verdict": holistic["overall_verdict"]})

        audit_log.log_analysis_complete(repo_slug, holistic["overall_verdict"], start_ts)

        md_report = build_markdown_report(trust_brief, domain_results, holistic)
        json_report = build_json_report(trust_brief, domain_results, holistic)

        # Always persist all three output files to outputs/<slug>/
        (out_dir / "trust_report.json").write_text(json.dumps(json_report, indent=2))
        (out_dir / "report.md").write_text("\n" + "=" * 60 + "\n" + md_report + "\n")

        # Also write trust_report.json to CWD so the web server subprocess can find it
        Path("trust_report.json").write_text(json.dumps(json_report, indent=2))

        print(f"\n[Trust Swarm] Outputs saved to {out_dir}", file=sys.stderr)

    finally:
        sys.stderr = tee._real
        tee.close()

    print("\n" + "=" * 60)
    print(md_report)


if __name__ == "__main__":
    main()
