"""Discovery script for detecting project technologies and generating config."""

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Optional

# Try to import TOML library (tomllib for Python 3.11+, tomli as fallback)
try:
    import tomllib as toml_lib
except ImportError:
    try:
        import tomli as toml_lib
    except ImportError:
        toml_lib = None  # type: ignore[assignment]

from .config import PreCommitConfig

# Constants for ignored directories and files
ALWAYS_IGNORED_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__"}

DEFAULT_GITIGNORE_PATTERNS = {
    "__pycache__/",
    "node_modules/",
    ".venv/",
    "venv/",
    "env/",
    "build/",
    "dist/",
    ".pytest_cache/",
    ".pyrefly_cache/",
    ".ruff_cache/",
}

# Technology detection indicators
PYTHON_INDICATORS = {
    "setup.py",
    "pyproject.toml",
    "requirements.txt",
    "pipfile",
    "poetry.lock",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    ".py",
    "manage.py",
    "__init__.py",
}

JAVASCRIPT_INDICATORS = {
    "package.json",
    "yarn.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    ".js",
    ".mjs",
    ".cjs",
    "webpack.config.js",
    "vite.config.js",
    "rollup.config.js",
    "babel.config.js",
    ".babelrc",
}

TYPESCRIPT_INDICATORS = {
    "tsconfig.json",
    "tsconfig.base.json",
    "tsconfig.build.json",
    ".ts",
    ".tsx",
    ".d.ts",
}

JSX_INDICATORS = {
    ".jsx",
    ".tsx",
    "next.config.js",
    "gatsby-config.js",
    "react-scripts",
    ".storybook",
}

GO_INDICATORS = {"go.mod", "go.sum", "main.go", ".go", "vendor"}

DOCKER_INDICATORS = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".dockerignore",
    "dockerfile.dev",
    "dockerfile.prod",
}

YAML_FILE_INDICATORS = {".yml", ".yaml", "docker-compose.yml", "docker-compose.yaml"}
JSON_FILE_INDICATORS = {".json"}
TOML_FILE_INDICATORS = {".toml", "pyproject.toml"}
XML_FILE_INDICATORS = {".xml"}


def extract_package_name(dep: str) -> str:
    """Extract package name from dependency string (removes version specifiers)."""
    return re.split(r"[>=~<]", dep)[0].strip()


def _read_pyproject_dependencies(pyproject_file: Path) -> set[str]:
    """Read dependencies from pyproject.toml file.

    Args:
        pyproject_file: Path to pyproject.toml

    Returns:
        Set of package names found in the file
    """
    dependencies = set()
    if not pyproject_file.exists() or not toml_lib:
        return dependencies

    try:
        with open(pyproject_file, "rb") as f:
            data = toml_lib.load(f)

        # Get dependencies from project.dependencies
        if "project" in data and "dependencies" in data["project"]:
            for dep in data["project"]["dependencies"]:
                dependencies.add(extract_package_name(dep))

        # Get dev dependencies
        if "project" in data and "optional-dependencies" in data["project"]:
            for group in data["project"]["optional-dependencies"].values():
                for dep in group:
                    dependencies.add(extract_package_name(dep))

    except (OSError, ValueError, KeyError):
        # OSError: file reading issues
        # ValueError: TOML parsing errors
        # KeyError: unexpected structure
        pass

    return dependencies


