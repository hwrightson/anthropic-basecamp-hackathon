from unittest.mock import MagicMock, patch
import base64
import pytest
from trust_swarm.github_fetcher import parse_github_url, prioritise_files, fetch_repo_files


def test_parse_github_url_standard():
    owner, repo = parse_github_url("https://github.com/anthropics/anthropic-sdk-python")
    assert owner == "anthropics"
    assert repo == "anthropic-sdk-python"


def test_parse_github_url_with_trailing_slash():
    owner, repo = parse_github_url("https://github.com/org/repo/")
    assert owner == "org"
    assert repo == "repo"


def test_parse_github_url_invalid():
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        parse_github_url("https://notgithub.com/org/repo")


def test_prioritise_files_puts_agent_files_first():
    files = [
        {"path": "tests/test_handler.py", "type": "blob"},
        {"path": "agents/orchestrator.py", "type": "blob"},
        {"path": "README.md", "type": "blob"},
        {"path": "src/utils.py", "type": "blob"},
    ]
    ordered = prioritise_files(files)
    paths = [f["path"] for f in ordered]
    assert paths.index("agents/orchestrator.py") < paths.index("tests/test_handler.py")
    assert paths.index("README.md") < paths.index("tests/test_handler.py")


def test_prioritise_files_excludes_tree_entries():
    files = [
        {"path": "src", "type": "tree"},
        {"path": "src/main.py", "type": "blob"},
    ]
    ordered = prioritise_files(files)
    assert all(f["type"] == "blob" for f in ordered)


def test_fetch_repo_files_returns_path_content_dicts():
    tree_response = MagicMock()
    tree_response.status_code = 200
    tree_response.json.return_value = {
        "tree": [{"path": "README.md", "type": "blob", "size": 100}]
    }

    content_response = MagicMock()
    content_response.status_code = 200
    content_response.json.return_value = {
        "content": base64.b64encode(b"# My Repo").decode(),
        "encoding": "base64",
    }

    with patch("trust_swarm.github_fetcher.httpx.get") as mock_get:
        mock_get.side_effect = [tree_response, content_response]
        result = fetch_repo_files("org", "repo", github_token=None)

    assert len(result) == 1
    assert result[0]["path"] == "README.md"
    assert result[0]["content"] == "# My Repo"
