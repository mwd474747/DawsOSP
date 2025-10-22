# DawsOS Credential Manager

## Overview

The `CredentialManager` provides secure, centralized management of API keys and credentials for DawsOS. It ensures credentials are never logged in plaintext and provides graceful degradation when credentials are missing.

## Features

- **Environment Variable Support**: Primary method for loading credentials
- **.env File Support**: Automatic loading from `.env` file
- **Secure Key Masking**: Never logs full API keys (only first 8 + last 3 chars)
- **Graceful Degradation**: Warns on missing keys but doesn't crash
- **Validation**: Startup validation shows which credentials are configured
- **Singleton Pattern**: Single instance shared across application

## Supported API Keys

### Required
- **ANTHROPIC_API_KEY**: Claude API key for LLM functionality
  - Get at: https://console.anthropic.com/

### Optional
- **FMP_API_KEY**: Financial Modeling Prep for market data
  - Get at: https://financialmodelingprep.com/developer/docs/
- **FRED_API_KEY**: Federal Reserve Economic Data
  - Get at: https://fred.stlouisfed.org/docs/api/api_key.html
- **NEWSAPI_KEY**: News API for news and sentiment
  - Get at: https://newsapi.org/register
- **ALPHA_VANTAGE_KEY**: Alpha Vantage (optional fallback)
  - Get at: https://www.alphavantage.co/support/#api-key

## Usage

### Basic Usage

```python
from dawsos.core.credentials import CredentialManager

# Initialize (with validation output)
credentials = CredentialManager(verbose=True)

# Get a credential
api_key = credentials.get('ANTHROPIC_API_KEY', required=True)

# Check if credential exists
if credentials.has_credential('FMP_API_KEY'):
    market_key = credentials.get('FMP_API_KEY', required=False)
```

### Using the Singleton

```python
from dawsos.core.credentials import get_credential_manager

# Get singleton instance (recommended)
credentials = get_credential_manager()
api_key = credentials.get('ANTHROPIC_API_KEY')
```

### In Capability Classes

```python
from dawsos.core.credentials import get_credential_manager

class MyCapability:
    def __init__(self):
        credentials = get_credential_manager()
        self.api_key = credentials.get('MY_API_KEY', required=False)
```

## Configuration Methods

### Method 1: Environment Variables (Recommended for Production)

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export FMP_API_KEY=your-fmp-key
export FRED_API_KEY=your-fred-key
```

### Method 2: .env File (Recommended for Development)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your keys:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   FMP_API_KEY=your-fmp-key
   FRED_API_KEY=your-fred-key
   NEWSAPI_KEY=your-news-key
   ALPHA_VANTAGE_KEY=your-av-key
   ```

3. The `.env` file is automatically loaded on initialization

## API Reference

### CredentialManager Class

#### `__init__(env_file: str = '.env', verbose: bool = True)`
Initialize the credential manager.

**Parameters:**
- `env_file`: Path to .env file (default: '.env')
- `verbose`: Print validation warnings (default: True)

#### `get(key_name: str, required: bool = True) -> str`
Get a credential by name.

**Parameters:**
- `key_name`: Name of the credential
- `required`: If True, warn when credential is missing

**Returns:**
- Credential value or empty string if not found

**Example:**
```python
api_key = credentials.get('ANTHROPIC_API_KEY', required=True)
```

#### `validate_all() -> Dict[str, bool]`
Check which credentials are available.

**Returns:**
- Dictionary mapping credential names to availability status

**Example:**
```python
results = credentials.validate_all()
# {'ANTHROPIC_API_KEY': True, 'FMP_API_KEY': False, ...}
```

#### `mask_key(key: str) -> str`
Return masked version of API key for safe logging.

**Parameters:**
- `key`: API key to mask

**Returns:**
- Masked key (e.g., 'sk-ant-12...xyz')

**Example:**
```python
masked = credentials.mask_key('sk-ant-1234567890abcxyz')
# Returns: 'sk-ant-12...xyz'
```

#### `has_credential(key_name: str) -> bool`
Check if a credential is available.

**Parameters:**
- `key_name`: Name of the credential

**Returns:**
- True if credential is available, False otherwise

**Example:**
```python
if credentials.has_credential('FMP_API_KEY'):
    # Use market data capability
    pass
```

#### `get_all_credentials() -> Dict[str, str]`
Get all loaded credentials (MASKED for safety).

**Returns:**
- Dictionary of masked credentials

#### `get_raw(key_name: str) -> str`
Get raw credential value without warnings.

**Parameters:**
- `key_name`: Name of the credential

**Returns:**
- Raw credential value or empty string

### Helper Functions

#### `get_credential_manager(env_file: str = '.env', verbose: bool = False) -> CredentialManager`
Get singleton credential manager instance.

**Parameters:**
- `env_file`: Path to .env file (only used on first call)
- `verbose`: Whether to print validation warnings (only used on first call)

**Returns:**
- CredentialManager instance

## Security Best Practices

1. **Never commit .env file**: Always add `.env` to `.gitignore`
2. **Use environment variables in production**: More secure than files
3. **Rotate keys regularly**: Change API keys periodically
4. **Use masked values in logs**: Always use `mask_key()` for logging
5. **Check credentials at startup**: Use `validate_all()` to verify configuration

## Testing

Run the credential manager test suite:

```bash
python scripts/test_credentials.py
```

This will test:
- CredentialManager initialization
- Key masking functionality
- Credential validation
- Show which keys are configured

## Example Output

When initializing with `verbose=True`:

```
============================================================
DawsOS Credential Validation
============================================================

Required Credentials:
  ANTHROPIC_API_KEY         ✓ Available     sk-ant-12...xyz

Optional Credentials:
  FMP_API_KEY               ✓ Available     abcd1234...xyz
  FRED_API_KEY              ✓ Available     12345678...abc
  NEWSAPI_KEY               ✗ Missing
  ALPHA_VANTAGE_KEY         ✗ Missing
============================================================
```

## Integration with Existing Code

The credential manager is already integrated with:

1. **dawsos/core/llm_client.py**: Claude API authentication
2. **dawsos/capabilities/market_data.py**: FMP API authentication
3. **dawsos/capabilities/fred_data.py**: FRED API authentication
4. **dawsos/capabilities/news.py**: News API authentication

All these classes now use `get_credential_manager()` instead of `os.getenv()`.

## Troubleshooting

### "No .env file found"
- Create a `.env` file in the project root
- Or set environment variables instead

### "Missing required credential: ANTHROPIC_API_KEY"
- Set the ANTHROPIC_API_KEY in your `.env` file or environment
- This is required for DawsOS to function

### Credentials not loading
- Check `.env` file location (should be in project root)
- Verify `.env` file format (KEY=value, no spaces around =)
- Try setting environment variables directly
- Run test script: `python scripts/test_credentials.py`

## File Locations

- **Core Module**: `dawsos/core/credentials.py`
- **Test Script**: `scripts/test_credentials.py`
- **Example Config**: `.env.example`
- **Documentation**: `dawsos/core/README_CREDENTIALS.md`
