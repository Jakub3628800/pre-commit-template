from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from pre_commit_template.config import PreCommitConfig

# Package version - update this when version changes
__version__ = "0.1.1"

# Initialize Jinja2 environment once at module level
TEMPLATES_DIR = Path(__file__).parent
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _generate_hooks(hook_type: str, **kwargs: Any) -> str:
    template_mapping = {
        "base": "base.j2",
        "python": "python.j2",
        "docker": "docker.j2",
        "js": "js.j2",
        "go": "go.j2",
        "github_actions": "github_actions.j2",
    }

    if hook_type not in template_mapping:
        raise ValueError(f"Unsupported hook type: {hook_type}")

    template = JINJA_ENV.get_template(template_mapping[hook_type])
    return template.render(**kwargs)


def _generate_meta_wrapper(
    content: str,
    python_version: Optional[str] = None,
    technologies: Optional[list[str]] = None,
) -> str:
    template = JINJA_ENV.get_template("meta.j2")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return template.render(
        content=content,
        python_version=python_version,
        version=__version__,
        timestamp=timestamp,
        technologies=technologies or [],
    )


def render_config(config: PreCommitConfig) -> str:
    """Render the complete pre-commit configuration.

    Args:
        config: Pre-commit configuration object

    Returns:
        Complete pre-commit configuration as YAML string with trailing newline
    """
    hooks_content = []

    # Always add base hooks
    base_content = _generate_hooks(
        "base",
        yaml=config.yaml_check,
        json=config.json_check,
        toml=config.toml_check,
        xml=config.xml_check,
        case_conflict=config.case_conflict,
        executables=config.executables,
        symlinks=config.symlinks,
        python=config.python_base,
    )
    hooks_content.append(base_content)

    # Data-driven hook generation
    optional_hooks: list[tuple[str, bool, dict[str, Any]]] = [
        (
            "python",
            config.python,
            {
                "uv_lock": config.uv_lock,
                "pyrefly_args": config.pyrefly_args,
            },
        ),
        (
            "docker",
            config.docker,
            {
                "dockerfile_linting": config.dockerfile_linting,
                "dockerignore_check": config.dockerignore_check,
            },
        ),
        (
            "github_actions",
            config.github_actions,
            {
                "workflow_validation": config.workflow_validation,
                "security_scanning": config.security_scanning,
            },
        ),
        (
            "js",
            config.js,
            {
                "typescript": config.typescript,
                "jsx": config.jsx,
                "prettier_config": config.prettier_config,
                "eslint_config": config.eslint_config,
            },
        ),
        (
            "go",
            config.go,
            {
                "go_critic": config.go_critic,
            },
        ),
    ]

    # Build list of detected technologies
    technologies = []
    for hook_type, enabled, params in optional_hooks:
        if enabled:
            hooks_content.append(_generate_hooks(hook_type, **params))
            # Map internal names to display names
            display_name = hook_type.replace("_", "-")
            technologies.append(display_name)

    combined_content = "\n\n".join(hooks_content)

    result = _generate_meta_wrapper(
        content=combined_content,
        python_version=config.python_version,
        technologies=technologies,
    )
    if not result.endswith("\n"):
        result += "\n"
    return result
