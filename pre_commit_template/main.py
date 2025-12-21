"""Interactive main script for pre-commit-template."""

import argparse
import subprocess
from contextlib import nullcontext
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .config import PreCommitConfig
from .discover import discover_config
from .hook_templates import render_config

console = Console()


def display_detected_technologies(detected_config: PreCommitConfig) -> None:
    """Display detected technologies in a nice table."""
    table = Table(title="Detected Technologies")
    table.add_column("Technology", style="cyan")
    table.add_column("Detected", style="green")
    table.add_column("Details", style="dim")

    # Language detections
    if detected_config.python:
        version_info = (
            f"Version: {detected_config.python_version}" if detected_config.python_version else "No version specified"
        )
        table.add_row("Python", "Yes", version_info)

    if detected_config.js:
        details = []
        if detected_config.typescript:
            details.append("TypeScript")
        if detected_config.jsx:
            details.append("JSX/React")
        detail_str = ", ".join(details) if details else "Basic JavaScript"
        table.add_row("JavaScript", "Yes", detail_str)

    if detected_config.go:
        table.add_row("Go", "Yes", "")

    # Infrastructure
    if detected_config.docker:
        table.add_row("Docker", "Yes", "")

    if detected_config.github_actions:
        table.add_row("GitHub Actions", "Yes", "")

    # File types
    file_types = []
    if detected_config.yaml_check:
        file_types.append("YAML")
    if detected_config.json_check:
        file_types.append("JSON")
    if detected_config.toml_check:
        file_types.append("TOML")
    if detected_config.xml_check:
        file_types.append("XML")

    if file_types:
        table.add_row("File Types", "Yes", ", ".join(file_types))

    console.print(table)
    console.print()


def ask_user_preferences(detected_config: PreCommitConfig) -> PreCommitConfig:
    """Ask user for their preferences, using detected config as defaults."""
    console.print(Panel.fit("Configure Pre-commit Hooks", style="bold blue"))
    console.print("We'll ask you a few questions to customize your configuration.")
    console.print("Detected defaults are shown - just press Enter to accept them.\n")

    # Create a copy to modify
    config_dict = detected_config.model_dump()

    # Base hooks section
    console.print("[bold]Basic Hooks[/bold]")

    if detected_config.yaml_check:
        config_dict["yaml_check"] = Confirm.ask("Include YAML syntax checking?", default=detected_config.yaml_check)

    if detected_config.json_check:
        config_dict["json_check"] = Confirm.ask("Include JSON syntax checking?", default=detected_config.json_check)

    if detected_config.toml_check:
        config_dict["toml_check"] = Confirm.ask("Include TOML syntax checking?", default=detected_config.toml_check)

    if detected_config.xml_check:
        config_dict["xml_check"] = Confirm.ask("Include XML syntax checking?", default=detected_config.xml_check)

    # Set additional safety checks to defaults without asking
    config_dict["case_conflict"] = True  # Always enable for cross-platform compatibility
    config_dict["executables"] = True  # Always enable for shell script safety

    console.print()

    # Python section
    if detected_config.python:
        console.print("[bold]Python Hooks[/bold]")
        config_dict["python"] = Confirm.ask("Include Python hooks (Ruff + MyPy)?", default=detected_config.python)

        if config_dict["python"]:
            # Use detected defaults without asking additional questions
            config_dict["python_base"] = detected_config.python_base
            config_dict["uv_lock"] = detected_config.uv_lock
            config_dict["pyrefly_args"] = detected_config.pyrefly_args  # Keep as None for default behavior

        console.print()

    # JavaScript section
    if detected_config.js:
        console.print("[bold]JavaScript/TypeScript Hooks[/bold]")
        config_dict["js"] = Confirm.ask(
            "Include JavaScript/TypeScript hooks (Prettier + ESLint)?",
            default=detected_config.js,
        )

        if config_dict["js"]:
            config_dict["typescript"] = Confirm.ask("Include TypeScript support?", default=detected_config.typescript)

            config_dict["jsx"] = Confirm.ask("Include JSX/React support?", default=detected_config.jsx)

        console.print()

    # Go section
    if detected_config.go:
        console.print("[bold]Go Hooks[/bold]")
        config_dict["go"] = Confirm.ask("Include Go hooks (golangci-lint + formatting)?", default=detected_config.go)

        if config_dict["go"]:
            config_dict["go_critic"] = Confirm.ask("Include go-critic for additional linting?", default=False)

        console.print()

    # Docker section
    if detected_config.docker:
        console.print("[bold]Docker Hooks[/bold]")
        config_dict["docker"] = Confirm.ask("Include Docker hooks?", default=detected_config.docker)

        if config_dict["docker"]:
            config_dict["dockerfile_linting"] = Confirm.ask("Include Dockerfile linting (hadolint)?", default=True)

        console.print()

    # GitHub Actions section
    if detected_config.github_actions:
        console.print("[bold]GitHub Actions Hooks[/bold]")
        config_dict["github_actions"] = Confirm.ask(
            "Include GitHub Actions hooks?", default=detected_config.github_actions
        )

        if config_dict["github_actions"]:
            config_dict["workflow_validation"] = Confirm.ask("Include workflow validation (actionlint)?", default=True)

            config_dict["security_scanning"] = Confirm.ask("Include security scanning for workflows?", default=False)

        console.print()

    # Python version
    if config_dict.get("python", False):
        if detected_config.python_version:
            config_dict["python_version"] = Prompt.ask(
                "Python version for default_language_version",
                default=detected_config.python_version,
            )
        else:
            config_dict["python_version"] = (
                Prompt.ask("Python version for default_language_version (optional)", default="") or None
            )

    # Create new config from the modified dict
    return PreCommitConfig(**config_dict)


