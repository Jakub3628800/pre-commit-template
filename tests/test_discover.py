"""Tests for discover module."""

import json
import sys
import tempfile
from pathlib import Path

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pre_commit_template.discover import (
    detect_docker,
    detect_github_actions,
    detect_go,
    detect_javascript,
    detect_json_files,
    detect_jsx,
    detect_project_dependencies,
    detect_python,
    detect_toml_files,
    detect_typescript,
    detect_uv_lock,
    detect_yaml_files,
    discover_config,
    discover_files,
)


def test_discover_files():
    """Test file discovery function."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create some test files
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "README.md").write_text("# Test")

        # Create a subdirectory with files
        sub_dir = tmp_path / "src"
        sub_dir.mkdir()
        (sub_dir / "main.go").write_text("package main")

        files = discover_files(tmp_path)

        assert "test.py" in files
        assert ".py" in files
        assert "package.json" in files
        assert ".json" in files
        assert "readme.md" in files
        assert ".md" in files
        assert "main.go" in files
        assert ".go" in files


def test_detect_python():
    """Test Python project detection."""
    # Test with Python files
    files = {"setup.py", "main.py", ".py"}
    assert detect_python(files)

    # Test with pyproject.toml
    files = {"pyproject.toml", "src/main.py"}
    assert detect_python(files)

    # Test without Python indicators
    files = {"package.json", "main.js"}
    assert not detect_python(files)


def test_detect_uv_lock():
    """Test uv.lock detection."""
    files = {"uv.lock", "pyproject.toml"}
    assert detect_uv_lock(files)

    files = {"requirements.txt", "setup.py"}
    assert not detect_uv_lock(files)


def test_detect_javascript():
    """Test JavaScript project detection."""
    # Test with package.json
    files = {"package.json", "main.js", ".js"}
    assert detect_javascript(files)

    # Test with .js files
    files = {"app.js", ".js", "utils.mjs", ".mjs"}
    assert detect_javascript(files)

    # Test without JS indicators
    files = {"main.py", "setup.py"}
    assert not detect_javascript(files)


def test_detect_typescript():
    """Test TypeScript detection."""
    files = {"tsconfig.json", "main.ts"}
    assert detect_typescript(files)

    files = {".ts", ".tsx", ".d.ts"}
    assert detect_typescript(files)

    files = {"main.js", "package.json"}
    assert not detect_typescript(files)


def test_detect_jsx():
    """Test JSX/React detection."""
    files = {".jsx", ".tsx"}
    assert detect_jsx(files)

    files = {"next.config.js", "package.json"}
    assert detect_jsx(files)

    files = {"main.js", "index.ts"}
    assert not detect_jsx(files)


def test_detect_go():
    """Test Go project detection."""
    files = {"go.mod", "main.go"}
    assert detect_go(files)

    files = {".go", "go.sum"}
    assert detect_go(files)

    files = {"main.py", "package.json"}
    assert not detect_go(files)


def test_detect_docker():
    """Test Docker detection."""
    files = {"dockerfile", "docker-compose.yml"}
    assert detect_docker(files)

    files = {".dockerignore", "dockerfile.dev"}
    assert detect_docker(files)

    files = {"main.py", "package.json"}
    assert not detect_docker(files)


def test_detect_github_actions():
    """Test GitHub Actions detection."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create .github/workflows directory with workflow file
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI")

        files: set[str] = set()  # Not used in this function
        assert detect_github_actions(files, tmp_path)

        # Test without workflows
        tmp_path2 = Path(tmp_dir) / "no_workflows"
        tmp_path2.mkdir()
        assert not detect_github_actions(files, tmp_path2)


