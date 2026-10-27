"""Tests for the Conventional Commits git hook validator."""

import os
import subprocess
import tempfile
import pytest

HOOK_SCRIPT = os.path.abspath(".githooks/commit-msg")


def run_hook_with_message(message: str) -> int:
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(message)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["python3", HOOK_SCRIPT, tmp_path],
            capture_output=True,
            text=True,
        )
        return result.returncode
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@pytest.mark.parametrize(
    "valid_message",
    [
        "feat: add badge preview generator",
        "feat(ui): add badge preview generator",
        "fix(cache): resolve ttl expiration issue",
        "docs: update readme with quickstart",
        "docs(api): add endpoint reference",
        "style: fix indentation",
        "refactor(github): simplify client logic",
        "perf: optimize svg rendering",
        "test(ui): add home page tests",
        "build(deps): bump httpx",
        "ci(github): add test workflow",
        "chore: clean temporary files",
        "revert: undo previous commit",
        "feat(api)!: breaking change in response structure",
        "Merge branch 'main' of https://github.com/...",
        "Revert \"feat: something\"",
    ],
)
def test_valid_conventional_commit_messages(valid_message):
    assert run_hook_with_message(valid_message) == 0


@pytest.mark.parametrize(
    "invalid_message",
    [
        "added new feature",
        "Fix bug in streak",
        "FEAT: uppercase type not allowed",
        "feat:missing space after colon",
        "random commit message",
        "wip",
        "",
        "# only comments\n# no message",
    ],
)
def test_invalid_conventional_commit_messages(invalid_message):
    assert run_hook_with_message(invalid_message) != 0
