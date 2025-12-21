"""Tests for base hooks module."""

import sys
from pathlib import Path

import yaml

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pre_commit_template.hook_templates.render import _generate_hooks


def test_generate_base_hooks_minimal():
    """Test basic hook generation with minimal options."""
    result = _generate_hooks("base")

    # Parse as YAML to check structure
    parsed = yaml.safe_load(result)

    # Should be a list with one repo
    assert isinstance(parsed, list)
    assert len(parsed) == 1

    repo = parsed[0]

    # Check that it's a valid repo structure
    assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"
    assert "rev" in repo
    assert repo["rev"].startswith("v")  # Check version format
    assert "hooks" in repo

    # Check that basic hooks are present
    hook_ids = [hook["id"] for hook in repo["hooks"]]
    expected_basic_hooks = [
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-added-large-files",
        "check-merge-conflict",
        "detect-private-key",
        "detect-aws-credentials",
        "no-commit-to-branch",
    ]

    for hook_id in expected_basic_hooks:
        assert hook_id in hook_ids, f"Expected hook {hook_id} not found"


def test_generate_base_hooks_with_yaml():
    """Test hook generation with YAML checking enabled."""
    result = _generate_hooks("base", yaml=True)

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]
    hook_ids = [hook["id"] for hook in repo["hooks"]]

    assert "check-yaml" in hook_ids


def test_generate_base_hooks_with_json():
    """Test hook generation with JSON checking enabled."""
    result = _generate_hooks("base", json=True)

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]
    hook_ids = [hook["id"] for hook in repo["hooks"]]

    assert "check-json" in hook_ids


def test_generate_base_hooks_with_all_options():
    """Test hook generation with all options enabled."""
    result = _generate_hooks(
        "base",
        yaml=True,
        json=True,
        toml=True,
        xml=True,
        case_conflict=True,
        executables=True,
        symlinks=True,
        python=True,
    )

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]
    hook_ids = [hook["id"] for hook in repo["hooks"]]

    # Check conditional hooks are present
    expected_conditional_hooks = [
        "check-yaml",
        "check-json",
        "check-toml",
        "check-xml",
        "check-case-conflict",
        "check-executables-have-shebangs",
        "check-symlinks",
        "check-ast",
        "check-builtin-literals",
        "check-docstring-first",
        "debug-statements",
    ]

    for hook_id in expected_conditional_hooks:
        assert hook_id in hook_ids, f"Expected conditional hook {hook_id} not found"


def test_yaml_indentation():
    """Test that generated YAML has correct indentation."""
    result = _generate_hooks("base", yaml=True, json=True)

    lines = result.split("\n")

    # Check repo line starts at column 0
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

    # Check hook properties are indented 4 spaces
    name_lines = [line for line in lines if "name:" in line and not line.strip().startswith("name:")]
    for name_line in name_lines:
        assert name_line.startswith("    name:")


def test_no_commit_to_branch_args():
    """Test that no-commit-to-branch has correct args."""
    result = _generate_hooks("base")

    parsed = yaml.safe_load(result)
    assert isinstance(parsed, list)
    repo = parsed[0]

    # Find no-commit-to-branch hook
    no_commit_hook = None
    for hook in repo["hooks"]:
        if hook["id"] == "no-commit-to-branch":
            no_commit_hook = hook
            break

    assert no_commit_hook is not None
    assert "args" in no_commit_hook
    assert no_commit_hook["args"] == ["--branch", "main", "--branch", "master"]
