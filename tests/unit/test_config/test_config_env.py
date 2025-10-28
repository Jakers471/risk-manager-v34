"""Unit tests for config/env.py - Environment variable substitution.

Tests the environment variable substitution utilities in src/risk_manager/config/env.py
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from risk_manager.config.env import (
    load_env_file,
    substitute_env_vars,
    substitute_env_vars_recursive,
    validate_env_vars,
)


class TestLoadEnvFile:
    """Test load_env_file() function."""

    def test_load_valid_env_file(self, tmp_path):
        """Test loading valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_USERNAME=myusername
PROJECT_X_API_KEY=abc123xyz
DEBUG=true
""")

        result = load_env_file(env_file)

        assert result["PROJECT_X_USERNAME"] == "myusername"
        assert result["PROJECT_X_API_KEY"] == "abc123xyz"
        assert result["DEBUG"] == "true"

    def test_load_env_file_with_comments(self, tmp_path):
        """Test loading .env file with comments."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# This is a comment
PROJECT_X_USERNAME=myusername
# Another comment
PROJECT_X_API_KEY=abc123xyz
""")

        result = load_env_file(env_file)

        assert "PROJECT_X_USERNAME" in result
        assert "PROJECT_X_API_KEY" in result
        assert len(result) == 2

    def test_load_env_file_with_empty_lines(self, tmp_path):
        """Test loading .env file with empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_USERNAME=myusername

PROJECT_X_API_KEY=abc123xyz


DEBUG=true
""")

        result = load_env_file(env_file)

        assert len(result) == 3
        assert result["DEBUG"] == "true"

    def test_load_env_file_missing(self, tmp_path):
        """Test loading non-existent .env file returns empty dict."""
        result = load_env_file(tmp_path / "nonexistent.env")

        assert result == {}

    def test_load_env_file_with_equals_in_value(self, tmp_path):
        """Test loading .env file with = in value."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=abc=123=xyz")

        result = load_env_file(env_file)

        assert result["API_KEY"] == "abc=123=xyz"

    def test_load_env_file_with_double_quotes(self, tmp_path):
        """Test loading .env file with double-quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text('QUOTED="value with spaces"')

        result = load_env_file(env_file)

        assert "QUOTED" in result
        assert result["QUOTED"] == "value with spaces"

    def test_load_env_file_with_single_quotes(self, tmp_path):
        """Test loading .env file with single-quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text("QUOTED='single quoted'")

        result = load_env_file(env_file)

        assert result["QUOTED"] == "single quoted"

    def test_load_env_file_empty(self, tmp_path):
        """Test loading empty .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        result = load_env_file(env_file)

        assert result == {}

    def test_load_env_file_only_comments(self, tmp_path):
        """Test loading .env file with only comments."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# Comment 1
# Comment 2
""")

        result = load_env_file(env_file)

        assert result == {}

    def test_load_env_file_malformed_line(self, tmp_path):
        """Test loading .env file with malformed line (no =)."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
GOOD_KEY=good_value
MALFORMED_LINE_NO_EQUALS
ANOTHER_GOOD=another_value
""")

        result = load_env_file(env_file)

        assert result["GOOD_KEY"] == "good_value"
        assert result["ANOTHER_GOOD"] == "another_value"
        assert "MALFORMED_LINE_NO_EQUALS" not in result


class TestSubstituteEnvVars:
    """Test substitute_env_vars() function."""

    def test_substitute_single_var(self, tmp_path):
        """Test substituting single environment variable."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars("Hello ${USERNAME}", env_file)

        assert result == "Hello testuser"

    def test_substitute_multiple_vars(self, tmp_path):
        """Test substituting multiple environment variables."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
USERNAME=testuser
HOST=localhost
PORT=5432
""")

        result = substitute_env_vars(
            "postgresql://${USERNAME}@${HOST}:${PORT}/db",
            env_file
        )

        assert result == "postgresql://testuser@localhost:5432/db"

    def test_substitute_no_vars(self, tmp_path):
        """Test string with no variables."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars("Hello world", env_file)

        assert result == "Hello world"

    def test_substitute_missing_var_raises_error(self, tmp_path):
        """Test missing variable raises error by default."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        with pytest.raises(ValueError, match="MISSING_VAR"):
            substitute_env_vars("Hello ${MISSING_VAR}", env_file)

    def test_substitute_missing_var_keep_original(self, tmp_path):
        """Test missing variable keeps original when raise_on_missing=False."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars(
            "Hello ${MISSING_VAR}",
            env_file,
            raise_on_missing=False
        )

        assert result == "Hello ${MISSING_VAR}"

    def test_substitute_empty_string(self, tmp_path):
        """Test substituting empty string."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars("", env_file)

        assert result == ""

    def test_substitute_var_at_start(self, tmp_path):
        """Test variable at start of string."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars("${USERNAME} says hello", env_file)

        assert result == "testuser says hello"

    def test_substitute_var_at_end(self, tmp_path):
        """Test variable at end of string."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars("Hello ${USERNAME}", env_file)

        assert result == "Hello testuser"

    def test_substitute_same_var_twice(self, tmp_path):
        """Test same variable appearing twice."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars(
            "${USERNAME} and ${USERNAME}",
            env_file
        )

        assert result == "testuser and testuser"

    def test_substitute_from_os_environ(self, tmp_path):
        """Test substituting from os.environ when not in .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")  # Empty .env file

        with patch.dict(os.environ, {"TEST_VAR": "test_value"}, clear=False):
            result = substitute_env_vars("Value: ${TEST_VAR}", env_file)

            assert result == "Value: test_value"

    def test_substitute_env_file_takes_precedence(self, tmp_path):
        """Test that .env file takes precedence over os.environ."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=from_env_file")

        with patch.dict(os.environ, {"TEST_VAR": "from_os_environ"}, clear=False):
            result = substitute_env_vars("Value: ${TEST_VAR}", env_file)

            assert result == "Value: from_env_file"


class TestSubstituteEnvVarsRecursive:
    """Test substitute_env_vars_recursive() function."""

    def test_substitute_in_dict(self, tmp_path):
        """Test recursive substitution in dictionary."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
