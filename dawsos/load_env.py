"""Load environment variables from .env file"""
import os
from pathlib import Path


def _safe_print(message: str) -> None:
    """Print helper that ignores broken pipe errors."""
    try:
        print(message)
    except BrokenPipeError:  # pragma: no cover - streamlit reruns can close stdout
        pass


def load_env():
    """Load environment variables from .env file if it exists"""
    # Try multiple locations for .env file
    current_dir = Path(__file__).parent  # dawsos/ directory
    possible_paths = [
        current_dir / '.env',  # dawsos/.env (preferred)
        Path('.env'),  # Current working directory
        Path('..') / '.env',  # Parent directory
    ]

    env_path = None
    for path in possible_paths:
        if path.exists():
            env_path = path
            break

    if env_path and env_path.exists():
        _safe_print(f"Loading environment from {env_path}...")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip("'").strip('"')
                    os.environ[key] = value
                    # Don't print the actual key value for security
                    _safe_print(f"  Set {key}")
        _safe_print("Environment loaded!")
        return True
    else:
        _safe_print("No .env file found. Create one with your API keys:")
        _safe_print("")
        _safe_print("ANTHROPIC_API_KEY=your-key-here")
        _safe_print("FMP_API_KEY=your-key-here")
        _safe_print("NEWSAPI_KEY=your-key-here")
        return False

if __name__ == "__main__":
    load_env()
