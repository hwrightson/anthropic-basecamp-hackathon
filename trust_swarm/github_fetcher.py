import base64
import os
from urllib.parse import urlparse, quote

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
    try:
        tree_resp = httpx.get(tree_url, headers=headers, timeout=30)
        tree_resp.raise_for_status()
    except httpx.RequestError as exc:
        raise ValueError(f"Failed to fetch repo tree: {exc}") from exc

    entries = prioritise_files(tree_resp.json().get("tree", []))[:MAX_FILES]

    files: list[dict] = []
    total_bytes = 0

    for entry in entries:
        if total_bytes >= MAX_TOTAL_BYTES:
            break
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{quote(entry['path'], safe='/')}"
        try:
            resp = httpx.get(content_url, headers=headers, timeout=30)
        except httpx.RequestError:
            continue
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
        if total_bytes > MAX_TOTAL_BYTES:
            break
        files.append({"path": entry["path"], "content": text})

    return files


def fetch_local(path: str) -> tuple[str, list[dict]]:
    """Fetch prioritised files from a local directory. Returns (repo_slug, files)."""
    from pathlib import Path
    root = Path(path).resolve()
    repo_name = root.name

    all_entries = []
    for p in root.rglob("*"):
        if p.is_file() and any(p.suffix.lower() == ext for ext in ALLOWED_EXTENSIONS):
            rel = str(p.relative_to(root))
            # Skip hidden dirs and common noise
            parts = rel.split("/")
            if any(part.startswith(".") for part in parts):
                continue
            if any(part in ("node_modules", "__pycache__", ".git", "venv", ".venv") for part in parts):
                continue
            all_entries.append({"type": "blob", "path": rel})

    prioritised = prioritise_files(all_entries)[:MAX_FILES]

    files: list[dict] = []
    total_bytes = 0
    for entry in prioritised:
        if total_bytes >= MAX_TOTAL_BYTES:
            break
        try:
            text = (root / entry["path"]).read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        total_bytes += len(text.encode())
        if total_bytes > MAX_TOTAL_BYTES:
            break
        files.append({"path": entry["path"], "content": text})

    return repo_name, files


def fetch(github_url: str) -> tuple[str, list[dict]]:
    """Top-level entry: parse URL or local path, fetch files. Returns (repo_slug, files)."""
    import os as _os
    from trust_swarm.sanitizer import sanitise
    if _os.path.isdir(github_url):
        slug, files = fetch_local(github_url)
    else:
        owner, repo = parse_github_url(github_url)
        token = os.getenv("GITHUB_TOKEN")
        files = fetch_repo_files(owner, repo, github_token=token)
        slug = f"{owner}/{repo}"
    return slug, sanitise(files)