def test_detect_file_types():
    """Test various file type detection functions."""
    # YAML files
    files = {".yml", ".yaml", "docker-compose.yml"}
    assert detect_yaml_files(files)

    files = {"main.py", "package.json"}
    assert not detect_yaml_files(files)

    # JSON files
    files = {".json", "package.json"}
    assert detect_json_files(files)

    files = {"main.py", "requirements.txt"}
    assert not detect_json_files(files)

    # TOML files
    files = {".toml", "pyproject.toml"}
    assert detect_toml_files(files)

    files = {"main.py", "package.json"}
    assert not detect_toml_files(files)


def test_discover_config_python_project():
    """Test config discovery for a Python project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create Python project files
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test"
requires-python = ">=3.9"
""")
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("requests>=2.0.0")
        (tmp_path / "uv.lock").write_text("# uv lock file")

        config = discover_config(tmp_path)

        assert config.python
        assert config.python_base
        assert config.uv_lock
        assert config.toml_check  # Because of pyproject.toml
        assert config.python_version == "python3.9"
        assert not config.js
        assert not config.go


def test_discover_config_javascript_project():
    """Test config discovery for a JavaScript project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create JavaScript project files
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "main.js").write_text("console.log('hello')")
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}')
        (tmp_path / "app.tsx").write_text("export const App = () => <div>Hello</div>")
        (tmp_path / ".prettierrc.json").write_text('{"semi": false}')

        config = discover_config(tmp_path)

        assert config.js
        assert config.typescript
        assert config.jsx
        assert config.json_check
        assert config.prettier_config == ".prettierrc.json"
        assert not config.python
        assert not config.go


def test_discover_config_mixed_project():
    """Test config discovery for a mixed technology project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create mixed project files
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "go.mod").write_text("module test")
        (tmp_path / "Dockerfile").write_text("FROM python:3.9")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")

        # Create GitHub Actions
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI")

        config = discover_config(tmp_path)

        assert config.python
        assert config.go
        assert config.docker
        assert config.github_actions
        assert config.yaml_check  # Because of docker-compose.yml
        assert not config.js


def test_discover_config_json_output():
    """Test that discovered config can be serialized to JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create simple Python project
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"')

        config = discover_config(tmp_path)

        # Should be able to serialize to JSON
        config_dict = config.model_dump(by_alias=True)
        json_str = json.dumps(config_dict, indent=2)

        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["python"]
        assert parsed["toml"]


def test_discover_config_empty_directory():
    """Test config discovery in an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        config = discover_config(tmp_path)

        # Should have minimal configuration
        assert not config.python
        assert not config.js
        assert not config.go
        assert not config.docker
        assert not config.github_actions
        assert not config.yaml_check
        assert not config.json_check
        assert not config.toml_check


def test_detect_project_dependencies_pyproject_toml():
    """Test dependency detection from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create pyproject.toml with dependencies
        (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test"
dependencies = [
    "PyYAML>=6.0",
    "requests>=2.25.0",
    "setuptools>=61.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pyrefly>=0.30.0",
    "types-requests",
]
""")

        dependencies = detect_project_dependencies(tmp_path)
        expected = {
            "PyYAML",
            "requests",
            "setuptools",
            "pytest",
            "pyrefly",
            "types-requests",
        }
        assert dependencies == expected


def test_detect_project_dependencies_requirements_txt():
    """Test dependency detection from requirements.txt files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create requirements.txt
        (tmp_path / "requirements.txt").write_text("""
PyYAML==6.0.2
requests>=2.25.0
# This is a comment
setuptools~=61.0
""")

        # Create requirements-dev.txt
        (tmp_path / "requirements-dev.txt").write_text("""
pytest>=7.0
pyrefly>=0.30.0
types-PyYAML
""")

        dependencies = detect_project_dependencies(tmp_path)
        expected = {
            "PyYAML",
            "requests",
            "setuptools",
            "pytest",
            "pyrefly",
            "types-PyYAML",
        }
        assert dependencies == expected


def test_detect_project_dependencies_no_files():
    """Test dependency detection with no dependency files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        dependencies = detect_project_dependencies(tmp_path)
        assert dependencies == set()
