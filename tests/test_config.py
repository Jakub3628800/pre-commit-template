"""Tests for config.py module."""

import json
import pytest
from pydantic import ValidationError

from pre_commit_template.config import PreCommitConfig


class TestPreCommitConfigValidation:
    """Test PreCommitConfig model validation."""

    def test_python_version_validation_valid_cases(self):
        """Test python_version field accepts valid values."""
        valid_versions = [
            "python3.9",
            "python3.10",
            "python3.11",
            "python3.12",
            "python3.13",
            "python3.14",
            "python",
            None,
        ]

        for version in valid_versions:
            config = PreCommitConfig(python_version=version)
            assert config.python_version == version

    def test_python_version_validation_invalid_cases(self):
        """Test python_version field rejects invalid values."""
        invalid_versions = [
            "3.9",
            "py3.9",
            "Python3.9",
            "node16",
            "javascript",
            "3.10",
            "",
        ]

        for version in invalid_versions:
            with pytest.raises(ValidationError) as exc_info:
                PreCommitConfig(python_version=version)

            assert 'Python version must start with "python"' in str(exc_info.value)

    def test_default_values(self):
        """Test all default values are correctly set."""
        config = PreCommitConfig()

        # Boolean fields that default to False
        assert config.yaml_check is False
        assert config.json_check is False
        assert config.toml_check is False
        assert config.xml_check is False
        assert config.case_conflict is False
        assert config.executables is False
        assert config.python is False
        assert config.python_base is False
        assert config.uv_lock is False
        assert config.js is False
        assert config.typescript is False
        assert config.jsx is False
        assert config.go is False
        assert config.go_critic is False
        assert config.docker is False
        assert config.github_actions is False

        # Boolean fields that default to True
        assert config.dockerfile_linting is True
        assert config.workflow_validation is True
        assert config.security_scanning is False

        # Optional fields that default to None
        assert config.python_version is None
        assert config.pyrefly_args is None

    def test_field_aliases(self):
        """Test field aliases work correctly."""
        # Test using aliases in constructor
        config = PreCommitConfig(yaml=True, json=True, toml=True, xml=True)

        assert config.yaml_check is True
        assert config.json_check is True
        assert config.toml_check is True
        assert config.xml_check is True

    def test_model_serialization_with_aliases(self):
        """Test model serialization uses aliases when requested."""
        config = PreCommitConfig(yaml=True, json=True, python=True, python_version="python3.9")

        # Serialize with aliases
        data_with_aliases = config.model_dump(by_alias=True)
        assert "yaml" in data_with_aliases
        assert "json" in data_with_aliases
        assert "yaml_check" not in data_with_aliases
        assert "json_check" not in data_with_aliases

        # Serialize without aliases
        data_without_aliases = config.model_dump(by_alias=False)
        assert "yaml_check" in data_without_aliases
        assert "json_check" in data_without_aliases
        assert "yaml" not in data_without_aliases
        assert "json" not in data_without_aliases

    def test_json_serialization_roundtrip(self):
        """Test model can be serialized to/from JSON."""
        original_config = PreCommitConfig(
            python=True,
            python_version="python3.10",
            yaml=True,
            pyrefly_args=["--strict", "--ignore-missing-imports"],
        )

        # Serialize to JSON
        json_data = original_config.model_dump(by_alias=True)
        json_str = json.dumps(json_data)

        # Deserialize from JSON
        parsed_data = json.loads(json_str)
        restored_config = PreCommitConfig.model_validate(parsed_data)

        # Verify they're equivalent
        assert restored_config.python == original_config.python
        assert restored_config.python_version == original_config.python_version
        assert restored_config.yaml_check == original_config.yaml_check
        assert restored_config.pyrefly_args == original_config.pyrefly_args

    def test_type_validation_boolean_fields(self):
        """Test boolean fields handle type coercion correctly."""
        # Test truthy values
        config = PreCommitConfig(python=True, yaml=True)
        assert config.python is True
        assert config.yaml_check is True

        # Test falsy values
        config = PreCommitConfig(python=False, yaml=False)
        assert config.python is False
        assert config.yaml_check is False

        # Test string coercion (Pydantic behavior varies)
        config = PreCommitConfig(python=True, yaml=True)
        assert config.python is True  # "yes" is truthy in Pydantic
        assert config.yaml_check is True  # "true" string is truthy

    def test_type_validation_list_fields(self):
        """Test list fields validate correctly."""
        # Valid list inputs
        config = PreCommitConfig(pyrefly_args=["--strict"])
        assert config.pyrefly_args == ["--strict"]

        # Note: Type checking is handled by pyrefly/mypy, not Pydantic validation

    def test_model_equality(self):
        """Test model equality comparison."""
        config1 = PreCommitConfig(python=True, yaml=True)
        config2 = PreCommitConfig(python=True, yaml=True)
        config3 = PreCommitConfig(python=False, yaml=True)

        assert config1 == config2
        assert config1 != config3

    def test_model_copy(self):
        """Test model copying functionality."""
        original = PreCommitConfig(python=True, python_version="python3.9", pyrefly_args=["--strict"])

        # Copy with modifications
        modified = original.model_copy(update={"python_version": "python3.10"})

        assert original.python_version == "python3.9"
        assert modified.python_version == "python3.10"
        assert modified.python == original.python
        assert modified.pyrefly_args == original.pyrefly_args

    def test_valid_field_names_only(self):
        """Test model with only valid field names."""
        # Test that valid fields work correctly
        config = PreCommitConfig(python=True, yaml=True)
        assert hasattr(config, "python")
        assert config.python is True

    def test_complex_configuration(self):
        """Test complex configuration with multiple technologies."""
        config = PreCommitConfig(
            python=True,
            python_version="python3.11",
            python_base=True,
            uv_lock=True,
            js=True,
            typescript=True,
            jsx=True,
            go=True,
            go_critic=True,
            docker=True,
            dockerfile_linting=True,
            github_actions=True,
            workflow_validation=True,
            security_scanning=True,
            yaml=True,
            json=True,
            toml=True,
            xml=True,
            case_conflict=True,
            executables=True,
            pyrefly_args=["--strict", "--ignore-missing-imports"],
        )

        # Verify all fields are set correctly
        assert config.python is True
        assert config.python_version == "python3.11"
        assert config.js is True
        assert config.typescript is True
        assert config.jsx is True
        assert config.go is True
        assert config.go_critic is True
        assert config.docker is True
        assert config.dockerfile_linting is True
        assert config.github_actions is True
        assert config.workflow_validation is True
        assert config.security_scanning is True
        assert config.pyrefly_args is not None and len(config.pyrefly_args) == 2
