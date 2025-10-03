"""
Secure Credential Manager for DawsOS API Keys

Provides centralized, secure credential management with:
- Environment variable support (primary method)
- .env file loading (fallback)
- Secure key validation and masking
- Graceful degradation (no crashes on missing keys)
"""

import os
from typing import Dict, Optional
from pathlib import Path


class CredentialManager:
    """
    Manages API credentials securely for DawsOS.

    Features:
    - Loads from environment variables first (highest priority)
    - Falls back to .env file if environment variable not set
    - Never logs full API keys (only masked versions)
    - Graceful degradation: warns on missing keys but doesn't crash
    - Validates all credentials at startup

    Supported API Keys:
    - ANTHROPIC_API_KEY: Claude API (required for core functionality)
    - FMP_API_KEY: Financial Modeling Prep
    - FRED_API_KEY: Federal Reserve Economic Data
    - NEWSAPI_KEY: News API
    - ALPHA_VANTAGE_KEY: Alpha Vantage (optional fallback)
    """

    # Define all supported credentials
    SUPPORTED_KEYS = {
        'ANTHROPIC_API_KEY': {
            'required': True,
            'description': 'Claude API key for LLM functionality',
            'prefix': 'sk-ant-'
        },
        'FMP_API_KEY': {
            'required': False,
            'description': 'Financial Modeling Prep API key for market data',
            'prefix': None
        },
        'FRED_API_KEY': {
            'required': False,
            'description': 'Federal Reserve Economic Data API key',
            'prefix': None
        },
        'NEWSAPI_KEY': {
            'required': False,
            'description': 'News API key for news and sentiment analysis',
            'prefix': None
        },
        'ALPHA_VANTAGE_KEY': {
            'required': False,
            'description': 'Alpha Vantage API key (optional fallback)',
            'prefix': None
        }
    }

    def __init__(self, env_file: str = '.env', verbose: bool = True):
        """
        Initialize credential manager and load credentials.

        Args:
            env_file: Path to .env file (relative to project root or absolute)
            verbose: Whether to print validation warnings
        """
        self.env_file = env_file
        self.verbose = verbose
        self._credentials = {}

        # Load credentials
        self._load_from_env_file()
        self._load_from_environment()

        # Validate on initialization if verbose
        if verbose:
            validation_results = self.validate_all()
            self._print_validation_results(validation_results)

    def _load_from_env_file(self):
        """
        Load credentials from .env file if it exists.

        Note: This is a simple implementation without python-dotenv dependency.
        Loads key=value pairs from .env file.
        """
        # Try multiple possible locations for .env file
        env_paths = [
            Path(self.env_file),  # Relative to current directory
            Path.cwd() / self.env_file,  # Current working directory
            Path(__file__).parent.parent.parent / self.env_file,  # Project root
        ]

        env_file_path = None
        for path in env_paths:
            if path.exists() and path.is_file():
                env_file_path = path
                break

        if not env_file_path:
            if self.verbose:
                print(f"[CredentialManager] No .env file found at {self.env_file}")
            return

        try:
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Only load supported keys
                        if key in self.SUPPORTED_KEYS:
                            self._credentials[key] = value

            if self.verbose:
                print(f"[CredentialManager] Loaded credentials from {env_file_path}")

        except Exception as e:
            if self.verbose:
                print(f"[CredentialManager] Error loading .env file: {e}")

    def _load_from_environment(self):
        """
        Load credentials from environment variables.
        Environment variables take precedence over .env file.
        """
        for key in self.SUPPORTED_KEYS:
            env_value = os.getenv(key)
            if env_value:
                self._credentials[key] = env_value

    def get(self, key_name: str, required: bool = True) -> str:
        """
        Get credential by name.

        Args:
            key_name: Name of the credential (e.g., 'ANTHROPIC_API_KEY')
            required: If True, warn when credential is missing

        Returns:
            Credential value or empty string if not found
        """
        value = self._credentials.get(key_name, '')

        # Warn if missing and required
        if not value and required:
            key_info = self.SUPPORTED_KEYS.get(key_name, {})
            description = key_info.get('description', key_name)

            if self.verbose:
                print(f"[CredentialManager] WARNING: Missing credential '{key_name}'")
                print(f"  Description: {description}")
                print(f"  Set via environment variable or .env file")

        return value

    def validate_all(self) -> Dict[str, bool]:
        """
        Check which credentials are available.

        Returns:
            Dictionary mapping credential names to availability status
        """
        results = {}

        for key, config in self.SUPPORTED_KEYS.items():
            is_available = bool(self._credentials.get(key))
            results[key] = is_available

        return results

    def _print_validation_results(self, results: Dict[str, bool]):
        """Print validation results on initialization."""
        print("\n" + "="*60)
        print("DawsOS Credential Validation")
        print("="*60)

        # Required credentials
        print("\nRequired Credentials:")
        for key, config in self.SUPPORTED_KEYS.items():
            if config['required']:
                status = "✓ Available" if results[key] else "✗ MISSING"
                masked = self.mask_key(self._credentials.get(key, ''))
                print(f"  {key:25} {status:15} {masked}")

        # Optional credentials
        print("\nOptional Credentials:")
        for key, config in self.SUPPORTED_KEYS.items():
            if not config['required']:
                status = "✓ Available" if results[key] else "✗ Missing"
                masked = self.mask_key(self._credentials.get(key, ''))
                print(f"  {key:25} {status:15} {masked}")

        print("="*60 + "\n")

        # Check for critical missing credentials
        missing_required = [
            key for key, config in self.SUPPORTED_KEYS.items()
            if config['required'] and not results[key]
        ]

        if missing_required:
            print("WARNING: Missing required credentials:")
            for key in missing_required:
                config = self.SUPPORTED_KEYS[key]
                print(f"  - {key}: {config['description']}")
            print()

    def mask_key(self, key: str) -> str:
        """
        Return masked version of API key for safe logging.

        Args:
            key: API key to mask

        Returns:
            Masked key showing only first 8 chars and last 3 chars
            Examples:
                'sk-ant-12345678...xyz'
                'abcd1234...xyz'
                '' (for empty keys)
        """
        if not key:
            return ''

        if len(key) <= 11:
            # For short keys, show less
            return key[:3] + '...'

        # Show first 8 chars and last 3 chars
        return key[:8] + '...' + key[-3:]

    def get_all_credentials(self) -> Dict[str, str]:
        """
        Get all loaded credentials (MASKED for safety).

        Returns:
            Dictionary of masked credentials
        """
        return {
            key: self.mask_key(value)
            for key, value in self._credentials.items()
        }

    def has_credential(self, key_name: str) -> bool:
        """
        Check if a credential is available.

        Args:
            key_name: Name of the credential

        Returns:
            True if credential is available, False otherwise
        """
        return bool(self._credentials.get(key_name))

    def get_raw(self, key_name: str) -> str:
        """
        Get raw credential value without warnings.

        Args:
            key_name: Name of the credential

        Returns:
            Raw credential value or empty string
        """
        return self._credentials.get(key_name, '')


# Singleton instance
_credential_manager = None


def get_credential_manager(env_file: str = '.env', verbose: bool = False) -> CredentialManager:
    """
    Get singleton credential manager instance.

    Args:
        env_file: Path to .env file (only used on first call)
        verbose: Whether to print validation warnings (only used on first call)

    Returns:
        CredentialManager instance
    """
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager(env_file=env_file, verbose=verbose)
    return _credential_manager
