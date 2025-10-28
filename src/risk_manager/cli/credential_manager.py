"""Credential management for Risk Manager V34.

Handles secure credential loading from:
1. Environment variables (.env file)
2. OS keyring (optional, as alternative to .env)

Security features:
- Never logs full credentials (automatic redaction)
- Validates credentials before exposing to SDK
- Supports both practice and live account credentials
- NEVER accepts credentials via CLI args (security policy)
"""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CredentialError(Exception):
    """Raised when credentials are missing or invalid."""
    pass


class ProjectXCredentials(BaseModel):
    """TopstepX/ProjectX API credentials with validation."""

    username: str = Field(..., min_length=1, description="TopstepX username")
    api_key: str = Field(..., min_length=1, description="TopstepX API key")
    client_id: Optional[str] = Field(default=None, description="Client ID (if required)")
    client_secret: Optional[str] = Field(default=None, description="Client secret (if required)")

    @field_validator("username", "api_key", "client_id", "client_secret")
    @classmethod
    def validate_no_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Validate no leading/trailing whitespace."""
        if v and v != v.strip():
            raise ValueError("Credentials must not have leading/trailing whitespace")
        return v

    def __repr__(self) -> str:
        """Redacted representation for logging."""
        return (
            f"ProjectXCredentials("
            f"username={self._redact(self.username)}, "
            f"api_key={self._redact(self.api_key)}, "
            f"client_id={self._redact(self.client_id)}, "
            f"client_secret={self._redact(self.client_secret)})"
        )

    def __str__(self) -> str:
        """Redacted string for logging."""
        return self.__repr__()

    @staticmethod
    def _redact(value: Optional[str]) -> str:
        """Redact credential for logging."""
        if not value:
            return "None"
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"


def get_credentials(
    env_file: str | Path = ".env",
    use_keyring: bool = False
) -> ProjectXCredentials:
    """Get TopstepX API credentials from environment or keyring.

    Credentials are loaded in this priority order:
    1. .env file (if exists)
    2. System environment variables
    3. OS keyring (if use_keyring=True)

    Args:
        env_file: Path to .env file (default: .env)
        use_keyring: If True, try to load from OS keyring (default: False)

    Returns:
        ProjectXCredentials instance with validated credentials

    Raises:
        CredentialError: If required credentials are missing or invalid

    Example:
        # Load from .env file
        credentials = get_credentials()

        # Use with SDK
        from project_x_py import TradingSuite
        suite = TradingSuite(
            username=credentials.username,
            api_key=credentials.api_key
        )

    Environment Variables:
        Required:
        - TOPSTEPX_USERNAME or PROJECT_X_USERNAME
        - TOPSTEPX_API_KEY or PROJECT_X_API_KEY

        Optional:
        - TOPSTEPX_CLIENT_ID or PROJECT_X_CLIENT_ID
        - TOPSTEPX_CLIENT_SECRET or PROJECT_X_CLIENT_SECRET

    Security:
        - Credentials are validated before return
        - Automatic redaction in logs (only first/last 4 chars shown)
        - Never accepts credentials via CLI args
        - .env file must be in .gitignore (never committed)
    """
    env_path = Path(env_file)

    # Load .env file if exists
    env_vars = {}
    if env_path.exists():
        logger.info(f"Loading credentials from: {env_path.absolute()}")
        env_vars = _load_env_file(env_path)
    else:
        logger.info(f".env file not found at: {env_path.absolute()}")
        logger.info("Checking system environment variables...")

    # Try to get credentials from environment (with multiple possible names)
    username = (
        env_vars.get("TOPSTEPX_USERNAME") or
        env_vars.get("PROJECT_X_USERNAME") or
        os.getenv("TOPSTEPX_USERNAME") or
        os.getenv("PROJECT_X_USERNAME")
    )

    api_key = (
        env_vars.get("TOPSTEPX_API_KEY") or
        env_vars.get("PROJECT_X_API_KEY") or
        os.getenv("TOPSTEPX_API_KEY") or
        os.getenv("PROJECT_X_API_KEY")
    )

    client_id = (
        env_vars.get("TOPSTEPX_CLIENT_ID") or
        env_vars.get("PROJECT_X_CLIENT_ID") or
        os.getenv("TOPSTEPX_CLIENT_ID") or
        os.getenv("PROJECT_X_CLIENT_ID")
    )

    client_secret = (
        env_vars.get("TOPSTEPX_CLIENT_SECRET") or
        env_vars.get("PROJECT_X_CLIENT_SECRET") or
        os.getenv("TOPSTEPX_CLIENT_SECRET") or
        os.getenv("PROJECT_X_CLIENT_SECRET")
    )

    # Try keyring as fallback (if enabled)
    if use_keyring and (not username or not api_key):
        logger.info("Trying OS keyring as fallback...")
        keyring_creds = _load_from_keyring()
        if keyring_creds:
            username = username or keyring_creds.get("username")
            api_key = api_key or keyring_creds.get("api_key")
            client_id = client_id or keyring_creds.get("client_id")
            client_secret = client_secret or keyring_creds.get("client_secret")

    # Validate we have required credentials
    missing = []
    if not username:
        missing.append("username (TOPSTEPX_USERNAME or PROJECT_X_USERNAME)")
    if not api_key:
        missing.append("api_key (TOPSTEPX_API_KEY or PROJECT_X_API_KEY)")

    if missing:
        raise CredentialError(
            f"Missing required credentials: {', '.join(missing)}\n\n"
            f"Fix: Create {env_path.absolute()} with:\n"
            f"  TOPSTEPX_USERNAME=your_username\n"
            f"  TOPSTEPX_API_KEY=your_api_key\n\n"
            f"Or set as environment variables.\n\n"
            f"Template available at: .env.template\n"
            f"Copy to .env and fill in your credentials:\n"
            f"  cp .env.template .env\n"
        )

    # Create validated credentials object
    try:
        credentials = ProjectXCredentials(
            username=username,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret
        )

        logger.info(f"Credentials loaded successfully for user: {credentials._redact(username)}")
        return credentials

    except Exception as e:
        raise CredentialError(f"Credential validation failed: {e}")


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}

    with open(env_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' not in line:
                logger.warning(f"Skipping malformed line {line_num} in {env_path}")
                continue

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


def _load_from_keyring() -> Optional[dict[str, str]]:
    """Load credentials from OS keyring.

    Returns:
        Dictionary with credentials, or None if keyring not available

    Note:
        This is an optional feature. If keyring library is not installed,
        returns None and logs a warning.
    """
    try:
        import keyring
    except ImportError:
        logger.warning(
            "keyring library not installed. Cannot load from OS keyring.\n"
            "Install with: pip install keyring"
        )
        return None

    try:
        # Load from keyring with service name "risk-manager-v34"
        service_name = "risk-manager-v34"

        username = keyring.get_password(service_name, "username")
        api_key = keyring.get_password(service_name, "api_key")
        client_id = keyring.get_password(service_name, "client_id")
        client_secret = keyring.get_password(service_name, "client_secret")

        if username or api_key:
            logger.info("Credentials loaded from OS keyring")
            return {
                "username": username,
                "api_key": api_key,
                "client_id": client_id,
                "client_secret": client_secret
            }
        else:
            logger.info("No credentials found in OS keyring")
            return None

    except Exception as e:
        logger.warning(f"Failed to load from keyring: {e}")
        return None


def save_to_keyring(credentials: ProjectXCredentials) -> None:
    """Save credentials to OS keyring.

    Args:
        credentials: Credentials to save

    Raises:
        ImportError: If keyring library not installed
        Exception: If save fails

    Example:
        creds = get_credentials()
        save_to_keyring(creds)  # Save for future use

    Note:
        This is an optional convenience feature. Most users will use .env file.
    """
    try:
        import keyring
    except ImportError:
        raise ImportError(
            "keyring library not installed. Cannot save to OS keyring.\n"
            "Install with: pip install keyring"
        )

    service_name = "risk-manager-v34"

    keyring.set_password(service_name, "username", credentials.username)
    keyring.set_password(service_name, "api_key", credentials.api_key)

    if credentials.client_id:
        keyring.set_password(service_name, "client_id", credentials.client_id)
    if credentials.client_secret:
        keyring.set_password(service_name, "client_secret", credentials.client_secret)

    logger.info(f"Credentials saved to OS keyring for user: {credentials._redact(credentials.username)}")


def validate_credentials(credentials: ProjectXCredentials) -> bool:
    """Validate credentials are present and properly formatted.

    Args:
        credentials: Credentials to validate

    Returns:
        True if valid

    Raises:
        CredentialError: If validation fails

    Note:
        This performs basic validation only (presence, format).
        It does NOT test credentials against the API.
    """
    errors = []

    if not credentials.username:
        errors.append("Username is empty")
    elif len(credentials.username) < 3:
        errors.append("Username too short (minimum 3 characters)")

    if not credentials.api_key:
        errors.append("API key is empty")
    elif len(credentials.api_key) < 16:
        errors.append("API key too short (minimum 16 characters)")

    if errors:
        raise CredentialError(f"Credential validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return True


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    try:
        # Load credentials
        print("Loading credentials...")
        creds = get_credentials()

        print("\nCredentials loaded:")
        print(f"  Username: {creds._redact(creds.username)}")
        print(f"  API Key: {creds._redact(creds.api_key)}")

        if creds.client_id:
            print(f"  Client ID: {creds._redact(creds.client_id)}")
        if creds.client_secret:
            print(f"  Client Secret: {creds._redact(creds.client_secret)}")

        # Validate
        print("\nValidating credentials...")
        validate_credentials(creds)
        print("✓ Credentials are valid")

    except CredentialError as e:
        print(f"\nCredential Error:\n{e}")
    except Exception as e:
        print(f"\nUnexpected Error:\n{e}")
