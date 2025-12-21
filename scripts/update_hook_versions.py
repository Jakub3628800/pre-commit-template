#!/usr/bin/env python3
"""
Automated pre-commit hook version updater for template files.

This script:
1. Creates a temporary directory
2. Extracts current hook revisions from template files
3. Generates a complete .pre-commit-config.yaml from templates
4. Runs pre-commit autoupdate to get latest versions
5. Updates the template files with new versions
6. Reports all changes made
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader
except ImportError as e:
    print(f"ERROR: Missing required dependency: {e}")
    print("Install with: uv pip install pyyaml jinja2")
    sys.exit(1)


class TemplateUpdater:
    """Handles updating pre-commit hook versions in template files."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        self.template_dir = self.repo_root / "pre_commit_template" / "hook_templates"
        self.temp_dir: Optional[Path] = None
        self.original_revisions: Dict[str, str] = {}
        self.updated_hooks: List[Dict[str, str]] = []

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")

    def setup_temp_directory(self) -> Path:
        """Create a temporary directory for the update process."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pre-commit-update-"))

        # Initialize git repo (required by pre-commit)
        try:
            subprocess.run(["git", "init"], cwd=str(self.temp_dir), capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=str(self.temp_dir),
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=str(self.temp_dir),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Failed to initialize git repo: {e}")

        return self.temp_dir

    def cleanup_temp_directory(self):
        """Remove the temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)  # type: ignore[deprecated]

    def extract_original_revisions(self) -> Dict[str, str]:
        """Extract current hook revisions from all template files."""
        revisions = {}

        for template_file in self.template_dir.glob("*.j2"):
            if template_file.name == "meta.j2":
                continue

            content = template_file.read_text()
            # Handles various revision formats: v1.2.3, 1.2.3, v1.2.3-alpha, etc.
            pattern = r"- repo: (https://github\.com/[^\n]+)\n\s+rev: ([^\s\n]+)"
            matches = re.findall(pattern, content)

            for repo_url, rev in matches:
                revisions[repo_url] = rev

        self.original_revisions = revisions
        print(f"Found {len(revisions)} hooks in templates")
        return revisions

    def generate_full_config(self) -> Path:
        """Generate a complete .pre-commit-config.yaml from all templates."""
        assert self.temp_dir is not None, "Temp directory must be set up first"
        output_file = self.temp_dir / ".pre-commit-config.yaml"
        env = Environment(loader=FileSystemLoader(str(self.template_dir)))

        context = {
            "yaml": True,
            "json": True,
            "toml": True,
            "xml": True,
            "case_conflict": True,
            "executables": True,
            "symlinks": True,
            "python": True,
            "dockerfile_linting": True,
            "dockerignore_check": True,
            "workflow_validation": True,
            "security_scanning": True,
            "go_critic": True,
            "typescript": True,
            "jsx": True,
            "prettier_config": ".prettierrc",
            "eslint_config": ".eslintrc.js",
            "pyrefly_args": ["--config=pyproject.toml"],
            "uv_lock": True,
            "python_version": "'3.10'",
        }

        all_content = []
        template_files = sorted(
            [f for f in self.template_dir.glob("*.j2") if f.name != "meta.j2"],
            key=lambda x: x.name,
        )

        for template_file in template_files:
            template = env.get_template(template_file.name)
            content = template.render(context)
            all_content.append(content)  # type: ignore[arg-type]

        combined_content = "\n".join(all_content)
        meta_template = env.get_template("meta.j2")
        final_config = meta_template.render({**context, "content": combined_content})

        output_file.write_text(final_config)
        try:
            with open(output_file) as f:
                config = yaml.safe_load(f)
            if config and isinstance(config, dict):
                repos = config.get("repos", [])
                print(f"Generated config with {len(repos)} repositories")
        except yaml.YAMLError as e:
            print(f"ERROR: Generated invalid YAML: {e}")
            raise

        return output_file

    def run_autoupdate(self) -> tuple[bool, str]:
        """Run pre-commit autoupdate and return success status and stdout."""
        try:
            subprocess.run(["pre-commit", "--version"], capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: pre-commit is not installed or not in PATH")
            print("Install with: pip install pre-commit")
            return False, ""

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ASKPASS"] = "echo"

        all_updates = []

        assert self.temp_dir is not None, "Temp directory must be set up first"

        try:
            with open(self.temp_dir / ".pre-commit-config.yaml") as f:
                config = yaml.safe_load(f)
        except Exception as e:
            print(f"ERROR: Failed to read config: {e}")
            return False, ""

        if config is None or not isinstance(config, dict):
            print("ERROR: Invalid config file")
            return False, ""

        repos = config.get("repos", [])
        print(f"Checking {len(repos)} repositories for updates...")

        for repo in repos:
            repo_url = repo.get("repo")
            if not repo_url:
                continue

            repo_name = repo_url.split("/")[-1]
            print(f"  {repo_name}...", end=" ", flush=True)

            try:
                result = subprocess.run(
                    ["pre-commit", "autoupdate", "--repo", repo_url],
                    cwd=str(self.temp_dir),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env,
                )

                if result.returncode == 0:
                    if "updating" in result.stdout:
                        print("updated")
                        all_updates.append(result.stdout)  # type: ignore[arg-type]
                    else:
                        print("up to date")
                else:
                    print("failed")

            except subprocess.TimeoutExpired:
                print("timeout")
            except Exception as e:
                print(f"error: {e}")

        combined_output = "\n".join(all_updates)

        if not combined_output:
            print("No updates found")
            return True, ""

        return True, combined_output

    def parse_autoupdate_output(self, autoupdate_stdout: str) -> List[Dict[str, str]]:
        """Parse pre-commit autoupdate stdout to extract version changes."""
        updated_hooks = []
        pattern = r"\[(https://github\.com/[^\]]+)\] updating ([^\s]+) -> ([^\s]+)"

        for line in autoupdate_stdout.splitlines():
            match = re.search(pattern, line)
            if match:
                repo_url = match.group(1)
                old_rev = match.group(2)
                new_rev = match.group(3)
                updated_hooks.append({"repo": repo_url, "old_rev": old_rev, "new_rev": new_rev})

        self.updated_hooks = updated_hooks
        return updated_hooks

    def apply_updates_to_templates(self) -> Dict[str, int]:
        """Apply version updates back to the template files."""
        if not self.updated_hooks:
            return {}

        updates_per_file = {}

        for template_file in self.template_dir.glob("*.j2"):
            if template_file.name == "meta.j2":
                continue

            content = template_file.read_text()
            updates_made = 0

            for hook in self.updated_hooks:
                if hook["repo"] in content:
                    old_pattern = f"rev: {hook['old_rev']}"
                    new_pattern = f"rev: {hook['new_rev']}"

                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        updates_made += 1

            if updates_made > 0:
                template_file.write_text(content)
                updates_per_file[template_file.name] = updates_made

        return updates_per_file

    def generate_report(self, updates_per_file: Dict[str, int]):
        """Generate a summary report of all changes."""
        if not self.updated_hooks:
            print("\nAll hook versions are current")
            return

        print(f"\nUpdated {len(self.updated_hooks)} hooks in {len(updates_per_file)} files:")
        for hook in self.updated_hooks:
            repo_name = hook["repo"].split("/")[-1]
            print(f"  {repo_name}: {hook['old_rev']} → {hook['new_rev']}")

    def run(self) -> bool:  # type: ignore[return]
        """Execute the complete update process."""
        try:
            self.setup_temp_directory()
            self.extract_original_revisions()
            self.generate_full_config()

            success, autoupdate_stdout = self.run_autoupdate()
            if not success:
                return False

            self.parse_autoupdate_output(autoupdate_stdout)
            updates_per_file = self.apply_updates_to_templates()
            self.generate_report(updates_per_file)

            return True

        except Exception as e:
            print(f"\nERROR: Update process failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            self.cleanup_temp_directory()


def main():
    """Main entry point."""
    # Allow specifying repo root as argument
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    try:
        updater = TemplateUpdater(repo_root)
        success = updater.run()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
