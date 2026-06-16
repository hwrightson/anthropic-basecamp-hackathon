import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from trust_swarm.github_fetcher import fetch
from trust_swarm.repo_reader import read_repo
from trust_swarm.domain_specialists import run_domain_specialists
from trust_swarm.holistic_specialist import run_holistic_specialist
from trust_swarm.report import build_markdown_report, build_json_report


def main() -> None:
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python -m trust_swarm <github_url>", file=sys.stderr)
        sys.exit(1)

    github_url = sys.argv[1]

    print(f"[Trust Swarm] Fetching repo: {github_url}", file=sys.stderr)
    repo_slug, files = fetch(github_url)
    print(f"[Trust Swarm] Fetched {len(files)} files", file=sys.stderr)

    trust_brief = read_repo(repo_slug, files)

    domain_results = run_domain_specialists(trust_brief)

    holistic = run_holistic_specialist(domain_results)

    md_report = build_markdown_report(trust_brief, domain_results, holistic)
    json_report = build_json_report(trust_brief, domain_results, holistic)

    output_path = Path("trust_report.json")
    output_path.write_text(json.dumps(json_report, indent=2))
    print(f"\n[Trust Swarm] JSON report written to {output_path}", file=sys.stderr)

    print("\n" + "=" * 60)
    print(md_report)


if __name__ == "__main__":
    main()