USERNAME=testuser
HOST=localhost
""")

        data = {
            "database": {
                "host": "${HOST}",
                "user": "${USERNAME}"
            }
        }

        result = substitute_env_vars_recursive(data, env_file)

        assert result["database"]["host"] == "localhost"
        assert result["database"]["user"] == "testuser"

    def test_substitute_in_list(self, tmp_path):
        """Test recursive substitution in list."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        data = ["${USERNAME}", "other_value", "${USERNAME}"]

        result = substitute_env_vars_recursive(data, env_file)

        assert result == ["testuser", "other_value", "testuser"]

    def test_substitute_in_nested_structure(self, tmp_path):
        """Test recursive substitution in deeply nested structure."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
USERNAME=testuser
HOST=localhost
""")

        data = {
            "servers": [
                {
                    "host": "${HOST}",
                    "users": ["${USERNAME}", "admin"]
                },
                {
                    "host": "remote.example.com",
                    "users": ["${USERNAME}"]
                }
            ]
        }

        result = substitute_env_vars_recursive(data, env_file)

        assert result["servers"][0]["host"] == "localhost"
        assert result["servers"][0]["users"][0] == "testuser"
        assert result["servers"][1]["users"][0] == "testuser"

    def test_substitute_preserves_non_string_types(self, tmp_path):
        """Test that non-string types are preserved."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        data = {
            "string": "${USERNAME}",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None
        }

        result = substitute_env_vars_recursive(data, env_file)

        assert result["string"] == "testuser"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None

    def test_substitute_empty_dict(self, tmp_path):
        """Test recursive substitution on empty dict."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars_recursive({}, env_file)

        assert result == {}

    def test_substitute_empty_list(self, tmp_path):
        """Test recursive substitution on empty list."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars_recursive([], env_file)

        assert result == []

    def test_substitute_with_missing_var(self, tmp_path):
        """Test recursive substitution with missing variable."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        data = {"value": "${MISSING_VAR}"}

        with pytest.raises(ValueError, match="MISSING_VAR"):
            substitute_env_vars_recursive(data, env_file)

    def test_substitute_plain_string(self, tmp_path):
        """Test recursive substitution on plain string."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=testuser")

        result = substitute_env_vars_recursive("Hello ${USERNAME}", env_file)

        assert result == "Hello testuser"


class TestValidateEnvVars:
    """Test validate_env_vars() function."""

    def test_validate_all_vars_present(self, tmp_path):
        """Test validation when all required variables present."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_USERNAME=user
PROJECT_X_API_KEY=key
""")

        required = ["PROJECT_X_USERNAME", "PROJECT_X_API_KEY"]

        missing = validate_env_vars(required, env_file)

        assert missing == []

    def test_validate_missing_single_var(self, tmp_path, monkeypatch):
        """Test validation when single variable missing."""
        # Isolate from real .env file
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("PROJECT_X_API_KEY", raising=False)

        env_file = tmp_path / ".env"
        env_file.write_text("PROJECT_X_USERNAME=user")

        required = ["PROJECT_X_USERNAME", "PROJECT_X_API_KEY"]

        missing = validate_env_vars(required, env_file)

        assert "PROJECT_X_API_KEY" in missing
        assert len(missing) == 1

    def test_validate_missing_multiple_vars(self, tmp_path):
        """Test validation when multiple variables missing."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        required = ["VAR1", "VAR2", "VAR3"]

        missing = validate_env_vars(required, env_file)

        assert "VAR1" in missing
        assert "VAR2" in missing
        assert "VAR3" in missing
        assert len(missing) == 3

    def test_validate_no_required_vars(self, tmp_path):
        """Test validation when no variables required."""
        env_file = tmp_path / ".env"
        env_file.write_text("USERNAME=user")

        missing = validate_env_vars([], env_file)

        assert missing == []

    def test_validate_vars_from_os_environ(self, tmp_path):
        """Test validation finds vars in os.environ."""
        env_file = tmp_path / ".env"
        env_file.write_text("VAR1=value1")

        required = ["VAR1", "VAR2"]

        with patch.dict(os.environ, {"VAR2": "value2"}, clear=False):
            missing = validate_env_vars(required, env_file)

            assert missing == []

    def test_validate_empty_value_counts_as_present(self, tmp_path):
        """Test that empty string values count as present."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PROJECT_X_USERNAME=
PROJECT_X_API_KEY=key
""")

        required = ["PROJECT_X_USERNAME", "PROJECT_X_API_KEY"]

        missing = validate_env_vars(required, env_file)

        assert missing == []
