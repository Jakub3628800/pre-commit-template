"""Configuration model for pre-commit hook generation."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PreCommitConfig(BaseModel):
    """Configuration for pre-commit hook generation."""

    model_config = {"extra": "allow"}

    # Python version for default_language_version
    python_version: Optional[str] = Field(default=None, alias="python_version")

    # Base hooks options
    yaml_check: bool = Field(default=False, alias="yaml")
    json_check: bool = Field(default=False, alias="json")
    toml_check: bool = Field(default=False, alias="toml")
    xml_check: bool = Field(default=False, alias="xml")
    case_conflict: bool = Field(default=False)
    executables: bool = Field(default=False)
    symlinks: bool = Field(default=False)
    python_base: bool = Field(default=False)

    # Python hooks options
    python: bool = Field(default=False)
    uv_lock: bool = Field(default=False)
    pyrefly_args: Optional[list[str]] = Field(default=None)

    # Docker hooks options
    docker: bool = Field(default=False)
    dockerfile_linting: bool = Field(default=True)
    dockerignore_check: bool = Field(default=False)

    # GitHub Actions hooks options
    github_actions: bool = Field(default=False)
    workflow_validation: bool = Field(default=True)
    security_scanning: bool = Field(default=False)

    # JavaScript hooks options
    js: bool = Field(default=False)
    typescript: bool = Field(default=False)
    jsx: bool = Field(default=False)
    prettier_config: Optional[str] = Field(default=None)
    eslint_config: Optional[str] = Field(default=None)

    # Go hooks options
    go: bool = Field(default=False)
    go_critic: bool = Field(default=False)

    @field_validator("python_version")
    @classmethod
    def validate_python_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate Python version format."""
        if v is not None and not v.startswith("python"):
            raise ValueError('Python version must start with "python" (e.g., python3.14)')
        return v
