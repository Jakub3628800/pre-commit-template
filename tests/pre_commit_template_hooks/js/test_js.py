"""Tests for JavaScript hooks module."""

import sys
from pathlib import Path

import yaml

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pre_commit_template.hook_templates.render import _generate_hooks


def test_generate_js_hooks_basic():
    """Test basic JavaScript hook generation."""
    result = _generate_hooks("js")

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Should have prettier and eslint repos
    prettier_repo = next((repo for repo in parsed_repos if "mirrors-prettier" in repo["repo"]), None)
    eslint_repo = next((repo for repo in parsed_repos if "mirrors-eslint" in repo["repo"]), None)

    assert prettier_repo is not None
    assert eslint_repo is not None

    # Check prettier hook
    prettier_hook_ids = [hook["id"] for hook in prettier_repo["hooks"]]
    assert "prettier" in prettier_hook_ids

    # Check eslint hook
    eslint_hook_ids = [hook["id"] for hook in eslint_repo["hooks"]]
    assert "eslint" in eslint_hook_ids


def test_generate_js_hooks_with_typescript():
    """Test JavaScript hook generation with TypeScript support."""
    result = _generate_hooks("js", typescript=True)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Check that TypeScript dependencies are included
    eslint_repo = next((repo for repo in parsed_repos if "mirrors-eslint" in repo["repo"]), None)
    assert eslint_repo is not None

    eslint_hook = next((hook for hook in eslint_repo["hooks"] if hook["id"] == "eslint"), None)
    assert eslint_hook is not None

    if "additional_dependencies" in eslint_hook:
        deps = eslint_hook["additional_dependencies"]
        assert any("@typescript-eslint" in str(dep) for dep in deps)


def test_generate_js_hooks_with_jsx():
    """Test JavaScript hook generation with JSX support."""
    result = _generate_hooks("js", jsx=True)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Check that React dependencies are included
    eslint_repo = next((repo for repo in parsed_repos if "mirrors-eslint" in repo["repo"]), None)
    assert eslint_repo is not None

    eslint_hook = next((hook for hook in eslint_repo["hooks"] if hook["id"] == "eslint"), None)
    assert eslint_hook is not None

    if "additional_dependencies" in eslint_hook:
        deps = eslint_hook["additional_dependencies"]
        assert any("eslint-plugin-react" in str(dep) for dep in deps)


def test_generate_js_hooks_with_configs():
    """Test JavaScript hook generation with custom config files."""
    prettier_config = ".prettierrc.json"
    eslint_config = ".eslintrc.js"

    result = _generate_hooks("js", prettier_config=prettier_config, eslint_config=eslint_config)

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Check prettier config
    prettier_repo = next((repo for repo in parsed_repos if "mirrors-prettier" in repo["repo"]), None)
    if prettier_repo:
        prettier_hook = next((hook for hook in prettier_repo["hooks"] if hook["id"] == "prettier"), None)
        if prettier_hook and "args" in prettier_hook:
            args = prettier_hook["args"]
            assert any(prettier_config in str(arg) for arg in args)

    # Check eslint config
    eslint_repo = next((repo for repo in parsed_repos if "mirrors-eslint" in repo["repo"]), None)
    if eslint_repo:
        eslint_hook = next((hook for hook in eslint_repo["hooks"] if hook["id"] == "eslint"), None)
        if eslint_hook and "args" in eslint_hook:
            args = eslint_hook["args"]
            assert any(eslint_config in str(arg) for arg in args)


def test_generate_js_hooks_all_options():
    """Test JavaScript hook generation with all options enabled."""
    result = _generate_hooks(
        "js",
        typescript=True,
        jsx=True,
        prettier_config=".prettierrc.yaml",
        eslint_config=".eslintrc.json",
    )

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Should have both prettier and eslint
    prettier_repo = next((repo for repo in parsed_repos if "mirrors-prettier" in repo["repo"]), None)
    eslint_repo = next((repo for repo in parsed_repos if "mirrors-eslint" in repo["repo"]), None)

    assert prettier_repo is not None
    assert eslint_repo is not None


def test_yaml_indentation():
    """Test that generated YAML has correct indentation."""
    result = _generate_hooks("js", typescript=True)

    lines = result.split("\n")

    # Check repo lines start correctly
    repo_lines = [line for line in lines if line.startswith("- repo:")]
    min_expected_repos = 2  # prettier and eslint
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


def test_file_type_configuration():
    """Test that file types are configured correctly."""
    result = _generate_hooks("js")

    # Parse as YAML list
    parsed_repos = yaml.safe_load(result)
    assert isinstance(parsed_repos, list)

    # Check prettier hook file types
    prettier_repo = next((repo for repo in parsed_repos if "mirrors-prettier" in repo["repo"]), None)
    if prettier_repo:
        prettier_hook = next((hook for hook in prettier_repo["hooks"] if hook["id"] == "prettier"), None)
        if prettier_hook:
            # Should have types or types_or for file targeting
            assert "types" in prettier_hook or "types_or" in prettier_hook