def _read_requirements_file(req_path: Path) -> set[str]:
    """Read dependencies from a requirements.txt file.

    Args:
        req_path: Path to requirements file

    Returns:
        Set of package names found in the file
    """
    dependencies = set()
    if not req_path.exists():
        return dependencies

    try:
        with open(req_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    dependencies.add(extract_package_name(line))
    except (OSError, UnicodeDecodeError):
        # OSError: file reading issues
        # UnicodeDecodeError: binary files or encoding issues
        pass

    return dependencies


def detect_project_dependencies(path: Path) -> set[str]:
    """Detect project dependencies from pyproject.toml, requirements.txt, etc.

    Args:
        path: Path to project directory

    Returns:
        Set of all detected package names
    """
    dependencies = set()

    # Check pyproject.toml
    dependencies.update(_read_pyproject_dependencies(path / "pyproject.toml"))

    # Check requirements.txt files
    for req_file in ["requirements.txt", "requirements-dev.txt", "dev-requirements.txt"]:
        dependencies.update(_read_requirements_file(path / req_file))

    return dependencies


def read_gitignore_patterns(path: Path) -> set[str]:
    """Read .gitignore file and return patterns."""
    gitignore_file = path / ".gitignore"
    patterns = set()

    if gitignore_file.exists():
        try:
            with open(gitignore_file, encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.add(line)
        except (OSError, UnicodeDecodeError):
            # If we can't read gitignore, continue without it
            # OSError: file reading issues
            # UnicodeDecodeError: binary or encoding issues
            pass

    return patterns


def is_ignored_by_gitignore(file_path: Path, project_root: Path, gitignore_patterns: set[str]) -> bool:
    """Check if a file should be ignored based on gitignore patterns."""
    try:
        # Get relative path from project root
        rel_path = file_path.relative_to(project_root)
        rel_path_str = str(rel_path)

        # Check if file is in any parent directory that should be ignored
        for part in rel_path.parts:
            if part in ALWAYS_IGNORED_DIRS:
                return True

        for pattern in gitignore_patterns:
            # Handle directory patterns (ending with /)
            if pattern.endswith("/"):
                if fnmatch.fnmatch(rel_path_str + "/", pattern) or fnmatch.fnmatch(rel_path_str, pattern[:-1]):
                    return True
            # Handle file patterns
            elif fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return True

        return False
    except ValueError:
        # File is not relative to project root
        return False


def discover_files(path: Path) -> set[str]:
    """Discover all files in the given path (recursive), respecting .gitignore."""
    files = set()

    # Read gitignore patterns
    gitignore_patterns = read_gitignore_patterns(path)

    # Always exclude .git directory regardless of gitignore
    gitignore_patterns.add(".git/")
    gitignore_patterns.add(".git")

    # Add some basic patterns if no gitignore exists
    if len(gitignore_patterns) <= 2:  # Only .git patterns added
        gitignore_patterns.update(DEFAULT_GITIGNORE_PATTERNS)

    for file_path in path.rglob("*"):
        if file_path.is_file():
            # Skip if ignored by gitignore patterns
            if not is_ignored_by_gitignore(file_path, path, gitignore_patterns):
                files.add(file_path.name.lower())
                # Also add file extensions
                if file_path.suffix:
                    files.add(file_path.suffix.lower())

    return files


def detect_python(files: set[str]) -> bool:
    """Detect if this is a Python project."""
    return bool(PYTHON_INDICATORS & files)


def detect_uv_lock(files: set[str]) -> bool:
    """Detect if project uses uv with uv.lock file."""
    return "uv.lock" in files


def detect_javascript(files: set[str]) -> bool:
    """Detect if this is a JavaScript project."""
    return bool(JAVASCRIPT_INDICATORS & files)


def detect_typescript(files: set[str]) -> bool:
    """Detect if project uses TypeScript."""
    return bool(TYPESCRIPT_INDICATORS & files)


def detect_jsx(files: set[str]) -> bool:
    """Detect if project uses JSX/React."""
    return bool(JSX_INDICATORS & files)


def detect_go(files: set[str]) -> bool:
    """Detect if this is a Go project."""
    return bool(GO_INDICATORS & files)


def detect_docker(files: set[str]) -> bool:
    """Detect if project uses Docker."""
    return bool(DOCKER_INDICATORS & files)


def detect_github_actions(files: set[str], path: Path) -> bool:
    """Detect if project uses GitHub Actions."""
    # Check for .github/workflows directory
    github_workflows = path / ".github" / "workflows"
    if github_workflows.exists() and github_workflows.is_dir():
        workflow_files = list(github_workflows.glob("*.yml")) + list(github_workflows.glob("*.yaml"))
        return len(workflow_files) > 0
    return False


def has_file_type(files: set[str], indicators: set[str]) -> bool:
    """Check if project has files matching any of the given indicators."""
    return bool(indicators & files)


def detect_yaml_files(files: set[str]) -> bool:
    """Detect if project has YAML files."""
    return has_file_type(files, YAML_FILE_INDICATORS)


def detect_json_files(files: set[str]) -> bool:
    """Detect if project has JSON files."""
    return has_file_type(files, JSON_FILE_INDICATORS)


def detect_toml_files(files: set[str]) -> bool:
    """Detect if project has TOML files."""
    return has_file_type(files, TOML_FILE_INDICATORS)


def detect_xml_files(files: set[str]) -> bool:
    """Detect if project has XML files."""
    return has_file_type(files, XML_FILE_INDICATORS)


def detect_python_version(path: Path) -> Optional[str]:
    """Attempt to detect Python version from project files."""
    # Check pyproject.toml
    pyproject_file = path / "pyproject.toml"
    if pyproject_file.exists() and toml_lib:
        try:
            with open(pyproject_file, "rb") as f:
                data = toml_lib.load(f)

            # Check requires-python
            project = data.get("project", {})
            requires_python = project.get("requires-python")
            if requires_python and isinstance(requires_python, str):
                # Extract version like ">=3.14" -> "python3.14"
                if ">=" in requires_python:
                    version = requires_python.split(">=")[1].strip()
                    return f"python{version}"
        except (OSError, ValueError, KeyError):
            # OSError: file reading issues
            # ValueError: TOML parsing errors
            # KeyError: unexpected structure
            pass

    # Check .python-version file
    python_version_file = path / ".python-version"
    if python_version_file.exists():
        try:
            version = python_version_file.read_text().strip()
            if version and not version.startswith("python"):
                return f"python{version}"
            return version if version else None
        except (OSError, UnicodeDecodeError):
            # OSError: file reading issues
            # UnicodeDecodeError: binary or encoding issues
            pass

    return None


def find_config_file(files: set[str], configs: list[str]) -> Optional[str]:
    """Find the first matching config file from a list."""
    for config in configs:
        if config.lower() in files:
            return config
    return None


def find_config_files(path: Path, files: set[str]) -> dict:
    """Find configuration files for various tools."""
    config_files = {}

    # Prettier configs
    prettier_config = find_config_file(
        files,
        [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.yml",
            ".prettierrc.yaml",
            ".prettierrc.js",
            "prettier.config.js",
        ],
    )
    if prettier_config:
        config_files["prettier_config"] = prettier_config

    # ESLint configs
    eslint_config = find_config_file(
        files,
        [
            ".eslintrc",
            ".eslintrc.json",
            ".eslintrc.yml",
            ".eslintrc.yaml",
            ".eslintrc.js",
            "eslint.config.js",
        ],
    )
    if eslint_config:
        config_files["eslint_config"] = eslint_config

    return config_files


def discover_config(path: Path) -> PreCommitConfig:
    """Discover project configuration by analyzing files."""
    files = discover_files(path)

    # Detect technologies
    has_python = detect_python(files)
    has_js = detect_javascript(files)
    has_typescript = detect_typescript(files)
    has_jsx = detect_jsx(files)
    has_go = detect_go(files)
    has_docker = detect_docker(files)
    has_github_actions = detect_github_actions(files, path)

    # Detect file types
    has_yaml = detect_yaml_files(files)
    has_json = detect_json_files(files)
    has_toml = detect_toml_files(files)
    has_xml = detect_xml_files(files)

    # Detect Python version
    python_version = detect_python_version(path) if has_python else None

    # Find config files
    config_files = find_config_files(path, files)

    # Build configuration
    config = PreCommitConfig(
        python_version=python_version,
        yaml=has_yaml,
        json=has_json,
        toml=has_toml,
        xml=has_xml,
        case_conflict=True,  # Always enable for cross-platform compatibility
        executables=True,  # Always enable for shell script safety
        python=has_python,
        python_base=has_python,  # Include Python base checks if Python detected
        uv_lock=detect_uv_lock(files),  # Use uv lock if uv.lock file exists
        js=has_js,
        typescript=has_typescript,
        jsx=has_jsx,
        go=has_go,
        docker=has_docker,
        github_actions=has_github_actions,
        **config_files,
    )

    return config


def main() -> None:
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(description="Discover project technologies and generate config")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Path to analyze (default: current directory)",
    )
    parser.add_argument(
        "--output",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    # Discover configuration
    config = discover_config(args.path)

    if args.output == "json":
        # Output as JSON
        config_dict = config.model_dump(by_alias=True)
        print(json.dumps(config_dict, indent=2))
    else:
        # Output as YAML (for future use)
        import yaml

        config_dict = config.model_dump(by_alias=True)
        print(yaml.dump(config_dict, default_flow_style=False))


if __name__ == "__main__":
    main()
