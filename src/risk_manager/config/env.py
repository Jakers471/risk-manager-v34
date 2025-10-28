"""Environment variable substitution for configuration files.

Supports ${VAR_NAME} syntax in YAML files with:
- Environment variable expansion
- .env file loading
- Clear error messages for missing variables
- Recursive substitution support
"""

import os
import re
from pathlib import Path
from typing import Any


def load_env_file(env_file: str | Path = ".env") -> dict[str, str]:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file (default: .env in current directory)

    Returns:
        Dictionary of environment variables from the file

    Example .env file:
        PROJECT_X_USERNAME=myusername
        PROJECT_X_API_KEY=abc123xyz
        # Comments are ignored

    Notes:
        - Lines starting with # are ignored (comments)
        - Empty lines are ignored
        - Format: KEY=VALUE (no spaces around =)
        - Variables are NOT added to os.environ (local scope only)
    """
    env_vars = {}
    env_path = Path(env_file)

    if not env_path.exists():
        return env_vars

    with open(env_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Remove whitespace
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' not in line:
                continue  # Skip malformed lines

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            env_vars[key] = value

    return env_vars


def substitute_env_vars(
    text: str,
    env_file: str | Path = ".env",
    raise_on_missing: bool = True
) -> str:
    """Substitute environment variables in text.

    Replaces ${VAR_NAME} with the value of environment variable VAR_NAME.

    Args:
        text: Text containing ${VAR_NAME} placeholders
        env_file: Path to .env file to load (default: .env)
        raise_on_missing: If True, raise error for missing variables.
                         If False, leave ${VAR_NAME} as-is.

    Returns:
        Text with environment variables substituted

    Raises:
        ValueError: If variable not found and raise_on_missing=True

    Example:
        # .env file:
        PROJECT_X_USERNAME=jake
        PROJECT_X_API_KEY=secret123

        # YAML file:
        username: "${PROJECT_X_USERNAME}"
        api_key: "${PROJECT_X_API_KEY}"

        # After substitution:
        username: "jake"
        api_key: "secret123"

    Variable Resolution Order:
        1. Check .env file (if exists)
        2. Check os.environ (system environment variables)
        3. If not found: raise ValueError or leave as-is
    """
    # Load .env file
    env_vars = load_env_file(env_file)

    # Pattern: ${VAR_NAME} or $VAR_NAME
    # We'll support both but prefer ${VAR_NAME} syntax
    pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}'

    def replacer(match: re.Match) -> str:
        """Replace a single ${VAR_NAME} match."""
        var_name = match.group(1)

        # Try .env file first
        if var_name in env_vars:
            return env_vars[var_name]

        # Try system environment
        if var_name in os.environ:
            return os.environ[var_name]

        # Not found
        if raise_on_missing:
            raise ValueError(
                f"Environment variable '{var_name}' not found.\n"
                f"Looked in:\n"
                f"  1. .env file: {Path(env_file).absolute()}\n"
                f"  2. System environment variables\n"
                f"Fix: Add {var_name}=<value> to .env file or set as environment variable."
            )
        else:
            # Leave as-is
            return match.group(0)

    return re.sub(pattern, replacer, text)


def substitute_env_vars_recursive(
    data: Any,
    env_file: str | Path = ".env",
    raise_on_missing: bool = True
) -> Any:
    """Recursively substitute environment variables in nested data structures.

    Args:
        data: Dictionary, list, or string to process
        env_file: Path to .env file
        raise_on_missing: If True, raise error for missing variables

    Returns:
        Data with environment variables substituted

    Example:
        data = {
            'username': '${PROJECT_X_USERNAME}',
            'nested': {
                'api_key': '${PROJECT_X_API_KEY}'
            },
            'list': ['${VAR1}', '${VAR2}']
        }

        result = substitute_env_vars_recursive(data)
        # All ${VAR_NAME} replaced in nested structure
    """
    if isinstance(data, str):
        return substitute_env_vars(data, env_file, raise_on_missing)
    elif isinstance(data, dict):
        return {
            key: substitute_env_vars_recursive(value, env_file, raise_on_missing)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [
            substitute_env_vars_recursive(item, env_file, raise_on_missing)
            for item in data
        ]
    else:
        # Return as-is for other types (int, float, bool, None)
        return data


def validate_env_vars(required_vars: list[str], env_file: str | Path = ".env") -> list[str]:
    """Validate that required environment variables are present.

    Args:
        required_vars: List of required variable names
        env_file: Path to .env file

    Returns:
        List of missing variable names (empty if all present)

    Example:
        required = ['PROJECT_X_USERNAME', 'PROJECT_X_API_KEY']
        missing = validate_env_vars(required)

        if missing:
            print(f"Missing variables: {missing}")
    """
    env_vars = load_env_file(env_file)
    missing = []

    for var_name in required_vars:
        if var_name not in env_vars and var_name not in os.environ:
            missing.append(var_name)

    return missing


# Example usage
if __name__ == "__main__":
    # Example: Substitute environment variables
    yaml_text = """
    topstepx:
      username: "${PROJECT_X_USERNAME}"
      api_key: "${PROJECT_X_API_KEY}"
      api_url: "https://api.topstepx.com/api"
    """

    try:
        result = substitute_env_vars(yaml_text)
        print("Substitution successful:")
        print(result)
    except ValueError as e:
        print(f"Error: {e}")

    # Example: Validate required variables
    required = ['PROJECT_X_USERNAME', 'PROJECT_X_API_KEY']
    missing = validate_env_vars(required)

    if missing:
        print(f"\nMissing required variables: {missing}")
        print("Create .env file with:")
        for var in missing:
            print(f"  {var}=<your-value>")
    else:
        print("\nAll required variables present!")
