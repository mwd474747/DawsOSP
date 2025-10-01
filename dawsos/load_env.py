"""Load environment variables from .env file"""
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file if it exists"""
    env_path = Path('.env')

    if env_path.exists():
        print("Loading environment from .env file...")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip("'").strip('"')
                    os.environ[key] = value
                    # Don't print the actual key value for security
                    print(f"  Set {key}")
        print("Environment loaded!")
        return True
    else:
        print("No .env file found. Create one with your API keys:")
        print("")
        print("ANTHROPIC_API_KEY=your-key-here")
        print("FMP_API_KEY=your-key-here")
        print("NEWSAPI_KEY=your-key-here")
        return False

if __name__ == "__main__":
    load_env()