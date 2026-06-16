import base64
import os
from urllib.parse import urlparse

import httpx

PRIORITY_PATTERNS = (
    "agent", "prompt", "system", "iam", "policy",
    "config", "handler", "orchestrat", "readme",
)
ALLOWED_EXTENSIONS = (".py", ".yaml", ".yml", ".json", ".md", ".txt")
MAX_FILES = 50
MAX_TOTAL_BYTES = 100_000


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) from a GitHub URL."""
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        raise ValueError(f"Invalid GitHub URL: {url}")
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")
    return parts[0], parts[1]


def prioritise_files(tree_entries: list[dict]) -> list[dict]:
    """Filter to blobs with allowed extensions; high-priority files first."""
    blobs = [
        e for e in tree_entries
        if e.get("type") == "blob"
        and any(e["path"].lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)
    ]

    def priority(entry: dict) -> tuple[int, int]:
        path_lower = entry["path"].lower()
        parts = path_lower.split("/")
        is_test_dir = parts[0] in ("tests", "test")
        matches_pattern = any(pat in path_lower for pat in PRIORITY_PATTERNS)
        if matches_pattern and not is_test_dir:
            return (0, 0)
        if is_test_dir:
            return (1, 1)
        return (1, 0)

    return sorted(blobs, key=priority)


def fetch_repo_files(owner: str, repo: str, github_token: str | None = None) -> list[dict]:
    """Fetch prioritised file contents from a GitHub repo via the REST API."""
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    tree_resp = httpx.get(tree_url, headers=headers, timeout=30)
    tree_resp.raise_for_status()

    entries = prioritise_files(tree_resp.json().get("tree", []))[:MAX_FILES]

    files: list[dict] = []
    total_bytes = 0

    for entry in entries:
        if total_bytes >= MAX_TOTAL_BYTES:
            break
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{entry['path']}"
        resp = httpx.get(content_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            continue
        data = resp.json()
        if data.get("encoding") != "base64":
            continue
        try:
            text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            continue
        total_bytes += len(text.encode())
        files.append({"path": entry["path"], "content": text})

    return files


def fetch(github_url: str) -> tuple[str, list[dict]]:
    """Top-level entry: parse URL, fetch files. Returns (repo_slug, files)."""
    owner, repo = parse_github_url(github_url)
    token = os.getenv("GITHUB_TOKEN")
    files = fetch_repo_files(owner, repo, github_token=token)
    return f"{owner}/{repo}", files
