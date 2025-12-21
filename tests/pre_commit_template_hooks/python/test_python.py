"""Tests for Python hooks module."""

import sys
from pathlib import Path

import yaml

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pre_commit_template.hook_templates.render import _generate_hooks


def test_generate_python_hooks_basic():
    """Test basic Python hook generation."""
    result = _generate_hooks("python")

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Should have ruff and pyrefly repos
    min_expected_repos = 2  # ruff and pyrefly
    assert len(parsed_repos) >= min_expected_repos

    # Check ruff repo
    ruff_repo = next((repo for repo in parsed_repos if "ruff-pre-commit" in repo["repo"]), None)
    assert ruff_repo is not None
    assert ruff_repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"
    assert "rev" in ruff_repo
    assert ruff_repo["rev"].startswith("v")  # Check version format

    ruff_hook_ids = [hook["id"] for hook in ruff_repo["hooks"]]
    assert "ruff-format" in ruff_hook_ids
    assert "ruff" in ruff_hook_ids

    # Check pyrefly repo
    pyrefly_repo = next((repo for repo in parsed_repos if "pyrefly-pre-commit" in repo["repo"]), None)
    assert pyrefly_repo is not None
    assert pyrefly_repo["repo"] == "https://github.com/facebook/pyrefly-pre-commit"

    pyrefly_hook_ids = [hook["id"] for hook in pyrefly_repo["hooks"]]
    assert "pyrefly-typecheck-specific-version" in pyrefly_hook_ids


def test_generate_python_hooks_with_uv_lock():
    """Test Python hook generation with uv.lock checking."""
    result = _generate_hooks("python", uv_lock=True)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Should have uv repo
    uv_repo = next((repo for repo in parsed_repos if "uv-pre-commit" in repo["repo"]), None)
    assert uv_repo is not None
    assert uv_repo["repo"] == "https://github.com/astral-sh/uv-pre-commit"

    uv_hook_ids = [hook["id"] for hook in uv_repo["hooks"]]
    assert "uv-lock" in uv_hook_ids


def test_generate_python_hooks_with_pyrefly_args():
    """Test Python hook generation with Pyrefly arguments."""
    pyrefly_args = ["--strict", "--ignore-missing-imports"]
    result = _generate_hooks("python", pyrefly_args=pyrefly_args)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Find pyrefly repo and hook
    pyrefly_repo = next((repo for repo in parsed_repos if "pyrefly-pre-commit" in repo["repo"]), None)
    assert pyrefly_repo is not None

    pyrefly_hook = next(
        (hook for hook in pyrefly_repo["hooks"] if hook["id"] == "pyrefly-typecheck-specific-version"),
        None,
    )
    assert pyrefly_hook is not None
    assert "args" in pyrefly_hook
    assert pyrefly_hook["args"] == pyrefly_args


def test_yaml_structure_and_indentation():
    """Test that generated YAML has correct structure and indentation."""
    result = _generate_hooks("python", uv_lock=True)

    lines = result.split("\n")

    # Check repo lines start correctly
    repo_lines = [line for line in lines if line.startswith("- repo:")]
    min_expected_repos = 2  # At least ruff and pyrefly
    assert len(repo_lines) >= min_expected_repos

    # Check rev lines are properly indented
    rev_lines = [line for line in lines if "rev:" in line]
    for rev_line in rev_lines:
        assert rev_line.startswith("  rev:")

    # Check hooks lines are properly indented
    hooks_lines = [line for line in lines if "hooks:" in line]
    for hooks_line in hooks_lines:
        assert hooks_line.startswith("  hooks:")

    # Check hook entries are properly indented
    hook_id_lines = [line for line in lines if line.strip().startswith("- id:")]
    for hook_line in hook_id_lines:
        assert hook_line.startswith("  - id:")


def test_ruff_hook_args():
    """Test that ruff hook has correct args."""
    result = _generate_hooks("python")

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    ruff_repo = next((repo for repo in parsed_repos if "ruff-pre-commit" in repo["repo"]), None)
    assert ruff_repo is not None

    # Find ruff linter hook (not formatter)
    ruff_hook = next((hook for hook in ruff_repo["hooks"] if hook["id"] == "ruff"), None)
    assert ruff_hook is not None
    assert "args" in ruff_hook
    assert ruff_hook["args"] == ["--line-length=120"]
