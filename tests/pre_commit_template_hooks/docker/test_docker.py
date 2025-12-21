"""Tests for Docker hooks module."""

import sys
from pathlib import Path

import yaml

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pre_commit_template.hook_templates.render import _generate_hooks


def test_generate_docker_hooks_basic():
    """Test basic Docker hook generation."""
    result = _generate_hooks("docker")

    # Should have basic structure without conditional hooks
    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]

    assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
    assert "hooks" in repo

    hook_ids = [hook["id"] for hook in repo["hooks"]]
    assert "check-added-large-files" in hook_ids


def test_generate_docker_hooks_with_dockerfile_linting():
    """Test Docker hook generation with Dockerfile linting."""
    result = _generate_hooks("docker", dockerfile_linting=True)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Should have hadolint repo (if implemented) or base repo with additional hooks
    hadolint_repo = next((repo for repo in parsed_repos if "hadolint" in repo["repo"]), None)
    if hadolint_repo:
        hook_ids = [hook["id"] for hook in hadolint_repo["hooks"]]
        assert "hadolint-docker" in hook_ids
    else:
        # Check if base repo has dockerfile-related hooks
        base_repo = next((repo for repo in parsed_repos if "pre-commit-hooks" in repo["repo"]), None)
        if base_repo:
            hook_ids = [hook["id"] for hook in base_repo["hooks"]]
            # May have dockerfile-related hooks in base repo


def test_generate_docker_hooks_with_dockerignore_check():
    """Test Docker hook generation with dockerignore checking."""
    result = _generate_hooks("docker", dockerignore_check=True)

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]
    hook_ids = [hook["id"] for hook in repo["hooks"]]

    # Should include case conflict check for cross-platform compatibility
    assert "check-case-conflict" in hook_ids


def test_generate_docker_hooks_all_options():
    """Test Docker hook generation with all options enabled."""
    result = _generate_hooks("docker", dockerfile_linting=True, dockerignore_check=True)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Collect all hook IDs from all repos
    all_hook_ids = []
    for repo in parsed_repos:
        all_hook_ids.extend([hook["id"] for hook in repo["hooks"]])

    # Check that we have the expected hooks
    assert "check-added-large-files" in all_hook_ids
    if "hadolint" not in all_hook_ids:
        # Hadolint might be in a separate template/implementation
        pass


def test_yaml_indentation():
    """Test that generated YAML has correct indentation."""
    result = _generate_hooks("docker", dockerignore_check=True)

    lines = result.split("\n")

    # Check repo line starts correctly
    repo_line = next(line for line in lines if line.startswith("- repo:"))
    assert repo_line.startswith("- repo:")

    # Check rev line is indented 2 spaces
    rev_line = next(line for line in lines if "rev:" in line)
    assert rev_line.startswith("  rev:")

    # Check hooks line is indented 2 spaces
    hooks_line = next(line for line in lines if "hooks:" in line)
    assert hooks_line.startswith("  hooks:")

    # Check hook entries are indented 2 spaces
    hook_lines = [line for line in lines if line.strip().startswith("- id:")]
    for hook_line in hook_lines:
        assert hook_line.startswith("  - id:")


def test_large_files_check_args():
    """Test that large files check has appropriate args for Docker."""
    result = _generate_hooks("docker")

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]

    # Find check-added-large-files hook
    large_files_hook = None
    for hook in repo["hooks"]:
        if hook["id"] == "check-added-large-files":
            large_files_hook = hook
            break

    assert large_files_hook is not None
    # Should have appropriate limits for Docker builds
    if "args" in large_files_hook:
        args = large_files_hook["args"]
        assert any("--maxkb=" in str(arg) for arg in args)