def main() -> None:
    """Main function to generate pre-commit configuration."""
    parser = argparse.ArgumentParser(description="Generate pre-commit configuration")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Enable interactive mode for customizing configuration",
    )
    args = parser.parse_args()

    # Detect current project
    current_path = Path.cwd()

    if args.interactive:
        console.print(
            Panel.fit(
                "Pre-commit Starter\n\nGenerate pre-commit configuration for your project",
                style="bold green",
            )
        )
        console.print()
        console.print(f"Analyzing project at: [cyan]{current_path}[/cyan]")
        console.print()

    # Auto-detect configuration
    status_context = console.status("Detecting technologies...") if args.interactive else nullcontext()
    with status_context:
        detected_config = discover_config(current_path)

    if args.interactive:
        # Display detected technologies
        display_detected_technologies(detected_config)

        # Ask if user wants to proceed with detected config or customize
        if Confirm.ask("Would you like to customize the configuration?", default=True):
            final_config = ask_user_preferences(detected_config)
        else:
            final_config = detected_config

        console.print()

        # Generate the configuration
        with console.status("Generating pre-commit configuration..."):
            pre_commit_yaml = render_config(final_config)

        # Output the configuration to stdout
        print(pre_commit_yaml)
    else:
        # Default auto-generate mode
        final_config = detected_config
        pre_commit_yaml = render_config(final_config)

        # Save configuration and run pre-commit
        config_file = current_path / ".pre-commit-config.yaml"
        config_file.write_text(pre_commit_yaml)
        console.print(f"Configuration saved to [green]{config_file}[/green]")

        # Install and run pre-commit
        try:
            subprocess.run(
                ["pre-commit", "install"],
                check=True,
                cwd=current_path,
                capture_output=True,
            )

            result = subprocess.run(
                ["pre-commit", "run", "--all-files"],
                cwd=current_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                console.print("Pre-commit setup complete and all hooks passed!")
            else:
                console.print("Pre-commit setup complete but some hooks failed:")
                console.print(result.stdout)
                if result.stderr:
                    console.print(result.stderr)
        except subprocess.CalledProcessError as e:
            console.print(f"Failed to setup pre-commit: {e}")
        except FileNotFoundError:
            console.print("pre-commit not found in PATH")


if __name__ == "__main__":
    main()
