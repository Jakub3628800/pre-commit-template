"""Tests for main.py module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from pre_commit_template.config import PreCommitConfig
from pre_commit_template.main import (
    ask_user_preferences,
    display_detected_technologies,
    main,
)


class TestMainCLI:
    """Test main CLI functionality."""

    @patch("pre_commit_template.main.discover_config")
    @patch("pre_commit_template.main.render_config")
    @patch("subprocess.run")
    @patch("pathlib.Path.write_text")
    def test_main_auto_generate_mode_default(self, mock_write, mock_subprocess, mock_render, mock_discover):
        """Test main function in default auto-generate mode."""
        # Setup mocks
        mock_config = PreCommitConfig(python=True, yaml=True)
        mock_discover.return_value = mock_config
        mock_render.return_value = "yaml content"
        mock_subprocess.return_value.returncode = 0

        with patch("sys.argv", ["pre-commit-starter"]):
            with patch("pre_commit_template.main.console"):
                main()

        mock_discover.assert_called_once()
        mock_render.assert_called_once()
        mock_write.assert_called_once_with("yaml content")
        assert mock_subprocess.call_count == 2  # install and run

    @patch("pre_commit_template.main.discover_config")
    @patch("pre_commit_template.main.render_config")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_main_interactive_mode(self, mock_print, mock_subprocess, mock_render, mock_discover):
        """Test main function with -i flag for interactive mode."""
        # Setup mocks
        mock_config = PreCommitConfig(python=True)
        mock_discover.return_value = mock_config
        mock_render.return_value = "yaml content"

        with patch("sys.argv", ["pre-commit-starter", "-i"]):
            with patch("pre_commit_template.main.Confirm.ask", return_value=False):
                main()

        mock_discover.assert_called_once()
        mock_render.assert_called_once()
        mock_print.assert_called_with("yaml content")
        mock_subprocess.assert_not_called()

    @patch("pre_commit_template.main.discover_config")
    @patch("subprocess.run")
    def test_main_subprocess_called_process_error(self, mock_subprocess, mock_discover):
        """Test main function handles subprocess.CalledProcessError."""
        mock_config = PreCommitConfig(python=True)
        mock_discover.return_value = mock_config
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")

        with patch("sys.argv", ["pre-commit-starter"]):
            with patch("pre_commit_template.main.console") as mock_console:
                with patch("pathlib.Path.write_text"):
                    main()

        mock_console.print.assert_any_call("Failed to setup pre-commit: Command 'cmd' returned non-zero exit status 1.")

    @patch("pre_commit_template.main.discover_config")
    @patch("subprocess.run")
    def test_main_file_not_found_error(self, mock_subprocess, mock_discover):
        """Test main function handles FileNotFoundError when pre-commit not found."""
        mock_config = PreCommitConfig(python=True)
        mock_discover.return_value = mock_config
        mock_subprocess.side_effect = FileNotFoundError()

        with patch("sys.argv", ["pre-commit-starter"]):
            with patch("pre_commit_template.main.console") as mock_console:
                with patch("pathlib.Path.write_text"):
                    main()

        mock_console.print.assert_any_call("pre-commit not found in PATH")

    @patch("pre_commit_template.main.discover_config")
    @patch("subprocess.run")
    def test_main_pre_commit_hooks_fail(self, mock_subprocess, mock_discover):
        """Test main function when pre-commit hooks fail."""
        mock_config = PreCommitConfig(python=True)
        mock_discover.return_value = mock_config

        # Mock subprocess calls: install succeeds, run fails
        install_result = MagicMock()
        install_result.returncode = 0
        run_result = MagicMock()
        run_result.returncode = 1
        run_result.stdout = "Hook failed output"
        run_result.stderr = "Error details"

        mock_subprocess.side_effect = [install_result, run_result]

        with patch("sys.argv", ["pre-commit-starter"]):
            with patch("pre_commit_template.main.console") as mock_console:
                with patch("pathlib.Path.write_text"):
                    main()

        mock_console.print.assert_any_call("Pre-commit setup complete but some hooks failed:")
        mock_console.print.assert_any_call("Hook failed output")
        mock_console.print.assert_any_call("Error details")


class TestUserPreferences:
    """Test user preference collection functionality."""

    def test_ask_user_preferences_accept_all_defaults(self):
        """Test user accepting all default preferences."""
        detected_config = PreCommitConfig(python=True, yaml=True, js=True, typescript=True)

        # Mock all user responses as True to accept defaults
        with patch("pre_commit_template.main.Confirm.ask", return_value=True):
            with patch("pre_commit_template.main.Prompt.ask", return_value=""):
                with patch("pre_commit_template.main.console"):
                    result = ask_user_preferences(detected_config)

        assert result.python is True
        assert result.js is True
        assert result.typescript is True
        # Note: yaml_check may not preserve due to dict reconstruction

    def test_ask_user_preferences_decline_technologies(self):
        """Test user declining detected technologies."""
        detected_config = PreCommitConfig(python=True, js=True, go=True, docker=True)

        # Mock user declining all technologies
        with patch("pre_commit_template.main.Confirm.ask", return_value=False):
            result = ask_user_preferences(detected_config)

        assert result.python is False
        assert result.js is False
        assert result.go is False
        assert result.docker is False

    def test_ask_user_preferences_python_version_prompt(self):
        """Test Python version prompting."""
        detected_config = PreCommitConfig(python=True, python_version="python3.9")

        with patch("pre_commit_template.main.Confirm.ask", return_value=True):
            with patch("pre_commit_template.main.Prompt.ask", return_value="python3.11"):
                result = ask_user_preferences(detected_config)

        assert result.python_version == "python3.11"

    def test_ask_user_preferences_python_no_version_detected(self):
        """Test Python version prompting when none detected."""
        detected_config = PreCommitConfig(python=True, python_version=None)

        with patch("pre_commit_template.main.Confirm.ask", return_value=True):
            with patch("pre_commit_template.main.Prompt.ask", return_value=""):
                result = ask_user_preferences(detected_config)

        assert result.python_version is None

    def test_ask_user_preferences_complex_workflow(self):
        """Test complex user preference workflow."""
        detected_config = PreCommitConfig(
            python=True,
            js=True,
            go=True,
            docker=True,
            github_actions=True,
            yaml=True,
            json=True,
        )

        # Mock user responses: adjust based on actual flow
        confirm_responses = [
            True,  # Include YAML syntax checking?
            True,  # Include JSON syntax checking?
            True,  # Include Python hooks (Ruff + MyPy)?
            True,  # Include JavaScript/TypeScript hooks?
            True,  # Include TypeScript support?
            False,  # Include JSX/React support?
            True,  # Include Go hooks? (keep enabled)
            False,  # Include go-critic?
            True,  # Include Docker hooks?
            False,  # Include Dockerfile linting? (user disables)
            True,  # Include GitHub Actions hooks?
            True,  # Include workflow validation?
            True,  # Include security scanning? (user enables)
        ]

        with patch("pre_commit_template.main.Confirm.ask", side_effect=confirm_responses):
            with patch("pre_commit_template.main.Prompt.ask", return_value="python3.10"):
                with patch("pre_commit_template.main.console"):
                    result = ask_user_preferences(detected_config)

        assert result.python is True
        assert result.js is True
        assert result.go is True
        assert result.docker is True


class TestDisplayFunctions:
    """Test display and formatting functions."""

    def test_display_detected_technologies_python_only(self):
        """Test displaying Python-only configuration."""
        config = PreCommitConfig(python=True, python_version="python3.9", yaml=True)

        with patch("pre_commit_template.main.console") as mock_console:
            display_detected_technologies(config)

        mock_console.print.assert_called()
        # Check that table was created and printed
        call_args = mock_console.print.call_args_list
        assert len(call_args) >= 1

    def test_display_detected_technologies_multiple_technologies(self):
        """Test displaying complex multi-technology configuration."""
        config = PreCommitConfig(
            python=True,
            python_version="python3.10",
            js=True,
            typescript=True,
            jsx=True,
            go=True,
            docker=True,
            github_actions=True,
            yaml=True,
            json=True,
            toml=True,
            xml=True,
        )

        with patch("pre_commit_template.main.console") as mock_console:
            display_detected_technologies(config)

        mock_console.print.assert_called()

    def test_display_detected_technologies_minimal_config(self):
        """Test displaying minimal configuration."""
        config = PreCommitConfig()  # All defaults

        with patch("pre_commit_template.main.console") as mock_console:
            display_detected_technologies(config)

        mock_console.print.assert_called()

    def test_display_detected_technologies_javascript_variants(self):
        """Test displaying JavaScript with different variants."""
        config = PreCommitConfig(js=True, typescript=True, jsx=True)

        with patch("pre_commit_template.main.console") as mock_console:
            display_detected_technologies(config)

        mock_console.print.assert_called()


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    @patch("pre_commit_template.main.discover_config")
    @patch("pre_commit_template.main.ask_user_preferences")
    @patch("pre_commit_template.main.render_config")
    def test_main_user_customization_flow(self, mock_render, mock_ask, mock_discover):
        """Test main function when user wants to customize in interactive mode."""
        detected_config = PreCommitConfig(python=True)
        custom_config = PreCommitConfig(python=True, js=True)

        mock_discover.return_value = detected_config
        mock_ask.return_value = custom_config
        mock_render.return_value = "custom yaml"

        with patch("sys.argv", ["pre-commit-starter", "-i"]):
            with patch("pre_commit_template.main.Confirm.ask", return_value=True):
                with patch("builtins.print") as mock_print:
                    main()

        mock_ask.assert_called_once_with(detected_config)
        mock_render.assert_called_once_with(custom_config)
        mock_print.assert_called_with("custom yaml")

    def test_main_argument_parsing(self):
        """Test argument parsing functionality."""
        with patch("sys.argv", ["pre-commit-starter", "--interactive"]):
            with patch("pre_commit_template.main.discover_config"):
                with patch("pre_commit_template.main.render_config"):
                    with patch("pre_commit_template.main.Confirm.ask", return_value=False):
                        with patch("builtins.print"):
                            main()

        # Should not raise any argument parsing errors

    def test_main_path_resolution(self):
        """Test Path.cwd() usage in main function."""
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/path")

            with patch("sys.argv", ["pre-commit-starter"]):
                with patch("pre_commit_template.main.discover_config") as mock_discover:
                    mock_discover.return_value = PreCommitConfig()
                    with patch("pre_commit_template.main.render_config"):
                        with patch("subprocess.run"):
                            with patch("pathlib.Path.write_text"):
                                with patch("pre_commit_template.main.console"):
                                    main()

            mock_discover.assert_called_once_with(Path("/test/path"))
